#!/usr/bin/env python3

import Inventory_Modules
import argparse
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all vpcs within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfiles",
	nargs="*",
	metavar="profile to use",
	default=["default"],
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-r", "--region",
	nargs="*",
	dest="pregion",
	metavar="region name string",
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
	"--default",
	dest="pDefaultOnly",
	metavar="Default Only flag",
	action="store_const",
	const=True,
	default=False,
	help="Flag to determine whether default VPCs are included in the output.")
parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,        # args.loglevel = 10
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,         # args.loglevel = 20
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,      # args.loglevel = 30
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,        # args.loglevel = 40
	default=logging.CRITICAL)   # args.loglevel = 50
args = parser.parse_args()

pProfiles = args.pProfiles
pRegionList = args.pregion
pDefaultOnly = args.pDefaultOnly
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")

SkipProfiles = ["default", "Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

print()
fmt = '%-20s %-10s %-21s %-20s %-12s %-10s'
print(fmt % ("Profile", "Region", "Vpc ID", "CIDR", "Is Default?", "Vpc Name"))
print(fmt % ("-------", "------", "------", "----", "-----------", "--------"))
ProfileList = Inventory_Modules.get_profiles(SkipProfiles, pProfiles)
RegionList = Inventory_Modules.get_ec2_regions(ProfileList[0], pRegionList)

logging.info(f"# of Regions: {len(RegionList)}")
logging.info(f"# of Profiles: {len(ProfileList)}")

Vpcs = {}
NumVpcsFound = 0
for region in RegionList:
	for profile in ProfileList:
		try:
			Vpcs = Inventory_Modules.find_profile_vpcs(profile, region, pDefaultOnly)
			logging.info(f"Info - Profile {profile} | Region {region} | Found {len(Vpcs)} vpcs")
			VpcNum = len(Vpcs['Vpcs']) if 'Vpcs' in Vpcs else 0
			print(f"{ERASE_LINE}Profile: {profile} | Region: {region} | Found {VpcNum} Vpcs", end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{profile}: Authorization Failure connecting to {region}")
			pass
		except TypeError as my_Error:
			print(my_Error)
			logging.info("There was an error")
			pass
		if 'Vpcs' in Vpcs.keys():  # If there are no VPCs, you can't reference the index
			logging.info(f"Displaying profile {profile}")
			VpcName = "No name defined"
			for vpc in Vpcs['Vpcs']:
				VpcId = vpc['VpcId']
				IsDefault = vpc['IsDefault']
				CIDR = vpc['CidrBlock']
				if 'Tags' in vpc:
					logging.debug("Looking for tags")
					for tag in vpc['Tags']:
						if tag['Key'] == "Name":
							VpcName = tag['Value']
				print(fmt % (profile, region, VpcId, CIDR, IsDefault, VpcName))
				NumVpcsFound += 1
		else:
			continue

print(ERASE_LINE)
print(f"Found {NumVpcsFound} Vpcs across {len(ProfileList)} profiles across {len(RegionList)} regions")
print("Thank you for using this script")
print()
