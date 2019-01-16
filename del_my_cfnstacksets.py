#!/usr/local/bin/python3

'''
TODO:
	- Enable this script to accept a Session Token to allow for Federated users via Isengard
	- Pythonize the whole thing
	- Write a requirements file to desribe the requirements (like colorama, pprint, argparse, etc.)
	- More Commenting throughout script
'''

import os, sys, pprint, argparse, logging
# from sty import
import Inventory_Modules
import boto3
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfiles",
	nargs="*",
	metavar="profile to use",
	default="all",
	help="To specify a specific profile or profiles, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-f","--fragment",
	dest="pstackfrag",
	nargs="*",
	metavar="CloudFormation stack fragment",
	default=["all"],
	help="List containing fragment(s) of the cloudformation stack or stackset(s) you want to check for.")
parser.add_argument(
	"-r","--region",
	nargs="*",
	dest="pregion",
	metavar="region name string",
	default=["us-east-1"],
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

pProfiles=args.pProfiles
pRegionList=args.pregion
pstackfrag=args.pstackfrag
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
NumStackSetsFound=0
NumMasterRegions = 0
StacksToDelete=[]
StackInstancesToDelete=[]
print()

# Find all stacksets in this account
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList=Inventory_Modules.get_profiles(pProfiles,SkipProfiles)
logging.info("There are %s profiles in your list" % (len(ProfileList)))

if pdryrun:
	print("You asked me to find (but not delete) stacksets that match the following:")
else:
	print("You asked me to find (and delete) stacksets that match the following:")
print("		In profiles that contain these string fragments: {}".format(pProfiles))
print("		In these regions: {}".format(pRegionList))
print("		For stacksets that contain these fragments: {}".format(pstackfrag))
print()
fmt='%-20s | %-12s | %-10s | %-50s | %-25s | %-50s'
print(fmt % ("Parent Profile","Acct Number","Region","Parent StackSet Name","Stack Status","Child Stack Name"))
print(fmt %	("--------------","-----------","------","--------------------","----------------","----------------"))
for pregion in RegionList:
	NumMasterRegions += 1
	# This section gets the listing of Stacksets for the profile(s) that were supplied at the command line.
	for profile in ProfileList:
		try:
			print(ERASE_LINE,Fore.BLUE,"	Looking in profile {profile_name} in region {region_name}".format(profile_name=profile,region_name=pregion),Fore.RESET,end='\r')
			Stacksets=Inventory_Modules.find_stacksets(profile,pregion,pstackfrag)
			NumStackSetsFound = NumStackSetsFound + len(Stacksets)
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure")

		# Delve into the stack associations for each StackSet, and find which accounts and regions have the child stacks
		for Stackset in Stacksets:
			session_cfn=boto3.Session(profile_name=profile, region_name=pregion)
			stackset_info=session_cfn.client('cloudformation')
			stackset_associations=stackset_info.list_stack_instances(StackSetName=Stackset['StackSetName'])
			logging.info("Profile: %s Stack: %s has %s child stacks" % (profile,Stackset['StackSetName'],len(stackset_associations['Summaries'])))
			for operation in stackset_associations['Summaries']:
				# This is where we begin going into each child account and finding the names of the stacks that belong to the parent stackset
				logging.info("StackSet %s in the parent profile %s is connected to the account %s in the %s Region" % (Stackset['StackSetName'],profile,operation['Account'],operation['Region']))
				StackInstancesToDelete.append(operation)
				session_sts=boto3.Session(profile_name=profile)
				client_sts=session_sts.client('sts')
				RoleArn="arn:aws:iam::"+operation['Account']+":role/AWSCloudFormationStackSetExecutionRole"
				response=[]
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
				for stackfrag in pstackfrag:
					initial_response=Inventory_Modules.find_stacks_in_acct(credentials,operation['Region'],stackfrag)
					# print()
					# print("This many stacks: {}".format(len(initial_response)))
					# pprint.pprint(initial_response)
					for j in range(len(initial_response)):
						# pprint.pprint(initial_response[j])
						response.append(initial_response[j])
						# pprint.pprint(response)
						# print("******")
				# pprint.pprint(response)
				# response=cfn_client.list_stacks(StackStatusFilter=['CREATE_COMPLETE','UPDATE_ROLLBACK_COMPLETE','UPDATE_COMPLETE','CREATE_FAILED'])['StackSummaries']
				logging.info(Fore.BLUE+"Instead of deleting the relevant child stack just yet - we'll list it first..."+Fore.RESET)
				if len(response)==0:
					# This is needed because the StackSet could list an account / region which doesn't actually have any stacks in the child account.
					continue
				else:
					# This case is where the response includes stacks (and those stacks will contain more than just the stacks that are connected to the original stackset name)
					for i in range(len(response)):
						# logging.info("StackSetName"+Stackset['StackSetName']+" | response StackName: "+response[i]['StackName'])
						# This if statement below is to determine if the child stack is associated with the parent stackset.
						if Stackset['StackSetName'] in response[i]['StackName']:
							ChildStackName=response[i]['StackName']
							StackStatus=response[i]['StackStatus']
							logging.info("ChildStackName: "+ChildStackName)
							print(fmt % (profile, operation['Account'],operation['Region'], Stackset['StackSetName'],StackStatus,ChildStackName))
							# logging.info("Found:",response[i]['StackName'])
							StacksToDelete.append([profile,operation['Account'],operation['Region'],Stackset['StackSetName'],StackStatus,ChildStackName])

# pprint.pprint(StacksToDelete)
# print("There were {} instances in this StacksToDelete dictionary".format(len(StacksToDelete)))
# sys.exit(9)

# Go to all of those accounts and delete their stacks
print(ERASE_LINE,"There are {} stacks to delete".format(len(StacksToDelete)))
StackRegionSet=set()
AccountSet=set()
print("There are {} instances to delete".format(len(StackInstancesToDelete)))
pprint.pprint(StackInstancesToDelete)
for i in range(len(StackInstancesToDelete)):
	if not pdryrun:
		FindComma=str(StackInstancesToDelete[i]['StackSetId']).find(":")
		StackSetName=str(StackInstancesToDelete[i]['StackSetId'])[0:FindComma]
		## To Do:
		# StackSetName=get_stack_name_from_stack_set_id(StackInstancesToDelete[i]['StackSetId'])
		print("This is the stack name: {}".format(StackSetName))
		StackInstance_response=stackset_info.delete_stack_instance(
		    			StackSetName=StackSetName,
						StackInstanceAccount=StackInstancesToDelete[i]['Account'],
						StackInstanceRegion=StackInstancesToDelete[i]['Region']
						)

for i in range(len(StacksToDelete)):
	logging.info("Beginning to delete stackname %s - %s of %s now." % (StacksToDelete[i][5], i+1,len(StacksToDelete)))
	StackRegionSet.add(StacksToDelete[i][2])
	AccountSet.add(StacksToDelete[i][1])
	if not pdryrun:
		role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(StacksToDelete[i][1])
		# Assume an admin role in the Child Account
		account_credentials = client_sts.assume_role(RoleArn=role_arn, RoleSessionName="StackSetDeleter")['Credentials']
		cfn_client=boto3.client('cloudformation',
			region_name=StacksToDelete[i][2],
			aws_access_key_id=account_credentials['AccessKeyId'],
			aws_secret_access_key=account_credentials['SecretAccessKey'],
			aws_session_token=account_credentials['SessionToken'])
		response=cfn_client.delete_stack(StackName=StacksToDelete[i][5])
		print("Deleted stack {} in account {} in region {}".format(StacksToDelete[i][5],StacksToDelete[i][1],StacksToDelete[i][2]))
	else:
		# print("DryRun is enabled, so we didn't delete the stack we found in account %s in region %s" % (StacksToDelete[i][1], StacksToDelete[i][2]))
		print("DryRun is enabled, so we didn't delete the stack we found in account {} in region {} called {}".format (StacksToDelete[i][1],StacksToDelete[i][2],StacksToDelete[i][5]))

# Now to delete the original stackset itself
if not pdryrun:
	for Stackset in Stacksets:
		logging.info("Deleting StackSet %s in Account %s" % (Stackset['StackSetName'],"Account ID here"))
		stacksets_to_delete=stackset_info.delete_stack_set(StackSetName=Stackset['StackSetName'])


print()
print(Fore.RED+"Initially found {} StackSets across {} regions within the Master profile".format(NumStackSetsFound,NumMasterRegions)+Fore.RESET)
print(Fore.RED+"Then we found {} child stacks across {} regions across {} accounts".format(len(StacksToDelete),len(StackRegionSet),len(AccountSet))+Fore.RESET)
print()
