#!/usr/local/bin/python3

import os, sys, pprint, boto3
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="To specify a specific profile, use this parameter. Default will be your default profile.")
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
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
	"+delete","+forreal",
	dest="DeletionRun",
	const=True,
	default=False,
	action="store_const",
	help="This will delete the stacks found - without any opportunity to confirm. Be careful!!")
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const",
	dest="loglevel",
	const=logging.INFO,
    default=logging.CRITICAL)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.WARNING)
args = parser.parse_args()

pProfile=args.pProfile
pRegionList=args.pregion
pstackfrag=args.pstackfrag
pstatus=args.pstatus
verbose=args.loglevel
DeletionRun=args.DeletionRun
logging.basicConfig(level=args.loglevel)

##########################
ERASE_LINE = '\x1b[2K'

NumStacksFound = 0
print()
fmt='%-20s %-15s %-15s %-50s'
print(fmt % ("Account","Region","Stack Status","Stack Name"))
print(fmt % ("-------","------","------------","----------"))
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
# pprint.pprint(RegionList)
# sys.exit(1)
StacksFound=[]
sts_session = boto3.Session(profile_name=pProfile)
sts_client = sts_session.client('sts')
for account in ChildAccounts:
	role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(account['AccountId'])
	logging.info("Role ARN: %s" % role_arn)
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-Stacks")['Credentials']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(profile+": Authorization Failure for account {}".format(account['AccountId']))
	for region in RegionList:
		try:
			StackNum=0
			Stacks=Inventory_Modules.find_stacks_in_acct(account_credentials,region,pstackfrag)
			# pprint.pprint(Stacks)
			StackNum=len(Stacks)
			logging.warning("Account: %s | Region: %s | Found %s Stacks", account['AccountId'], region, StackNum )
			print(ERASE_LINE,Fore.RED+"Account: {} Region: {} Found {} Stacks".format(account['AccountId'],region,StackNum)+Fore.RESET,end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(account['AccountId']+": Authorization Failure")
		if StackNum > 0:
			for y in range(len(Stacks)):
				StackName=Stacks[y]['StackName']
				StackStatus=Stacks[y]['StackStatus']
				print(fmt % (account['AccountId'],region,StackStatus,StackName))
				NumStacksFound += 1
				StacksFound.append({
					'Account':account['AccountId'],
					'Region':region,
					'StackName':StackName,
					'StackStatus':Stacks[y]['StackStatus']})
print(ERASE_LINE)
print(Fore.RED+"Found",NumStacksFound,"Stacks across",len(ChildAccounts),"accounts across",len(RegionList),"regions"+Fore.RESET)
print()
# pprint.pprint(StacksFound)

if DeletionRun and ('GuardDuty' in pstackfrag):
	logging.warning("Deleting %s stacks",len(StacksFound))
	for y in range(len(StacksFound)):
		print("Deleting stack {} from profile {} in region {} with status: {}".format(StacksFound[y]['StackName'],StacksFound[y]['Profile'],StacksFound[y]['Region'],StacksFound[y]['StackStatus']))
		""" This next line is BAD because it's hard-coded for GuardDuty, but we'll fix that eventually """
		if StacksFound[y]['StackStatus'] == 'DELETE_FAILED':
			# This deletion generally fails because the Master Detector doesn't properly delete (and it's usually already deleted due to some other script) - so we just need to delete the stack anyway - and ignore the actual resource.
			response=Inventory_Modules.delete_stack(StacksFound[y]['Profile'],StacksFound[y]['Region'],StacksFound[y]['StackName'],RetainResources=True,ResourcesToRetain=["MasterDetector"])
		else:
			response=Inventory_Modules.delete_stack(StacksFound[y]['Profile'],StacksFound[y]['Region'],StacksFound[y]['StackName'])
elif DeletionRun:
	logging.warning("Deleting %s stacks",len(StacksFound))
	for y in range(len(StacksFound)):
		print("Deleting stack {} from profile {} in region {} with status: {}".format(StacksFound[y]['StackName'],StacksFound[y]['Profile'],StacksFound[y]['Region'],StacksFound[y]['StackStatus']))
		response=Inventory_Modules.delete_stack(StacksFound[y]['Profile'],StacksFound[y]['Region'],StacksFound[y]['StackName'])


print("Thanks for using this script...")
