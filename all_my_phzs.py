#!/usr/bin/env python3

import os
import sys
import pprint
import Inventory_Modules
import argparse
from colorama import init, Fore, Back, Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfiles",
	nargs="*",
	metavar="profile to use",
	default="all",
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-r", "--region",
	nargs="*",
	dest="pregion",
	metavar="region name string",
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,  # args.loglevel = 40
	default=logging.CRITICAL)  # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,  # args.loglevel = 30
	default=logging.CRITICAL)  # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,  # args.loglevel = 20
	default=logging.CRITICAL)  # args.loglevel = 50
parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,  # args.loglevel = 10
	default=logging.CRITICAL)
args = parser.parse_args()

pProfiles = args.pProfiles
pRegionList = args.pregion
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")

SkipProfiles = ["default"]

##########################
ERASE_LINE = '\x1b[2K'

NumPHZsFound = 0
NumRegions = 0
print()
fmt = '%-20s %-10s %-25s %-20s %-25s'
print(fmt % ("Profile", "Region", "Hosted Zone Name", "Number of Records", "Zone ID"))
print(fmt % ("-------", "------", "----------------", "-----------------", "-------"))
RegionList = Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList = Inventory_Modules.get_profiles(SkipProfiles, pProfiles)

for pregion in RegionList:
	NumRegions += 1
	NumProfilesInvestigated = 0  # I only care about the last run - so I don't get profiles * regions.
	for profile in ProfileList:
		NumProfilesInvestigated += 1
		try:
			HostedZones = Inventory_Modules.find_private_hosted_zones(profile, pregion)['HostedZones']
			PHZNum = len(HostedZones)
			logging.info("Profile: %-15s | Region: %-15s | Found %2d Hosted Zones", profile, pregion, PHZNum)
			print(ERASE_LINE, Fore.RED+"Profile: %-15s Region: %-15s Found %2d Hosted Zones" % (profile, pregion, PHZNum)+Fore.RESET, end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{profile}: Authorization Failure")
		if len(HostedZones) > 0:
			for y in range(len(HostedZones)):
				PHZName = HostedZones[y]['Name']
				Records = HostedZones[y]['ResourceRecordSetCount']
				PHZId = HostedZones[y]['Id']
				print(fmt % (profile, pregion, PHZName, Records, PHZId))
				NumPHZsFound += 1
print(ERASE_LINE)
print(f"{Fore.RED}Found", NumPHZsFound, "Hosted Zones across", NumProfilesInvestigated, "profiles across", NumRegions, f"regions{Fore.RESET}")
print()
print("Thanks for using this script...")
print()
