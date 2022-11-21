#!/usr/bin/env python3

import Inventory_Modules
from Inventory_Modules import get_credentials_for_accounts_in_org
from colorama import init, Fore
from botocore.exceptions import ClientError
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access

import logging

init()

parser = CommonArguments()
parser.multiprofile()  # Allows for multiple profiles to be specified
parser.multiregion()  # Allows for multiple regions to be specified at the command line
parser.fragment()   # Allows for specifying a string fragment to be looked for
parser.extendedargs()  # Allows for SkipAccounts and Timing
parser.verbosity()  # Allows for the verbosity to be handled.
parser.rootOnly()   # Looks for the directories in the root account of the profile only
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pFragments = args.Fragments
pSkipAccounts = args.SkipAccounts
pTiming = args.Time
pRootOnly = args.RootOnly
verbose = args.loglevel

logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
logging.getLogger("botocore").setLevel(logging.CRITICAL)

SkipProfiles = ['default']

##########################

ERASE_LINE = '\x1b[2K'

credential_list = []
directories = dict()
ProfileList = Inventory_Modules.get_profiles(SkipProfiles, pProfiles)
aws_acct = aws_acct_access(ProfileList[0])
RegionList = Inventory_Modules.get_ec2_regions3(aws_acct, pRegionList)
CredentialList = []

print()

if pProfiles is None:
	try:
		aws_acct = aws_acct_access()
		# print(f"You've asked us to look through {len(pProfiles)} profiles")
		# print(f"{ERASE_LINE}Looking at account {aws_acct.acct_number} within profile: {profile}", end='\r')
		CredentialList = get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly)
		# credentials = Inventory_Modules.get_child_access3(aws_acct, aws_acct.acct_number)
		# credential_list.append(credentials)
	except AttributeError as myError:
		print(f"Failed on account: {aws_acct.acct_number}, but continuing on...")
		pass
else:
	for profile in ProfileList:
		try:
			aws_acct = aws_acct_access(profile)
			CredentialList.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly))
			# print(f"{ERASE_LINE}Looking at account {aws_acct.acct_number} within profile: {profile}", end='\r')
			# credentials = Inventory_Modules.get_child_access3(aws_acct, aws_acct.acct_number)
			# credential_list.append(credentials)
		except AttributeError as myError:
			print(f"Failed on profile: {profile}, but continuing on...")
			continue

NumInstancesFound = 0
print()
print(f"Looking through {len(RegionList)} regions and {len(ProfileList)} profiles")
print()
fmt = '%-15s %-10s %-40s %-12s %-16s %-15s %-20s %-13s'
print(fmt % ("Account", "Region", "Directory Name", "Directory Id", "Home Region", "Shared", "Type", "Owner"))
print(fmt % ("-------", "------", "--------------", "------------", "-----------", "------", "----", "-----"))

for credential in CredentialList:
	aws_acct = aws_acct_access(ocredentials=credential)
	for region in RegionList:
		print(f"{ERASE_LINE}Looking in account: {aws_acct.acct_number} in region {region}", end='\r')
		try:
			directories = Inventory_Modules.find_directories3(aws_acct, region, pFragments)
			logging.info(f"directories: {directories}")
			directoryNum = len(directories)
			print(f"{ERASE_LINE}Account: {aws_acct.acct_number} Region: {region} Found {directoryNum} directories", end='\r')
		except TypeError as my_Error:
			logging.info(f"Error: {my_Error}")
			continue
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{ERASE_LINE} Account {aws_acct.acct_number} : Authorization Failure")
		if len(directories) > 0:
			for directory in directories:
				DirectoryName = directory['DirectoryName']
				DirectoryId = directory['DirectoryId']
				HomeRegion = directory['HomeRegion']
				Status = directory['Status']
				Type = directory['Type']
				Owner = directory['Owner']
				print(fmt % (aws_acct.acct_number, region, DirectoryName, DirectoryId, HomeRegion, Status, Type, Owner))
				NumInstancesFound += 1
print(ERASE_LINE)
print(f"Found {NumInstancesFound} directories across {len(credential_list)} accounts across {len(RegionList)} regions")
print()
print("Thank you for using this script")
print()
