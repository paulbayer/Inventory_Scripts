#!/usr/bin/env python3

import os
import sys
import pprint
import Inventory_Modules
import argparse
from colorama import init, Fore, Back, Style
from botocore.exceptions import ClientError, NoCredentialsError
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
logging.basicConfig(level=args.loglevel)

SkipProfiles = ["default", "Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

NumLBsFound = 0
NumRegions = 0
print()
fmt = '%-20s %-10s %-20s %-10s %-50s'
print(fmt % ("Profile", "Region", "Load Balancer Name", "LB Status", "Load Balancer DNS Name"))
print(fmt % ("-------", "------", "------------------", "---------", "----------------------"))
RegionList = Inventory_Modules.get_ec2_regions(fregion_list=pRegionList)
ProfileList = Inventory_Modules.get_profiles(SkipProfiles, pProfiles)

for pregion in RegionList:
	NumRegions += 1
	NumProfilesInvestigated = 0  # I only care about the last run - so I don't get profiles * regions.
	for profile in ProfileList:
		NumProfilesInvestigated += 1
		try:
			aws_acct = aws_acct_access(profile)
			LoadBalancers = Inventory_Modules.find_load_balancers(aws_acct, pregion, pstackfrag, pstatus)
			LBNum = len(LoadBalancers)
			# logging.info("Profile: %-15s | Region: %-15s | Found %2d Load Balancers", profile, pregion, LBNum)
			print(
				f"{ERASE_LINE}{Fore.RED} Profile: {profile:-15s} Region: {pregion:-15s} Found {LBNum:2d} Load Balancers{Fore.RESET}",
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
print(ERASE_LINE)
print(f"{Fore.RED}Found", NumLBsFound, "Load Balancers across", NumProfilesInvestigated, "profiles across", NumRegions,
      f"regions{Fore.RESET}")
print()
