#!/usr/bin/env python3

import Inventory_Modules
from colorama import init, Fore
from botocore.exceptions import ClientError
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access

import logging

init()

parser = CommonArguments()
parser.multiprofile()  # Allows for a single profile to be specified
parser.multiregion()  # Allows for multiple regions to be specified at the command line
parser.fragment()   # Allows for soecifying a string fragment to be looked for
parser.verbosity()  # Allows for the verbosity to be handled.
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pFragments = args.Fragments
verbose = args.loglevel

logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

SkipProfiles = ["default"]


def left(s, amount):
	return s[:amount]


def right(s, amount):
	return s[-amount:]


def mid(s, offset, amount):
	return s[offset - 1:offset + amount - 1]


##########################

ERASE_LINE = '\x1b[2K'
NumInstancesFound = 0
ProfileList = Inventory_Modules.get_profiles(SkipProfiles, pProfiles)
aws_acct = aws_acct_access(ProfileList[0])
RegionList = Inventory_Modules.get_ec2_regions3(aws_acct, pRegionList)
print()
print(f"Looking through {len(RegionList)} regions and {len(ProfileList)} profiles")
print()
fmt = '%-20s %-10s %-40s %-12s %-35s'
print(fmt % ("Profile", "Region", "Function Name", "Runtime", "Role"))
print(fmt % ("-------", "------", "-------------", "-------", "----"))

for profile in ProfileList:
	aws_acct = aws_acct_access(profile)
	for region in RegionList:
		print(f"{ERASE_LINE}Looking in profile: {profile} in region {region}", end='\r')
		try:
			Functions = Inventory_Modules.find_lambda_functions3(aws_acct, region, pFragments)
			FunctionNum = len(Functions['Functions'])
			print(f"{ERASE_LINE}Profile: {profile} Region: {region} Found {FunctionNum} functions", end='\r')
		except TypeError as my_Error:
			logging.info(f"Error: {my_Error}")
			continue
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{ERASE_LINE + profile}: Authorization Failure")
		if len(Functions['Functions']) > 0:
			for function in range(len(Functions['Functions'])):
				# print("Y:",y,"Number:",len(Functions['Functions']))
				# print("Function Name:",Functions['Functions'][y]['FunctionName'])
				FunctionName = Functions['Functions'][function]['FunctionName']
				Runtime = Functions['Functions'][function]['Runtime']
				Rolet = Functions['Functions'][function]['Role']
				Role = mid(Rolet, Rolet.find("/") + 2, len(Rolet))
				print(fmt % (profile, region, FunctionName, Runtime, Role))
				NumInstancesFound += 1
print(ERASE_LINE)
print(f"Found {NumInstancesFound} functions across {len(ProfileList)} profiles across {len(RegionList)} regions")
print()
print("Thank you for using this script")
print()
