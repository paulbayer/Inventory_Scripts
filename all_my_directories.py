#!/usr/bin/env python3

import Inventory_Modules
from Inventory_Modules import get_credentials_for_accounts_in_org, get_all_credentials, addLoggingLevel, display_results
from ArgumentsClass import CommonArguments
from colorama import init, Fore
from time import time
from botocore.exceptions import ClientError

import logging

init()
__version__ = '2023.05.04'

parser = CommonArguments()
parser.multiprofile()  # Allows for multiple profiles to be specified
parser.multiregion()  # Allows for multiple regions to be specified at the command line
parser.fragment()  # Allows for specifying a string fragment to be looked for
parser.extendedargs()  # Allows for SkipAccounts and Timing
parser.timing()  # Allows to show the time from one process to another
parser.rootOnly()  # Looks for the directories in the root account of the profile only
parser.version(__version__)
parser.verbosity()  # Allows for the verbosity to be handled.
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pFragments = args.Fragments
pAccounts = args.Accounts
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pTiming = args.Time
pRootOnly = args.RootOnly
verbose = args.loglevel

logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
logging.getLogger("botocore").setLevel(logging.CRITICAL)
addLoggingLevel('TIMING', 45)

##########################

ERASE_LINE = '\x1b[2K'
logging.info(f"Profiles: {pProfiles}")
if pTiming:
	begin_time = time()

print()
print(f"Checking for Directories... ")
print()

CredentialList = []
if pSkipAccounts is None:
	pSkipAccounts = []
if pSkipProfiles is None:
	SkipProfiles = []
account_num = 0

CredentialList = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)
if pTiming:
	print(f"{Fore.GREEN}\tAfter getting credentials, this script took {time()-begin_time} seconds{Fore.RESET}")
	print()
RegionList = list(set([x['Region'] for x in CredentialList]))
AccountList = list(set([x['AccountId'] for x in CredentialList]))
# ProfileList = list(set([x['Profile'] for x in CredentialList]))
if pTiming:
	print(f"{Fore.GREEN}\tAfter parsing out all Regions, Account and Profiles, this script took {time()-begin_time} seconds{Fore.RESET}")
	print()
# timing(pTiming)
# credential_list = []
# directories = dict()
# ProfileList = Inventory_Modules.get_profiles(SkipProfiles, pProfiles)
# aws_acct = aws_acct_access(ProfileList[0])
# RegionList = Inventory_Modules.get_ec2_regions3(aws_acct, pRegionList)
# CredentialList = []

print()

# if pProfiles is None:
# 	try:
# 		aws_acct = aws_acct_access()
# 		# print(f"You've asked us to look through {len(pProfiles)} profiles")
# 		# print(f"{ERASE_LINE}Looking at account {aws_acct.acct_number} within profile: {profile}", end='\r')
# 		profile = 'None'
# 		CredentialList = get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList)
# 	# credentials = Inventory_Modules.get_child_access3(aws_acct, aws_acct.acct_number)
# 	# credential_list.append(credentials)
# 	except AttributeError as myError:
# 		print(f"Failed on account: {aws_acct.acct_number}, but continuing on...")
# 		pass
# else:
# 	for profile in ProfileList:
# 		try:
# 			aws_acct = aws_acct_access(profile)
# 			CredentialList.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList))
# 		# print(f"{ERASE_LINE}Looking at account {aws_acct.acct_number} within profile: {profile}", end='\r')
# 		# credentials = Inventory_Modules.get_child_access3(aws_acct, aws_acct.acct_number)
# 		# credential_list.append(credentials)
# 		except AttributeError as myError:
# 			print(f"Failed on profile: {profile}, but continuing on...")
# 			continue

credential_number = 0
print()
print(f"Looking through {len(AccountList)} accounts and {len(RegionList)} regions")
print()
# fmt = '%-15s %-10s %-40s %-12s %-16s %-15s %-20s %-13s'
# print(fmt % ("Account", "Region", "Directory Name", "Directory Id", "Home Region", "Shared", "Type", "Owner"))
# print(fmt % ("-------", "------", "--------------", "------------", "-----------", "------", "----", "-----"))

AllDirectories = []
for credential in CredentialList:
	cycle_time = time()
	credential_number += 1
	# aws_acct = aws_acct_access(ocredentials=credential)
	# for region in RegionList:
	print(f"{ERASE_LINE}Looking in account: {credential['AccountId']} in region {credential['Region']}", end='\r')
	try:
		directories = Inventory_Modules.find_directories2(credential, credential['Region'], pFragments)
		# directories = Inventory_Modules.find_directories3(aws_acct, region, pFragments)
		logging.info(f"directories: {directories}")
		print(f"{ERASE_LINE}Account: {credential['AccountId']} Region: {credential['Region']} Found {len(directories)} directories", end='\r')
		if len(directories) > 0:
			for directory in directories:
				DirectoryName = directory['DirectoryName']
				DirectoryId = directory['DirectoryId']
				HomeRegion = directory['HomeRegion']
				Status = directory['Status']
				Type = directory['Type']
				Owner = directory['Owner']
				directory.update({'MgmtAccount': credential['MgmtAccount'],
								  'Region'     : credential['Region'],
								  'AccountId'  : credential['AccountId']})
				AllDirectories.append(directory)
	except TypeError as my_Error:
		logging.info(f"Error: {my_Error}")
		continue
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{ERASE_LINE} Account {credential['AccountId']} : Authorization Failure")
	if pTiming:
		print(f"{Fore.GREEN}\tJust ran for credential #{credential_number}/{len(CredentialList)}. It took {time() - cycle_time:-3f} seconds to find {len(directories)} directories in account {credential['AccountId']} in region {credential['Region']}{Fore.RESET} {len(AllDirectories)} so far")

print()
# print(fmt % (aws_acct.acct_number, credential['Region'], DirectoryName, DirectoryId, HomeRegion, Status, Type, Owner))
display_dict = {'AccountId'    : {'Format': '15s', 'DisplayOrder': 2, 'Heading': 'Account Number'},
				'MgmtAccount'  : {'Format': '15s', 'DisplayOrder': 1, 'Heading': 'Parent Acct'},
				'Region'       : {'Format': '15s', 'DisplayOrder': 3, 'Heading': 'Region'},
				'DirectoryName': {'Format': '20s', 'DisplayOrder': 4, 'Heading': 'Directory Name'},
				'DirectoryId'  : {'Format': '12s', 'DisplayOrder': 5, 'Heading': 'Directory ID?'},
				'HomeRegion'   : {'Format': '15s', 'DisplayOrder': 6, 'Heading': 'Home Region'},
				'Status'       : {'Format': '10s', 'DisplayOrder': 7, 'Heading': 'Status'},
				'Type'         : {'Format': '20s', 'DisplayOrder': 8, 'Heading': 'Type'},
				'Owner'        : {'Format': '15s', 'DisplayOrder': 9, 'Heading': 'Owner'}}
sorted_Results = sorted(AllDirectories, key=lambda d: (d['MgmtAccount'], d['AccountId'], d['Region'], d['DirectoryName']))
display_results(sorted_Results, display_dict, "None")

print(ERASE_LINE)
print(f"Found {len(AllDirectories)} directories across {len(CredentialList)} accounts across {len(RegionList)} regions")
print()
if pTiming:
	print(f"{Fore.GREEN}\tThis script took {time()-begin_time} seconds{Fore.RESET}")
	print()
print("Thank you for using this script")
print()
