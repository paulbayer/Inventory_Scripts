#!/usr/bin/env python3

import logging
from ArgumentsClass import CommonArguments
# from account_class import aws_acct_access
import Inventory_Modules
from Inventory_Modules import get_org_accounts_from_profiles
from time import time
# from botocore.exceptions import ClientError, NoCredentialsError, InvalidConfigError
from colorama import init, Fore, Style

init()

parser = CommonArguments()
parser.multiprofile()
parser.rootOnly()
parser.extendedargs()
parser.verbosity()

parser.my_parser.add_argument(
		'-s', '--q', '--short',
		help="Display only brief listing of the root accounts, and not the Child Accounts under them",
		action="store_const",
		dest="shortform",
		const=True,
		default=False)
parser.my_parser.add_argument(
		'-A', '--account',
		help="Find which Org this account is a part of",
		nargs="*",
		dest="accountList",
		default=None)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRootOnly = args.RootOnly
pTiming = args.Time
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
verbose = args.loglevel
shortform = args.shortform
pAccountList = args.accountList
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(processName)s %(threadName)s %(funcName)20s() ] %(message)s")

if pTiming:
	begin_time = time()

if pSkipProfiles is None:
	pSkipProfiles = ["default"]
ERASE_LINE = '\x1b[2K'

# logging.warning("All available profiles will be shown")

"""
TODO:
	If they provide a profile that isn't a root profile, you should find out which org it belongs to, 
	and then show the org for that. 
	This will be difficult, since we don't know which profile that belongs to. Hmmm...
"""
##################


def display_results(account_item):
	"""
	Note that this function simply formats the output of the data within the list provided
	"""
	print(f"{Fore.RED if account_item['RootAcct'] else Fore.RESET}{account_item['profile']:23s} {account_item['aws_acct'].acct_number:15s} {account_item['MgmtAcct']:15s} {account_item['OrgId']:12s} {account_item['RootAcct']}{Fore.RESET}")


##################

ProfileList = Inventory_Modules.get_profiles(fSkipProfiles=pSkipProfiles, fprofiles=pProfiles)
# print("Capturing info for supplied profiles")
logging.warning(f"These profiles are being checked {ProfileList}.")
print(f"Please bear with us as we run through {len(ProfileList)} profiles")
AllProfileAccounts = get_org_accounts_from_profiles(ProfileList, progress_bar=False)
AccountList = []
landing_zone = 'N/A'

if pTiming:
	print()
	print(f"It's been {time()-begin_time} seconds...")
	print()
fmt = '%-23s %-15s %-15s %-12s %-10s'
print("<------------------------------------>")
print(fmt % ("Profile Name", "Account Number", "Payer Org Acct", "Org ID", "Root Acct?"))
print(fmt % ("------------", "--------------", "--------------", "------", "----------"))

for item in AllProfileAccounts:
	# Print results for all profiles
	try:
		if pRootOnly and not item['RootAcct']:
			continue
		else:
			# display_results(item)
			if item['Success']:
				print(f"{Fore.RED if item['RootAcct'] else ''}{item['profile']:23s} {item['aws_acct'].acct_number:15s} {item['MgmtAcct']:15s} {str(item['OrgId']):12s} {item['RootAcct']}{Fore.RESET}")
			else:
				print(f"{item['profile']} errored. Message: {item['ErrorMessage']}")
	except TypeError as my_Error:
		print(f"Error - {my_Error} on {item}")
		pass
'''
If I create a dictionary from the Root Accts and Root Profiles Lists - 
I can use that to determine which profile belongs to the root user of my (child) account.
But this dictionary is only guaranteed to be valid after ALL profiles have been checked, 
so... it doesn't solve our issue - unless we don't write anything to the screen until *everything* is done, 
and we keep all output in another dictionary - where we can populate the missing data at the end... 
but that takes a long time, since nothing would be sent to the screen in the meantime.
'''
# If I'm looking for only the root accounts, when I find something that isn't a root account, don't print anything and continue on.

print(ERASE_LINE)
print("-------------------")

if not shortform:
	fmt = '%-23s %-15s %-6s'
	child_fmt = "\t\t%-20s %-20s %-20s"
	print()
	print(fmt % ("Organization's Profile", "Root Account", "ALZ"))
	print(fmt % ("----------------------", "------------", "---"))
	NumOfOrgAccounts = 0
	NumOfNonOrgAccounts = 0
	FailedAccounts = 0
	account = dict()
	for item in AllProfileAccounts:
		if item['Success'] and not item['RootAcct']:
			account.update(item['aws_acct'].ChildAccounts[0])
			account.update({'Profile': item['profile']})
			# print(account)
			AccountList.append(account.copy())
			NumOfNonOrgAccounts += len(item['aws_acct'].ChildAccounts)
		elif item['Success'] and item['RootAcct']:
			# account = dict()
			# landing_zone = Inventory_Modules.find_if_alz(item['profile'])['ALZ']
			for i in item['aws_acct'].ChildAccounts:
				account.update(i)
				account.update({'Profile': item['profile']})
				# print(account)
				AccountList.append(account.copy())
			NumOfOrgAccounts += len(item['aws_acct'].ChildAccounts)
			# if landing_zone:
			# 	fmt = f"%-23s {Style.BRIGHT}%-15s {Style.RESET_ALL}{Fore.RED}%-6s {Fore.RESET}"
			# else:
			# 	fmt = f"%-23s {Style.BRIGHT}%-15s {Style.RESET_ALL}%-6s"
			print(f"{item['profile']:23s}{Style.BRIGHT} {item['MgmtAcct']:15s}{Style.RESET_ALL} {Fore.RED if landing_zone else Fore.RESET}{landing_zone}{Fore.RESET}")
			print(f"\t\t{'Child Account Number':20s} {'Child Account Status':20s} {'Child Email Address':20s}")
			# for account in sorted(child_accounts):
			for child_acct in item['aws_acct'].ChildAccounts:
				print(f"\t\t{child_acct['AccountId']:20s} {child_acct['AccountStatus']:20s} {child_acct['AccountEmail']:20s}")
		elif not item['Success']:
			FailedAccounts += 1
			continue

	print()
	print(f"Number of Organizations: {len([i for i in AllProfileAccounts if i['RootAcct']])}")
	print(f"Number of Organization Accounts: {NumOfOrgAccounts}")
	print(f"Number of Standalone Accounts: {NumOfNonOrgAccounts}")
	print(f"Number of profiles that failed: {FailedAccounts}")
	logging.error(f"List of failed profiles: {[i['profile'] for i in AllProfileAccounts if not i['Success']]}")
	print()

if pAccountList is not None:
	# AccountList = (x for x in AllAccounts if x['Success'])
	# for x in AccountList:
		# print(x)
	for acct in AccountList:
		if acct['AccountId'] in pAccountList:
			print("Found the requested account number:")
			print(f"Profile: {acct['Profile']} | Account: {acct['AccountId']} | Org: {acct['MgmtAccount']}")

print()
if pTiming:
	print(f"{Fore.GREEN}This script took {time() - begin_time} seconds{Fore.RESET}")
print("Thanks for using this script")
print()
