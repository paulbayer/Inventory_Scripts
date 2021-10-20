#!/usr/bin/env python3

import os
import sys
import pprint
import boto3
import Inventory_Modules
import pprint
import argparse
from colorama import init, Fore, Back, Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.my_parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="To specify a specific profile, use this parameter. Default will be your default profile.")
parser.my_parser.add_argument(
	"-f", "--fragment",
	dest="pstackfrag",
	metavar="CloudFormation stack fragment",
	default="all",
	help="String fragment of the cloudformation stack or stackset(s) you want to check for.")
parser.my_parser.add_argument(
	"-s", "--status",
	dest="pstatus",
	metavar="CloudFormation status",
	default="active",
	help="String that determines whether we only see 'CREATE_COMPLETE' or 'DELETE_COMPLETE' too")
parser.my_parser.add_argument(
	"-k", "--skip",
	dest="pSkipAccounts",
	nargs="*",
	metavar="Accounts to leave alone",
	default=[],
	help="These are the account numbers you don't want to screw with. Likely the core accounts.")
parser.my_parser.add_argument(
	"-r", "--region",
	nargs="*",
	dest="pregion",
	metavar="region name string",
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
parser.my_parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,  # args.loglevel = 10
	default=logging.CRITICAL)  # args.loglevel = 50
parser.my_parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,  # args.loglevel = 20
	default=logging.CRITICAL)  # args.loglevel = 50
parser.my_parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,  # args.loglevel = 30
	default=logging.CRITICAL)  # args.loglevel = 50
parser.my_parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,  # args.loglevel = 40
	default=logging.CRITICAL)  # args.loglevel = 50
args = parser.my_parser.parse_args()

pProfile = args.pProfiles
pRegionList = args.pregion
pstackfrag = args.pstackfrag
pstatus = args.pstatus
AccountsToSkip = args.pSkipAccounts
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'

print(args.loglevel)

NumStacksFound = 0
print()
fmt = '%-20s %-15s %-15s %-50s'
print(fmt % ("Account", "Region", "Stack Status", "Stack Name"))
print(fmt % ("-------", "------", "------------", "----------"))
# RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
RegionList = Inventory_Modules.get_service_regions('cloudformation', pRegionList)
ChildAccounts = Inventory_Modules.find_child_accounts2(pProfile)
ChildAccounts = Inventory_Modules.RemoveCoreAccounts(ChildAccounts, AccountsToSkip)
# pprint.pprint(AccountsToSkip)
# pprint.pprint(ChildAccounts)
# sys.exit(1)
StacksFound = []
aws_session = boto3.Session(profile_name=pProfile)
sts_client = aws_session.client('sts')
for account in ChildAccounts:
	role_arn = f"arn:aws:iam::{account['AccountId']}:role/AWSCloudFormationStackSetExecutionRole"
	logging.info(f"Role ARN: {role_arn}")
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-Stacks")['Credentials']
		account_credentials['AccountNumber'] = account['AccountId']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{pProfile}: Authorization Failure for account {account['AccountId']}")
		elif str(my_Error).find("AccessDenied") > 0:
			print(f"{pProfile}: Access Denied Failure for account {account['AccountId']}")
		else:
			print(f"{pProfile}: Other kind of failure for account {account['AccountId']}")
			print(my_Error)
		break
	for region in RegionList:
		try:
			StackNum = 0
			Stacks = Inventory_Modules.find_stacks_in_acct(account_credentials, region, pstackfrag, pstatus)
			# pprint.pprint(Stacks)
			# StackNum=len(Stacks)
			logging.warning("Account: %s | Region: %s | Found %s Stacks", account['AccountId'], region, StackNum)
			logging.info(ERASE_LINE, f"{Fore.RED}Account: {account['AccountId']} Region: {region} Found {StackNum} Stacks{Fore.RESET}", end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{account['AccountId']}: Authorization Failure")
		if len(Stacks) > 0:
			for y in range(len(Stacks)):
				StackName = Stacks[y]['StackName']
				StackStatus = Stacks[y]['StackStatus']
				StackID = Stacks[y]['StackId']
				DriftStatus = Inventory_Modules.enable_drift_on_stacks(account_credentials, region, StackName)
				logging.error("Enabled drift detection on %s in account %s in region %s", StackName, account_credentials['AccountNumber'], region)
				NumStacksFound += 1

print()
print(f"{Fore.RED}Looked through", NumStacksFound, "Stacks across", len(ChildAccounts), "accounts across", len(RegionList), f"regions{Fore.RESET}")
print()
# pprint.pprint(StacksFound)

print("Thanks for using this script...")
