#!/usr/local/bin/python3

import os, sys, pprint, argparse
# from sty import
import Inventory_Modules
import boto3
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

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
	help="String fragment of the cloudformation stack or stackset(s) you want to check for.")
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
NumRegions = 0
StacksToDelete=[]
print()

# Find all stacksets in this account
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList=Inventory_Modules.get_profiles(pProfiles,SkipProfiles)
logging.info("There are %s profiles in your list" % (len(ProfileList)))

fmt='%-20s | %-12s | %-10s | %-50s | %-25s | %-50s'
print(fmt % ("Parent Profile","Acct Number","Region","Parent StackSet Name","Stack Status","Child Stack Name"))
print(fmt %	("--------------","-----------","------","--------------------","----------------","----------------"))
for pregion in RegionList:
	NumRegions += 1
	for profile in ProfileList: #Inventory_Modules.get_profiles(pProfiles,plevel,SkipProfiles):
		try:
			# cloudformation.list-stack-sets () gives you the stack-set-names and status of the stack-sets
			print(ERASE_LINE,Fore.BLUE,"	Looking in profile {profile_name} in region {region_name}".format(profile_name=profile,region_name=pregion),Fore.RESET,end='\r')
			Stacksets=Inventory_Modules.find_stacksets(profile,pregion,pstackfrag)
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure")

		# Find which accounts the stacks belong to and in which regions
		for Stackset in Stacksets:
			session_cfn=boto3.Session(profile_name=profile, region_name=pregion)
			stackset_info=session_cfn.client('cloudformation')
			stackset_associations=stackset_info.list_stack_instances(StackSetName=Stackset['StackSetName'])
			logging.info("Profile: %s Stack: %s has %s child stacks" % (profile,Stackset['StackSetName'],len(stackset_associations['Summaries'])))
			for operation in stackset_associations['Summaries']:
				logging.debug("StackSet %s in the parent profile %s is connected to the account %s in the %s Region" % (Stackset['StackSetName'],profile,operation['Account'],operation['Region']))
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
				response=cfn_client.list_stacks(StackStatusFilter=['CREATE_COMPLETE','UPDATE_ROLLBACK_COMPLETE','UPDATE_COMPLETE','CREATE_FAILED'])['StackSummaries']
				for i in range(len(response)):
					if Stackset['StackSetName'] in response[i]['StackName']:
						ChildStackName=response[i]['StackName']
						StackStatus=response[i]['StackStatus']
						logging.info("ChildStackName: "+ChildStackName)
				print(fmt % (profile, operation['Account'],operation['Region'], Stackset['StackSetName'],StackStatus,ChildStackName))
				# logging.info("Found:",response[i]['StackName'])
				StacksToDelete.append([profile,operation['Account'],operation['Region'],Stackset['StackSetName'],StackStatus,ChildStackName])
				NumStacksFound+=1

# Go to all of those accounts and delete their stacks
print(ERASE_LINE,"There are {} stacks to delete".format(len(StacksToDelete)))
for i in range(len(StacksToDelete)):
	logging.info("Beginning to delete stack %s of %s now." % (i+1,len(StacksToDelete)))
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
	else:
		print("DryRun is enabled, so we didn't delete the stack we found in account %s in region %s" % (StacksToDelete[i][1], StacksToDelete[i][2]))

print()
print(Fore.RED+"Found {} Stacks across {} regions across {} profiles".format(NumStacksFound,NumRegions,len(ProfileList))+Fore.RESET)
print()
