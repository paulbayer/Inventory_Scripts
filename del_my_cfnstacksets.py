#!/usr/local/bin/python3

import os, sys, pprint, argparse
import Inventory_Modules
import boto3
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-c","--creds",
	dest="plevel",
	metavar="Creds",
	default="1",
	help="Which credentials file to use for investigation.")
parser.add_argument(
	"-p","--profile",
	dest="pProfiles",
	nargs="*",
	metavar="profile to use",
	default="all",
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-f","--fragment",
	dest="pstackfrag",
	metavar="CloudFormation stack fragment",
	default="all",
	help="String fragment of the cloudformation stack or stackset(s) you want to check for.")
parser.add_argument(
	"-s","--status",
	dest="pstatus",
	metavar="CloudFormation status",
	default="active",
	help="String that determines whether we only see 'CREATE_COMPLETE' or 'DELETE_COMPLETE' too")
parser.add_argument(
	"-r","--region",
	nargs="*",
	dest="pregion",
	metavar="region name string",
	default="us-east-1",
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const",
	dest="loglevel",
	const=logging.DEBUG,
    default=logging.CRITICAL)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.INFO)
parser.add_argument(
    '+forreal','+for-real','-for-real','-forreal','--for-real','--forreal','--forrealsies',
    help="Do a Dry-run; don't delete anything",
    action="store_const",
	const=False,
	default=True,
	dest="DryRun")
args = parser.parse_args()

# If plevel
	# 1: credentials file only
	# 2: config file only
	# 3: credentials and config files
pProfiles=args.pProfiles
plevel=args.plevel
pRegionList=args.pregion
pstackfrag=args.pstackfrag
pstatus=args.pstatus
verbose=args.loglevel
pdryrun=args.DryRun
logging.basicConfig(level=args.loglevel)
# RegionList=[]

# if pRegionList

# SkipProfiles=["default"]
SkipProfiles=["default","Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

NumStacksFound = 0
NumRegions = 0
print()

# Find all stacksets in this account
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList=Inventory_Modules.get_profiles(pProfiles,plevel,SkipProfiles)# pprint.pprint(RegionList)
# sys.exit(1)
for pregion in RegionList:
	NumRegions += 1
	NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	fmt='%-20s | %-12s | %-10s | %-20s | %-25s | %-50s'
	print(fmt % ("Parent Profile","Acct Number","Region","Parent StackSet Name","Stack Status","Child Stack Name"))
	print(fmt %	("--------------","-----------","------","--------------------","----------------","----------------"))
	for profile in ProfileList: #Inventory_Modules.get_profiles(pProfiles,plevel,SkipProfiles):
		NumProfilesInvestigated += 1
		try:
			# cloudformation.list-stack-sets () gives you the stack-set-names and status of the stack-sets
			Stacksets=Inventory_Modules.find_stacksets(profile,pregion,pstackfrag,pstatus)
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure")

# Find which accounts the stacks belong to and in which regions
		StacksToDelete=[]
		a=0
		for Stackset in Stacksets:
			session_cfn=boto3.Session(profile_name=profile, region_name=pregion)
			stackset_info=session_cfn.client('cloudformation')
			stackset_associations=stackset_info.list_stack_instances(StackSetName=Stackset['StackSetName'])
			logging.info(Fore.RED+"Profile:",profile,"Stack:",Stackset['StackSetName'],"has",len(stackset_associations['Summaries']),"child stacks"+Fore.RESET)
			for operation in stackset_associations['Summaries']:
				# stacksetoperation=stackset_info.list_stack_set_operation_results(StackSetName=Stackset['StackSetName'],OperationId=operation['OperationId'])['Summaries']
				# # print("Profile:",profile,"Stack:",stack['StackSetName'],"has",len(stackset['Summaries']),"child stacks")
				# for y in range(len(stacksetoperation)):
					logging.debug(Fore.RED+"StackSet",Stackset['StackSetName'],"in the parent profile",profile,"is connected to the account",operation['Account'],"in the",operation['Region'], "Region"+Fore.RESET)
					# pprint.pprint(stacksetopertaion[y]['Account'])
					session_sts=boto3.Session(profile_name=profile)
					client_sts=session_sts.client('sts')
					RoleArn="arn:aws:iam::"+operation['Account']+":role/AWSCloudFormationStackSetExecutionRole"
					try:
						assumed_role=client_sts.assume_role(
							RoleArn=RoleArn,
							RoleSessionName="AssumeRoleSession1"
						)
					except ClientError as my_Error:
						if str(my_Error).find("AccessDenied") > 0:
							logging.info(profile+": Access Denied. Probably the role",RoleArn,"doesn't exist, or you aren't allowed to use it.")
						continue
					credentials=assumed_role['Credentials']
					cfn_client=boto3.client(
						'cloudformation',
						aws_access_key_id = credentials['AccessKeyId'],
						aws_secret_access_key = credentials['SecretAccessKey'],
						aws_session_token = credentials['SessionToken']
					)
					logging.info(Fore.BLUE+"Instead of deleting just yet - we'll list it first..."+Fore.RESET)
					response=cfn_client.list_stacks(StackStatusFilter=['CREATE_COMPLETE','UPDATE_ROLLBACK_COMPLETE'])['StackSummaries']
					for i in range(len(response)):
						if Stackset['StackSetName'] in response[i]['StackName']:
							ChildStackName=response[i]['StackName']
							StackStatus=response[i]['StackStatus']
							logging.info("ChildStackName:",ChildStackName)
					print(fmt % (profile, operation['Account'],operation['Region'], Stackset['StackSetName'],StackStatus,ChildStackName))
					# logging.info("Found:",response[i]['StackName'])
					StacksToDelete.append([profile,operation['Account'],operation['Region'],Stackset['StackSetName'],StackStatus,ChildStackName])
# cloudformation.list-stack-set-operations (stack-set-name) gives you the operation-id (possibly sorted by EndTimestamp)
# cloudformation.list-stack-set-operation-results (stack-set-name, operation-id) gives you the accounts and regions it's been installed into (Look for Status "SUCCEEDED")
# pprint.pprint(StacksToDelete)

# Go to all of those accounts and delete their stacks
for i in range(len(StacksToDelete)):
	# (0) Profile, (1) Account ID, (2) Region, (3) StackSet Name, (4) ChildStackStatus, (5) ChildStackName
	role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(StacksToDelete[i][1])
	# Assume an admin role in the Child Account
	account_credentials = client_sts.assume_role(RoleArn=role_arn, RoleSessionName="ALZAddIsengardUserScript")['Credentials']
	cfn_client=boto3.client('cloudformation',
		region_name=StacksToDelete[i][2],
		aws_access_key_id=account_credentials['AccessKeyId'],
		aws_secret_access_key=account_credentials['SecretAccessKey'],
		aws_session_token=account_credentials['SessionToken'])
	if not pdryrun:
		response=cfn_client.delete_stack(StackName=StacksToDelete[i][5])
	else:
		print("DryRun is enabled, so we didn't delete the stack %s in account %s in region %s using profile %s" % (StacksToDelete[i][5], StacksToDelete[i][1], StacksToDelete[i][2], StacksToDelete[i][0]))


sys.exit(9)


fmt='%-20s %-10s %-15s %-50s'
print(fmt % ("Profile","Region","Stack Status","Stack Name"))
print(fmt % ("-------","------","------------","----------"))
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList=Inventory_Modules.get_profiles(pProfiles,plevel,SkipProfiles)# pprint.pprint(RegionList)
# sys.exit(1)
for pregion in RegionList:
	NumRegions += 1
	NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for profile in ProfileList: #Inventory_Modules.get_profiles(pProfiles,plevel,SkipProfiles):
		NumProfilesInvestigated += 1
		try:
			Stacks=Inventory_Modules.find_stacks(profile,pregion,pstackfrag,pstatus)
			# StackSets=Inventory_Modules.find_stacksets(profile,pregion,pstackfrag)
			# pprint.pprint(Stacks)
			StackNum=len(Stacks)
			logging.info("Profile: %s | Region: %s | Found %s Stacks", profile, pregion, StackNum )
			print(Fore.RED+"Profile: ",profile,"Region: ",pregion,"Found",StackNum,"Stacks"+Fore.RESET)
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure")
		if len(Stacks) > 0:
			for y in range(len(Stacks)):
				StackName=Stacks[y]['StackName']
				StackStatus=Stacks[y]['StackStatus']
		# 		IsDefault=Stacks['StackSummaries'][y]['IsDefault']
		# 		CIDR=Stacks['Stacks'][y]['CidrBlock']
		# 		if 'Tags' in Stacks['StackSummaries'][y]:
		# 			for z in range(len(Stacks['StackSummaries'][y]['Tags'])):
		# 				if Stacks['StackSummaries'][y]['Tags'][z]['Key']=="Name":
		# 					VpcName=Stacks['StackSummaries'][y]['Tags'][z]['Value']
		# 		else:
		# 			VpcName="No name defined"
				print(fmt % (profile,pregion,StackStatus,StackName))
				NumStacksFound += 1
print(ERASE_LINE)
print(Fore.RED+"Found",NumStacksFound,"Stacks across",NumProfilesInvestigated,"profiles across",NumRegions,"regions"+Fore.RESET)
print()
