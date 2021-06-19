#!/usr/bin/env python3

import logging
import Inventory_Modules
import argparse
import boto3
from colorama import init, Fore
from botocore.exceptions import ClientError

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	help="To specify a specific profile, use this parameter.")
parser.add_argument(
	"-f", "--fragment",
	dest="pstackfrag",
	metavar="CloudFormation stack fragment",
	default=["all"],
	help="String fragment of the cloudformation stack or stackset(s) you want to check for.")
parser.add_argument(
	"-s", "--status",
	dest="pstatus",
	metavar="CloudFormation status",
	default="active",
	help="String that determines whether we only see 'CREATE_COMPLETE' or 'DELETE_COMPLETE' too. Valid values are 'ACTIVE' or 'DELETED'")
parser.add_argument(
	"-r", "--region",
	nargs="*",
	dest="pregion",
	metavar="region name string",
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,        # args.loglevel = 40
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,      # args.loglevel = 30
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,         # args.loglevel = 20
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,        # args.loglevel = 10
	default=logging.CRITICAL)   # args.loglevel = 50
args = parser.parse_args()

pProfile = args.pProfile
pRegionList = args.pregion
pstackfrag = args.pstackfrag
pstatus = args.pstatus
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")

SkipProfiles = ["default"]
ChildAccounts = Inventory_Modules.find_child_accounts2(pProfile)

NumStacksFound = 0
##########################
ERASE_LINE = '\x1b[2K'

print()
fmt = '%-20s %-15s %-15s %-50s'
print(fmt % ("Account", "Region", "Status", "StackSet Name"))
print(fmt % ("-------", "------", "------", "-------------"))
RegionList = Inventory_Modules.get_ec2_regions(pRegionList)

sts_session = boto3.Session(profile_name=pProfile)
sts_client = sts_session.client('sts')
account_credentials = None      # This shouldn't matter, but makes the IDE checker happy.
for account in ChildAccounts:
	role_arn = f"arn:aws:iam::{account['AccountId']}:role/AWSCloudFormationStackSetExecutionRole"
	logging.info(f"Role ARN: {role_arn}")
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-StackSets")['Credentials']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0 or str(my_Error).find("AccessDenied") > 0:
			logging.error("%s: Authorization Failure for account %s", pProfile, account['AccountId'])
			continue
	for region in RegionList:
		try:
			print(ERASE_LINE, f"{Fore.RED}Checking Account: ", account['AccountId'], "Region: ", region+Fore.RESET, end="\r")
			StackSets = Inventory_Modules.find_stacksets2(account_credentials, region, account['AccountId'], pstackfrag)
			logging.warning("Account: %s | Region: %s | Found %s Stacksets", account['AccountId'], region, len(StackSets))
			if not StackSets == []:
				print(ERASE_LINE, f"{Fore.RED}Account: ", account['AccountId'], "Region: ", region, "Found", len(StackSets), f"Stacksets{Fore.RESET}", end="\r")
			for y in range(len(StackSets)):
				StackName = StackSets[y]['StackSetName']
				StackStatus = StackSets[y]['Status']
				print(fmt % (account['AccountId'], region, StackStatus, StackName))
				NumStacksFound += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{account['AccountId']}: Authorization Failure")
print(ERASE_LINE)
print(f"{Fore.RED}Found", NumStacksFound, "Stacksets across", len(ChildAccounts), "accounts across", len(RegionList), f"regions{Fore.RESET}")
print()
print("Thanks for using this script...")
