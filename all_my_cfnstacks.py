#!/usr/bin/env python3

# import boto3
import Inventory_Modules
from pprint import pprint
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()

parser = CommonArguments()
parser.extendedargs()   # This adds additional *optional* arguments to the listing
parser.my_parser.add_argument(
	"-f", "--fragment",
	dest="stackfrag",
	metavar="CloudFormation stack fragment",
	default="all",
	help="String fragment of the cloudformation stack or stackset(s) you want to check for.")
parser.my_parser.add_argument(
	"-s", "--status",
	dest="status",
	metavar="CloudFormation status",
	default="active",
	help="String that determines whether we only see 'CREATE_COMPLETE' or 'DELETE_COMPLETE' too")
parser.my_parser.add_argument(
	"+delete", "+forreal",
	dest="DeletionRun",
	action="store_true",
	help="This will delete the stacks found - without any opportunity to confirm. Be careful!!")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegionList = args.Region
AccountsToSkip = args.SkipAccounts
verbose = args.loglevel
pstackfrag = args.stackfrag
pstatus = args.status
DeletionRun = args.DeletionRun
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'

print(args.loglevel)

print()
if args.loglevel < 21:  # INFO level
	fmt = '%-20s %-15s %-15s %-50s %-50s'
	print(fmt % ("Account", "Region", "Stack Status", "Stack Name", "Stack ID"))
	print(fmt % ("-------", "------", "------------", "----------", "--------"))
else:
	fmt = '%-20s %-15s %-15s %-50s'
	print(fmt % ("Account", "Region", "Stack Status", "Stack Name"))
	print(fmt % ("-------", "------", "------------", "----------"))

aws_acct = aws_acct_access(pProfile)
ChildAccounts = aws_acct.ChildAccounts

RegionList = Inventory_Modules.get_service_regions('cloudformation', pRegionList)
ChildAccounts = Inventory_Modules.RemoveCoreAccounts(ChildAccounts, AccountsToSkip)

StacksFound = []
aws_session = aws_acct.session
sts_client = aws_session.client('sts')
for account in ChildAccounts:
	role_arn = f"arn:aws:iam::{account['AccountId']}:role/AWSCloudFormationStackSetExecutionRole"
	logging.info(f"Role ARN: {role_arn}")
	try:
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, account['AccountId'])
		# account_credentials = sts_client.assume_role(
		# 	RoleArn=role_arn,
		# 	RoleSessionName="Find-Stacks")['Credentials']
		account_credentials['AccountNumber'] = account['AccountId']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{pProfile}: Authorization Failure for account {account['AccountId']}")
		elif str(my_Error).find("AccessDenied") > 0:
			print(f"{pProfile}: Access Denied Failure for account {account['AccountId']}")
		else:
			print(f"{pProfile}: Other kind of failure for account {account['AccountId']}")
			print(my_Error)
		continue
	for region in RegionList:
		Stacks = False
		try:
			Stacks = Inventory_Modules.find_stacks_in_acct(account_credentials, region, pstackfrag, pstatus)
			# pprint.pprint(Stacks)
			logging.warning("Account: %s | Region: %s | Found %s Stacks", account['AccountId'], region, len(Stacks))
			print(ERASE_LINE, Fore.RED+"Account: {} Region: {} Found {} Stacks".format(account['AccountId'], region, len(Stacks))+Fore.RESET, end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{account['AccountId']}: Authorization Failure")
		if Stacks and len(Stacks) > 0:
			for y in range(len(Stacks)):
				StackName = Stacks[y]['StackName']
				StackStatus = Stacks[y]['StackStatus']
				StackID = Stacks[y]['StackId']
				if args.loglevel < 21:  # INFO level
					print(fmt % (account['AccountId'], region, StackStatus, StackName, StackID))
				else:
					print(fmt % (account['AccountId'], region, StackStatus, StackName))
				StacksFound.append({
					'Account': account['AccountId'],
					'Region': region,
					'StackName': StackName,
					'StackStatus': StackStatus,
					'StackArn': StackID})
lAccounts = []
lRegions = []
lAccountsAndRegions = []
for i in range(len(StacksFound)):
	lAccounts.append(StacksFound[i]['Account'])
	lRegions.append(StacksFound[i]['Region'])
	lAccountsAndRegions.append((StacksFound[i]['Account'], StacksFound[i]['Region']))
print(ERASE_LINE)
print(f"{Fore.RED}Looked through", len(StacksFound), "Stacks across", len(ChildAccounts), "accounts across", len(RegionList), f"regions{Fore.RESET}")
print()
if args.loglevel < 21:  # INFO level
	print("The list of accounts and regions:")
	pprint(list(sorted(set(lAccountsAndRegions))))

if DeletionRun and ('GuardDuty' in pstackfrag):
	logging.warning("Deleting %s stacks", len(StacksFound))
	for y in range(len(StacksFound)):
		role_arn = f"arn:aws:iam::{StacksFound[y]['Account']}:role/AWSCloudFormationStackSetExecutionRole"
		cfn_client = aws_session.client('cloudformation')
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Delete-Stacks")['Credentials']
		account_credentials['AccountNumber'] = StacksFound[y]['Account']
		print(f"Deleting stack {StacksFound[y]['StackName']} from Account {StacksFound[y]['Account']} in region {StacksFound[y]['Region']} with status: {StacksFound[y]['StackStatus']}")
		""" This next line is BAD because it's hard-coded for GuardDuty, but we'll fix that eventually """
		if StacksFound[y]['StackStatus'] == 'DELETE_FAILED':
			# This deletion generally fails because the Master Detector doesn't properly delete (and it's usually already deleted due to some other script) - so we just need to delete the stack anyway - and ignore the actual resource.
			response = Inventory_Modules.delete_stack2(account_credentials, StacksFound[y]['Region'], StacksFound[y]['StackName'], RetainResources=True, ResourcesToRetain=["MasterDetector"])
		else:
			response = Inventory_Modules.delete_stack2(account_credentials, StacksFound[y]['Region'], StacksFound[y]['StackName'])
elif DeletionRun:
	logging.warning("Deleting %s stacks", len(StacksFound))
	for y in range(len(StacksFound)):
		role_arn = f"arn:aws:iam::{StacksFound[y]['Account']}:role/AWSCloudFormationStackSetExecutionRole"
		cfn_client = aws_session.client('cloudformation')
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Delete-Stacks")['Credentials']
		account_credentials['AccountNumber'] = StacksFound[y]['Account']
		print(f"Deleting stack {StacksFound[y]['StackName']} from account {StacksFound[y]['Account']} in region {StacksFound[y]['Region']} with status: {StacksFound[y]['StackStatus']}")
		response = Inventory_Modules.delete_stack2(account_credentials, StacksFound[y]['Region'], StacksFound[y]['StackName'])
		pprint(response)

print()
print("Thanks for using this script...")
