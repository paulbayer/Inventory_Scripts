#!/usr/bin/env python3

import logging
from pprint import pprint
from queue import Queue
from threading import Thread
from time import sleep, time


import simplejson as json
from botocore.exceptions import ClientError
from colorama import Fore, init

import Inventory_Modules
from Inventory_Modules import get_credentials_for_accounts_in_org
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access

"""
This script was created to help solve a testing problem for the "move_stack_instances.py" script.e
Originally, that script didn't have built-in recovery, so we needed this script to "recover" those stack-instance ids that might have been lost during the move_stack_instances.py run. However, that script now has built-in recovery, so this script isn't really needed. However, it can still be used to find any stack-instances that have been orphaned from their original stack-set, if that happens. 
"""

init()
__version__ = "2023.05.04"

parser = CommonArguments()
parser.singleprofile()  # Allows for a single profile to be specified
parser.multiregion()  # Allows for multiple regions to be specified at the command line
parser.extendedargs()  # Allows for extended arguments like which accounts to skip, and whether Force is enabled.
parser.timing()
parser.rolestouse()
parser.verbosity()  # Allows for the verbosity to be handled.
parser.version(__version__)
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
	"--home",
	dest="homeRegion",
	metavar="Single Region name",
	help="Region where the StackSets are homed")
parser.my_parser.add_argument(
	"--new",
	dest="newStackSetName",
	metavar="New Stackset name",
	help="The NEW Stack Set name")
parser.my_parser.add_argument(
	"--old",
	dest="oldStackSetName",
	metavar="Old Stackset name",
	help="The OLD Stack Set name")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegionList = args.Regions
pRegion = args.homeRegion
pAccounts = args.Accounts
pSkipAccounts = args.SkipAccounts
pRoles = args.AccessRoles
verbose = args.loglevel
pTiming = args.Time
pOldStackSetName = args.oldStackSetName
pNewStackSetName = args.newStackSetName
pstackfrag = args.stackfrag
pstatus = args.status
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")

##########################
def find_orphaned_stacks_within_child_accounts(faccounts:list=None):
	item_counter = 0
	# AccountCredentials =
	for region in RegionLiwwwst:
		item_counter += 1
		Stacks = []
		try:
			Stacks = Inventory_Modules.find_stacks2(account_credentials, region, pstackfrag, pstatus)
			logging.warning(f"Account: {account_number} | Region: {region} | Found {len(Stacks)} Stacks")
			print(f"{ERASE_LINE}{Fore.RED}Account: {account_number} Region: {region} Found {len(Stacks)} Stacks{Fore.RESET} ({item_counter} of {len(AccountList) * len(RegionList)})", end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{account_number}: Authorization Failure")
		# TODO: Currently we're using this "Stacks" list as a boolean if it's populated. We should change this.
		if Stacks and len(Stacks) > 0:
			for y in range(len(Stacks)):
				StackName = Stacks[y]['StackName']
				StackStatus = Stacks[y]['StackStatus']
				StackID = Stacks[y]['StackId']
				if pStackIdFlag:
					print(fmt % (account_number, region, StackStatus, StackName, StackID))
				else:
					print(fmt % (account_number, region, StackStatus, StackName))
				StacksFound.append({
					'Account'    : account_number,
					'Region'     : region,
					'StackName'  : StackName,
					'StackStatus': StackStatus,
					'StackArn'   : StackID})
	return(StacksFound)



ERASE_LINE = '\x1b[2K'
aws_acct = aws_acct_access(pProfile)
begin_time = time()
ChildAccounts = []
if pAccounts is None:
	ChildAccounts = aws_acct.ChildAccounts
else:
	for account in aws_acct.ChildAccounts:
		if account['AccountId'] in pAccounts:
			ChildAccounts.append({'AccountId'    : account['AccountId'],
			                      'AccountEmail' : account['AccountEmail'],
			                      'AccountStatus': account['AccountStatus'],
			                      'MgmtAccount'  : account['MgmtAccount']})
RegionList = Inventory_Modules.get_service_regions('cloudformation', pRegionList)
# ChildAccounts = Inventory_Modules.RemoveCoreAccounts(ChildAccounts, AccountsToSkip)
AccountList = [account['AccountId'] for account in ChildAccounts]
pStackIdFlag = True
precoveryFlag = True

print(f"You asked to find stacks with this fragment {Fore.RED}'{pstackfrag}'{Fore.RESET}")
print(f"in these accounts:\n{Fore.RED}{AccountList}{Fore.RESET}")
print(f"in these regions:\n{Fore.RED}{RegionList}{Fore.RESET}")
print(f"While skipping these accounts:\n{Fore.RED}{pSkipAccounts}{Fore.RESET}") if pSkipAccounts is not None else ''

print()
fmt = '%-20s %-15s %-15s %-50s %-50s'
print(fmt % ("Account", "Region", "Stack Status", "Stack Name", "Stack ID"))
print(fmt % ("-------", "------", "------------", "----------", "--------"))

StacksFound = []
sts_client = aws_acct.session.client('sts')
item_counter = 0

AllCredentials = []
pRootOnly = False # It doesn't make any sense to think that this script would be used for only the root account
AllCredentials = get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, pProfile, RegionList, pRoles, pTiming)

AllStackInstances =

# for account_number in AccountList:
# 	try:
# 		account_credentials = Inventory_Modules.get_child_access3(aws_acct, account_number)
# 	except ClientError as my_Error:
# 		if str(my_Error).find("AuthFailure") > 0:
# 			print(f"{pProfile}: Authorization Failure for account {account_number}")
# 		elif str(my_Error).find("AccessDenied") > 0:
# 			print(f"{pProfile}: Access Denied Failure for account {account_number}")
# 		else:
# 			print(f"{pProfile}: Other kind of failure for account {account_number}")
# 			print(my_Error)
# 		continue

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

if precoveryFlag:
	Stack_Instances = []
	for item in StacksFound:
		Stack_Instances.append({'Account': item['Account'],
		                        'Region' : item['Region'],
		                        'Status' : item['StackStatus'],
		                        'StackId': item['StackArn']})
	stack_ids = {'Stack_instances': Stack_Instances, 'Success': True}
	BigString = {'AccountNumber'    : aws_acct.acct_number,
	             'AccountToMove'    : None,
	             'ManagementAccount': aws_acct.MgmtAccount,
	             'NewStackSetName'  : pNewStackSetName,
	             'OldStackSetName'  : pOldStackSetName,
	             'ProfileUsed'      : pProfile,
	             'Region'           : pRegion,
	             'stack_ids'        : stack_ids}
	file_data = json.dumps(BigString, sort_keys=True, indent=4 * ' ')
	OutputFilename = (f"{pOldStackSetName}-{pNewStackSetName}-{aws_acct.acct_number}-{pRegion}")
	with open(OutputFilename, 'w') as out:
		print(file_data, file=out)

	if pTiming:
		print(ERASE_LINE)
		print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")

print()
print("Thanks for using this script...")
print()
