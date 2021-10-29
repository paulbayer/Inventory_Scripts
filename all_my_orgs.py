#!/usr/bin/env python3

import os
import sys
import logging
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
import Inventory_Modules
from botocore.exceptions import ClientError, NoCredentialsError, InvalidConfigError
from colorama import init, Fore, Style

init()

parser = CommonArguments()
parser.multiprofile()
parser.verbosity()
parser.my_parser.add_argument(
		'-R', '--root',
		help="Display only the root accounts found in the profiles",
		action="store_const",
		dest="rootonly",
		const=True,
		default=False)
parser.my_parser.add_argument(
		'-s', '--q', '--short',
		help="Display only brief listing of the root accounts, and not the Child Accounts under them",
		action="store_const",
		dest="shortform",
		const=True,
		default=False)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
verbose = args.loglevel
rootonly = args.rootonly
shortform = args.shortform
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

SkipProfiles = ["default"]
ERASE_LINE = '\x1b[2K'

RootAccts = []  # List of the Organization Root's Account Number
RootProfiles = []  # List of the Organization Root's profiles

logging.warning("All available profiles will be shown")
ProfileList = Inventory_Modules.get_profiles(fSkipProfiles=SkipProfiles, fprofiles=pProfiles)
# ShowEverything = True

"""
TODO:
	If they provide a profile that isn't a root profile, you should find out which org it belongs to, 
	and then show the org for that. 
	This will be difficult, since we don't know which profile that belongs to. Hmmm...
"""

fmt = '%-23s %-15s %-27s %-12s %-10s'
print("------------------------------------")
print(fmt % ("Profile Name", "Account Number", "Payer Org Acct", "Org ID", "Root Acct?"))
print(fmt % ("------------", "--------------", "--------------", "------", "----------"))
NumProfiles = 0
FailedProfiles = []
for profile in ProfileList:
	try:
		NumProfiles += 1
		print(f"{ERASE_LINE}Trying profile {NumProfiles} of {len(ProfileList)}", end='\r')
		aws_acct = aws_acct_access(profile)
		ErrorFlag = False
		RootAcct = False
		if aws_acct.acct_number in ['123456789012', 'Failure']:
			ErrorFlag = True
			logging.info(f"Access to the profile {profile} has failed")
			FailedProfiles.append(profile)
			pass
		elif aws_acct.AccountType.lower() == 'root':  # The Account is deemed to be an Management Account
			logging.info(f"AccountNumber: {aws_acct.acct_number}")
			MnmgtAcct = aws_acct.MgmtAccount
			Email = aws_acct.MgmtEmail
			OrgId = aws_acct.OrgID
			RootAcct = True
			RootAccts.append(MnmgtAcct)
			RootProfiles.append(profile)
		elif aws_acct.AccountType.lower() in ['standalone', 'child']:
			MnmgtAcct = aws_acct.MgmtAccount
			Email = aws_acct.MgmtEmail
			OrgId = aws_acct.OrgID
			RootAcct = False
	except ClientError as my_Error:
		ErrorFlag = True
		FailedProfiles.append(profile)
		if str(my_Error).find("AWSOrganizationsNotInUseException") > 0:
			MnmgtAcct = "Not an Org Account"
		elif str(my_Error).find("AccessDenied") > 0:
			MnmgtAcct = "Acct not auth for Org API."
		elif str(my_Error).find("InvalidClientTokenId") > 0:
			MnmgtAcct = "Credentials Invalid."
		elif str(my_Error).find("ExpiredToken") > 0:
			MnmgtAcct = "Token Expired."
		else:
			print("Client Error")
			print(my_Error)
	except InvalidConfigError as my_Error:
		ErrorFlag = True
		FailedProfiles.append(profile)
		if str(my_Error).find("does not exist") > 0:
			ErrorMessage = str(my_Error)[str(my_Error).find(":"):]
			print(ErrorMessage)
		else:
			print("Credentials Error")
			print(my_Error)
	except NoCredentialsError as my_Error:
		ErrorFlag = True
		FailedProfiles.append(profile)
		if str(my_Error).find("Unable to locate credentials") > 0:
			MnmgtAcct = "This profile doesn't have credentials."
		else:
			print("Credentials Error")
			print(my_Error)
	except AttributeError as my_Error:
		ErrorFlag = True
		FailedProfiles.append(profile)
		if str(my_Error).find("object has no attribute") > 0:
			MnmgtAcct = "This profile's credentials don't work."
		else:
			print("Credentials Error")
			print(my_Error)
	'''
	If I create a dictionary from the Root Accts and Root Profiles Lists - 
	I can use that to determine which profile belongs to the root user of my (child) account.
	But this dictionary is only guaranteed to be valid after ALL profiles have been checked, 
	so... it doesn't solve our issue - unless we don't write anything to the screen until *everything* is done, 
	and we keep all output in another dictionary - where we can populate the missing data at the end... 
	but that takes a long time, since nothing would be sent to the screen in the meantime.
	'''
	# Print results for this profile
	if ErrorFlag:
		continue
	elif RootAcct:
		print(Fore.RED + fmt % (
		profile, aws_acct.acct_number, aws_acct.MgmtAccount, aws_acct.OrgID, RootAcct) + Style.RESET_ALL)
	# If I'm looking for only the root accounts, when I find something that isn't a root account, don't print anything and continue on.
	elif rootonly:
		print(ERASE_LINE, f"{profile} isn't a root account", end="\r")
	else:
		print(fmt % (profile, aws_acct.acct_number, aws_acct.MgmtAccount, aws_acct.OrgID, RootAcct))
print(ERASE_LINE)
print("-------------------")

if not shortform:
	fmt = '%-23s %-15s %-6s'
	child_fmt = "\t\t%-20s %-20s"
	print()
	print(fmt % ("Organization's Profile", "Root Account", "ALZ"))
	print(fmt % ("----------------------", "------------", "---"))
	NumOfAccounts = 0
	for profile in RootProfiles:
		aws_acct = aws_acct_access(profile)
		MnmgtAcct = aws_acct.acct_number
		child_accounts = aws_acct.ChildAccounts
		landing_zone = Inventory_Modules.find_if_alz(profile)['ALZ']
		NumOfAccounts += len(child_accounts)
		if landing_zone:
			fmt = f"%-23s {Style.BRIGHT}%-15s {Style.RESET_ALL}{Fore.RED}%-6s {Fore.RESET}"
		else:
			fmt = f"%-23s {Style.BRIGHT}%-15s {Style.RESET_ALL}%-6s"
		print(fmt % (profile, aws_acct.MgmtAccount, landing_zone))
		print(child_fmt % ("Child Account Number", "Child Email Address"))
		# for account in sorted(child_accounts):
		for account in child_accounts:
			print(child_fmt % (account['AccountId'], account['AccountEmail']))
	print()
	print("Number of Organizations:", len(RootProfiles))
	print("Number of Organization Accounts:", NumOfAccounts)
	print(f"Number of profiles that failed: {len(FailedProfiles)}")
	logging.error(f"List of failed profiles: {FailedProfiles}")

print("Thanks for using this script")
