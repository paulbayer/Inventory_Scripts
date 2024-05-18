#!/usr/bin/env python3

from Inventory_Modules import get_all_credentials, display_results, find_directories2
from ArgumentsClass import CommonArguments
from colorama import init, Fore
from time import time
from tqdm.auto import tqdm
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

# Setup logging levels
logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)

##########################

ERASE_LINE = '\x1b[2K'
logging.info(f"Profiles: {pProfiles}")
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
	print(f"{Fore.GREEN}\tAfter getting credentials, this script took {time() - begin_time} seconds{Fore.RESET}")
	print()
RegionList = list(set([x['Region'] for x in CredentialList]))
AccountList = list(set([x['AccountId'] for x in CredentialList]))
# ProfileList = list(set([x['Profile'] for x in CredentialList]))
if pTiming:
	print(f"{Fore.GREEN}\tAfter parsing out all Regions, Account and Profiles, this script took {time() - begin_time} seconds{Fore.RESET}")
	print()

print()

credential_number = 0
print()
print(f"Looking through {len(AccountList)} accounts and {len(RegionList)} regions")
print()

AllDirectories = []
for credential in tqdm(CredentialList, desc=f"Looking through {len(CredentialList)} accounts and regions"):
	credential_number += 1
	logging.info(f"{ERASE_LINE}Looking in account: {credential['AccountId']} in region {credential['Region']}")
	try:
		directories = find_directories2(credential, credential['Region'], pFragments)
		logging.info(f"directories: {directories}")
		logging.info(f"{ERASE_LINE}Account: {credential['AccountId']} Region: {credential['Region']} Found {len(directories)} directories")
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
		if "AuthFailure" in str(my_Error):
			logging.error(f"{ERASE_LINE} Account {credential['AccountId']} : Authorization Failure")

print()
display_dict = {'MgmtAccount'  : {'DisplayOrder': 1, 'Heading': 'Parent Acct'},
                'AccountId'    : {'DisplayOrder': 2, 'Heading': 'Account Number'},
                'Region'       : {'DisplayOrder': 3, 'Heading': 'Region'},
                'DirectoryName': {'DisplayOrder': 4, 'Heading': 'Directory Name'},
                'DirectoryId'  : {'DisplayOrder': 5, 'Heading': 'Directory ID?'},
                'HomeRegion'   : {'DisplayOrder': 6, 'Heading': 'Home Region'},
                'Status'       : {'DisplayOrder': 7, 'Heading': 'Status'},
                'Type'         : {'DisplayOrder': 8, 'Heading': 'Type'},
                'Owner'        : {'DisplayOrder': 9, 'Heading': 'Owner'}}
sorted_Results = sorted(AllDirectories, key=lambda d: (d['MgmtAccount'], d['AccountId'], d['Region'], d['DirectoryName']))
display_results(sorted_Results, display_dict, "None")

print(ERASE_LINE)
print(f"Found {len(AllDirectories)} directories across {len(CredentialList)} accounts across {len(RegionList)} regions")
print()
if pTiming:
	print(f"{Fore.GREEN}\tThis script took {time() - begin_time} seconds{Fore.RESET}")
	print()
print("Thank you for using this script")
print()
