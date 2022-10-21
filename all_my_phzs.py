#!/usr/bin/env python3


import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()

parser = CommonArguments()
parser.multiregion()
parser.multiprofile()
parser.verbosity()
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'
if pProfiles is None:
	logging.debug(f"No profile provided. Using defaults for account access")
	aws_acct = aws_acct_access()
	ProfileList = ['default']		# While we set this to "default", we'll never actually use it. This is so the for-loop below actually runs once.
else:
	logging.debug(f"Profile parameter provided. Finding profiles that match")
	ProfileList = Inventory_Modules.get_profiles(fprofiles=pProfiles)
	logging.debug(f"Using the first profile found to determine region access")
	aws_acct = aws_acct_access(ProfileList[0])
RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)

NumPHZsFound = 0
HostedZones = []
print()
fmt = '%-20s %-10s %-25s %-20s %-25s'
print(fmt % ("Account", "Region", "Hosted Zone Name", "Number of Records", "Zone ID"))
print(fmt % ("-------", "------", "----------------", "-----------------", "-------"))

for profile in ProfileList:
	if pProfiles is None:
		aws_acct = aws_acct_access()
	else:
		aws_acct = aws_acct_access(profile)
	for region in RegionList:
		try:
			HostedZones = Inventory_Modules.find_private_hosted_zones3(aws_acct, region)['HostedZones']
			PHZNum = len(HostedZones)
			logging.info(f"Account: {aws_acct.acct_number:12s} | Region: {region:15s} | Found {PHZNum:2d} Hosted Zones")
			print(f"{ERASE_LINE}{Fore.RED}Account: {aws_acct.acct_number:12s} Region: {region:15s} Found: {PHZNum:2d} Hosted Zones{Fore.RESET}", end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{profile}: Authorization Failure")
		if len(HostedZones) > 0:
			for y in range(len(HostedZones)):
				PHZName = HostedZones[y]['Name']
				Records = HostedZones[y]['ResourceRecordSetCount']
				PHZId = HostedZones[y]['Id']
				print(fmt % (aws_acct.acct_number, region, PHZName, Records, PHZId))
				NumPHZsFound += 1
print(ERASE_LINE)
print(f"{Fore.RED}Found {NumPHZsFound} Hosted Zones across {len(ProfileList)} accounts across {len(RegionList)} regions{Fore.RESET}")
print()
print("Thanks for using this script...")
print()
