#!/usr/bin/env python3


import Inventory_Modules
from datetime import datetime, timedelta
from colorama import init, Fore
from botocore.exceptions import ClientError
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access

import logging

init()
parser = CommonArguments()
parser.verbosity()
parser.multiprofile()
parser.multiregion()

parser.my_parser.add_argument(
		"-f", "--fragment",
		dest="pstackfrag",
		metavar="CloudFormation stack fragment",
		default="all",
		help="String fragment of the cloudformation stack or stackset(s) you want to check for.")
parser.my_parser.add_argument(
		"-s", "--status",
		dest="pstatus",
		metavar="CloudFormation status",
		default="active",
		help="String that determines whether we only see 'CREATE_COMPLETE' or 'DELETE_COMPLETE' too")
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pstackfrag = args.pstackfrag
pstatus = args.pstatus
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

SkipProfiles = ["default", "Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

NumLBsFound = 0
RegionList = Inventory_Modules.get_ec2_regions(fregion_list=pRegionList)
ProfileList = Inventory_Modules.get_profiles(SkipProfiles, pProfiles)
NumRegions = len(RegionList)
OneRegionCycle = timedelta(seconds=0)
OneProfileCycle = timedelta(seconds=0)
print()
print(f"Looking through {NumRegions} regions and {len(ProfileList)} profiles")
print()
fmt = '%-20s %-10s %-20s %-10s %-50s'
print(fmt % ("Profile", "Region", "Load Balancer Name", "LB Status", "Load Balancer DNS Name"))
print(fmt % ("-------", "------", "------------------", "---------", "----------------------"))

for pregion in RegionList:
	NumProfilesInvestigated = 0  # I only care about the last run - so I don't get profiles * regions.
	for profile in ProfileList:
		ProfileStart = datetime.now().astimezone()
		NumProfilesInvestigated += 1
		try:
			logging.debug(f"Trying Profile: {profile} next")
			aws_acct = aws_acct_access(profile)
			LoadBalancers = Inventory_Modules.find_load_balancers3(aws_acct, pregion, pstackfrag, pstatus)
			print(
				f"{ERASE_LINE}{Fore.RED} Profile: {profile:15s} Region: {pregion} of {NumRegions} | "
				f"Found {NumLBsFound} Load Balancers{Fore.RESET} | {OneProfileCycle.seconds*((len(ProfileList)*NumRegions)-NumProfilesInvestigated)} seconds to go",
				end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{profile}: Authorization Failure")
		if len(LoadBalancers) > 0:
			for y in range(len(LoadBalancers)):
				LBName = LoadBalancers[y]['LoadBalancerName']
				LBStatus = LoadBalancers[y]['State']['Code']
				LBDNSName = LoadBalancers[y]['DNSName']
				print(fmt % (profile, pregion, LBName, LBStatus, LBDNSName))
				NumLBsFound += 1
		ProfileEnd = datetime.now().astimezone()
		OneProfileCycle = ProfileEnd - ProfileStart
	NumRegions -= 1

print(ERASE_LINE)
print(f"{Fore.RED}Found {NumLBsFound} Load Balancers across {NumProfilesInvestigated} profiles across {len(RegionList)} regions{Fore.RESET}")
print()
