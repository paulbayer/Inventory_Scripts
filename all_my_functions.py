#!/usr/bin/env python3

import os, sys, pprint
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
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
	'-d', '--debug',
	help="Print lots of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,
	default=logging.CRITICAL)
parser.add_argument(
	'-v', '--verbose',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.INFO)
args = parser.parse_args()

pProfiles=args.pProfiles
pRegionList=args.pregion
logging.basicConfig(level=args.loglevel)

SkipProfiles=["default"]


def left(s, amount):
	return s[:amount]


def right(s, amount):
	return s[-amount:]


def mid(s, offset, amount):
	return s[offset-1:offset+amount-1]

##########################
ERASE_LINE = '\x1b[2K'
NumInstancesFound = 0
NumRegions = 0
print()
fmt='%-20s %-10s %-40s %-12s %-35s'
print(fmt % ("Profile", "Region", "Function Name", "Runtime", "Role"))
print(fmt % ("-------", "------", "-------------", "-------", "----"))
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList=Inventory_Modules.get_profiles(SkipProfiles, pProfiles)
# pprint.pprint(RegionList)
for pregion in RegionList:
	NumRegions += 1
	NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for profile in ProfileList:
		NumProfilesInvestigated += 1
		try:
			Functions=Inventory_Modules.find_profile_functions(profile, pregion)
			FunctionNum=len(Functions['Functions'])
			print(ERASE_LINE+"Profile:", profile, "Region:", pregion, "Found", FunctionNum, "functions", end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(ERASE_LINE+profile+": Authorization Failure")
		if len(Functions['Functions']) > 0:
			for y in range(len(Functions['Functions'])):
				# print("Y:",y,"Number:",len(Functions['Functions']))
				# print("Function Name:",Functions['Functions'][y]['FunctionName'])
				FunctionName=Functions['Functions'][y]['FunctionName']
				Runtime=Functions['Functions'][y]['Runtime']
				Rolet=Functions['Functions'][y]['Role']
				Role=mid(Rolet,Rolet.find("/")+2,len(Rolet))
				print(fmt % (profile,pregion,FunctionName,Runtime,Role))
				NumInstancesFound += 1
print(ERASE_LINE)
print("Found",NumInstancesFound,"functions across",NumProfilesInvestigated,"profiles across",NumRegions,"regions")
print()
