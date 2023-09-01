#!/usr/bin/env python3

import logging
from ArgumentsClass import CommonArguments
# from account_class import aws_acct_access
import Inventory_Modules
from Inventory_Modules import get_org_accounts_from_profiles, display_results
from time import time
# from botocore.exceptions import ClientError, NoCredentialsError, InvalidConfigError
from colorama import init, Fore, Style
import sys

init()
__version__ = "2023.08.31"
ERASE_LINE = '\x1b[2K'


def parse_args(args):
	parser = CommonArguments()
	parser.multiprofile()
	parser.extendedargs()
	parser.rootOnly()
	parser.timing()
	parser.save_to_file()
	parser.verbosity()
	parser.version(__version__)

	parser.my_parser.add_argument(
		'-s', '-q', '--short',
		help="Display only brief listing of the profile accounts, and not the Child Accounts under them",
		action="store_const",
		dest="pShortform",
		const=True,
		default=False)
	parser.my_parser.add_argument(
		'-A', '--acct',
		help="Find which Org this account is a part of",
		nargs="*",
		dest="accountList",
		default=None)
	return parser.my_parser.parse_args(args)

"""
TODO:
	If they provide a profile that isn't a root profile, you should find out which org it belongs to, 
	and then show the org for that. 
	This will be difficult, since we don't know which profile that belongs to. Hmmm...
"""


##################

def all_my_orgs(fProfiles, fSkipProfiles, fAccountList, fTiming, fRootOnly, fSaveFilename, fShortform, fverbose):
	if fTiming:
		begin_time = time()
	ProfileList = Inventory_Modules.get_profiles(fSkipProfiles=fSkipProfiles, fprofiles=fProfiles)
	# print("Capturing info for supplied profiles")
	logging.warning(f"These profiles are being checked {ProfileList}.")
	print(f"Please bear with us as we run through {len(ProfileList)} profiles")
	AllProfileAccounts = get_org_accounts_from_profiles(ProfileList, progress_bar=False)
	AccountList = []
	# Rather than even try to determine if a root account is using ALZ, I've just removed it. I'll take out the column eventually.
	landing_zone = 'N/A'

	if fTiming:
		print()
		print(f"It's taken {Fore.GREEN}{time() - begin_time:.2f}{Fore.RESET} seconds to find profile accounts...")
		print()
	fmt = '%-23s %-15s %-15s %-12s %-10s'
	print("<------------------------------------>")
	print(fmt % ("Profile Name", "Account Number", "Payer Org Acct", "Org ID", "Root Acct?"))
	print(fmt % ("------------", "--------------", "--------------", "------", "----------"))

	for item in AllProfileAccounts:
		# Print results for all profiles
		try:
			if fRootOnly and not item['RootAcct']:
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
	FailedProfiles = [i['profile'] for i in AllProfileAccounts if not i['Success']]
	OrgsFound = [i['MgmtAcct'] for i in AllProfileAccounts if i['RootAcct']]

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

	if not fShortform:
		NumOfOrgAccounts = 0
		ClosedAccounts = []
		FailedAccounts = 0
		account = dict()
		if fSaveFilename is None:
			fmt = '%-23s %-15s %-6s'
			child_fmt = "\t\t%-20s %-20s %-20s"
			print()
			print(fmt % ("Organization's Profile", "Root Account", "ALZ"))
			print(fmt % ("----------------------", "------------", "---"))
			for item in AllProfileAccounts:
				# AllProfileAccounts holds the list of account class objects of the accounts associated with the profiles it found.
				if item['Success'] and not item['RootAcct']:
					account.update(item['aws_acct'].ChildAccounts[0])
					account.update({'Profile': item['profile']})
					AccountList.append(account.copy())
				elif item['Success'] and item['RootAcct']:
					for i in item['aws_acct'].ChildAccounts:
						account.update(i)
						account.update({'Profile': item['profile']})
						AccountList.append(account.copy())
					NumOfOrgAccounts += len(item['aws_acct'].ChildAccounts)
					print(f"{item['profile']:23s}{Style.BRIGHT} {item['MgmtAcct']:15s}{Style.RESET_ALL} {Fore.RED if landing_zone else Fore.RESET}{landing_zone:6s}{Fore.RESET}")
					print(f"\t\t{'Child Account Number':20s} {'Child Account Status':20s} {'Child Email Address':20s}")
					for child_acct in item['aws_acct'].ChildAccounts:
						print(f"\t\t{Fore.RED if not child_acct['AccountStatus'] == 'ACTIVE' else ''}{child_acct['AccountId']:20s} {child_acct['AccountStatus']:20s} {child_acct['AccountEmail']:20s}{Fore.RESET if not child_acct['AccountStatus'] == 'ACTIVE' else ''}")
						if not child_acct['AccountStatus'] == 'ACTIVE':
							ClosedAccounts.append(child_acct['AccountId'])
				elif not item['Success']:
					FailedAccounts += 1
					continue

		elif fSaveFilename is not None:
			# The user specified a file name, which means they want a (pipe-delimited) CSV file with the relevant output.
			display_dict = {'MgmtAccount'  : {'DisplayOrder': 1, 'Heading': 'Parent Acct'},
			                'AccountId'    : {'DisplayOrder': 2, 'Heading': 'Account Number'},
			                'AccountStatus': {'DisplayOrder': 3, 'Heading': 'Account Status', 'Condition': ['SUSPENDED', 'CLOSED']},
			                'AccountEmail' : {'DisplayOrder': 4, 'Heading': 'Email'}}
			sorted_Results = sorted(AllProfileAccounts, key=lambda d: (d['MgmtAccount'], d['AccountId']))
			display_results(sorted_Results, display_dict, "None", fSaveFilename)

		StandAloneAccounts = [x['AccountId'] for x in AccountList if x['MgmtAccount'] == x['AccountId'] and x['AccountEmail'] == 'Not an Org Management Account']
		FailedProfiles = [i['profile'] for i in AllProfileAccounts if not i['Success']]
		OrgsFound = [i['MgmtAcct'] for i in AllProfileAccounts if i['RootAcct']]
		StandAloneAccounts.sort()
		FailedProfiles.sort()
		OrgsFound.sort()
		ClosedAccounts.sort()

		print()
		print(f"Number of Organizations: {len(OrgsFound)}")
		print(f"Number of Organization Accounts: {NumOfOrgAccounts}")
		print(f"Number of Standalone Accounts: {len(StandAloneAccounts)}")
		print(f"Number of suspended or closed accounts: {len(ClosedAccounts)}")
		print(f"Number of profiles that failed: {len(FailedProfiles)}")
		if fverbose < 50:
			print("----------------------")
			print(f"The following accounts are the Org Accounts: {OrgsFound}")
			print(f"The following accounts are Standalone: {StandAloneAccounts}")
			print(f"The following accounts are closed or suspended: {ClosedAccounts}")
			print(f"The following profiles failed: {FailedProfiles}")
			print("----------------------")
		print()
		return_response = {'OrgsFound'         : OrgsFound,
		                   'StandAloneAccounts': StandAloneAccounts,
		                   'ClosedAccounts'    : ClosedAccounts,
		                   'FailedProfiles'    : FailedProfiles,
		                   'AccountList'       : AccountList}
	else:
		# The user specified "short-form" which means they don't want any information on child accounts.
		return_response = {'OrgsFound'         : OrgsFound,
		                   'FailedProfiles'    : FailedProfiles,
		                   'AllProfileAccounts': AllProfileAccounts}
		pass

	if fAccountList is not None:
		for acct in AccountList:
			if acct['AccountId'] in fAccountList:
				print("Found the requested account number:")
				print(f"Profile: {acct['Profile']} | Org: {acct['MgmtAccount']} | Account: {acct['AccountId']} | Status: {acct['AccountStatus']} | Email: {acct['AccountEmail']}")

	print()
	if fTiming:
		print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
	print("Thanks for using this script")
	print()
	return (return_response)


if __name__ == '__main__':
	args = parse_args(sys.argv[1:])

	pProfiles = args.Profiles
	pRootOnly = args.RootOnly
	pTiming = args.Time
	pSkipAccounts = args.SkipAccounts
	pSkipProfiles = args.SkipProfiles
	pverbose = args.loglevel
	pSaveFilename = args.Filename
	pShortform = args.pShortform
	pAccountList = args.accountList
	logging.basicConfig(level=pverbose, format="[%(filename)s:%(lineno)s - %(processName)s %(threadName)s %(funcName)20s() ] %(message)s")

	all_my_orgs(pProfiles, pSkipProfiles, pAccountList, pTiming, pRootOnly, pSaveFilename, pShortform, pverbose)
