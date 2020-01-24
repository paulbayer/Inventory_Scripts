#!/usr/local/bin/python3

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
	"-p","--profile",
	dest="pProfiles",
	nargs="*",
	metavar="profile to use",
	default="all",
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-f","--fragment",
	dest="pstackfrag",
	metavar="CloudFormation stack fragment",
	default="all",
	help="String fragment of the cloudformation stack or stackset(s) you want to check for.")
parser.add_argument(
	"-s","--status",
	dest="pstatus",
	metavar="CloudFormation status",
	default="active",
	help="String that determines whether we only see 'CREATE_COMPLETE' or 'DELETE_COMPLETE' too")
parser.add_argument(
	"-r","--region",
	nargs="*",
	dest="pregion",
	metavar="region name string",
	default="us-east-1",
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
pstackfrag=args.pstackfrag
pstatus=args.pstatus
verbose=args.loglevel
logging.basicConfig(level=args.loglevel)

SkipProfiles=["default","Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

NumPHZsFound = 0
NumRegions = 0
print()
fmt='%-20s %-10s %-25s %-20s %-25s'
print(fmt % ("Profile","Region","Hosted Zone Name","Number of Records","Zone ID"))
print(fmt % ("-------","------","----------------","-----------------","-------"))
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList=Inventory_Modules.get_profiles(SkipProfiles,pProfiles)

for pregion in RegionList:
	NumRegions += 1
	NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for profile in ProfileList:
		NumProfilesInvestigated += 1
		try:
			HostedZones=Inventory_Modules.find_private_hosted_zones(profile,pregion)['HostedZones']
			PHZNum=len(HostedZones)
			logging.info("Profile: %-15s | Region: %-15s | Found %2d Hosted Zones", profile, pregion, PHZNum )
			print(ERASE_LINE,Fore.RED+"Profile: %-15s Region: %-15s Found %2d Hosted Zones" % (profile, pregion, PHZNum)+Fore.RESET,end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure")
		if len(HostedZones) > 0:
			for y in range(len(HostedZones)):
				PHZName=HostedZones[y]['Name']
				Records=HostedZones[y]['ResourceRecordSetCount']
				PHZId=HostedZones[y]['Id']
				print(fmt % (profile,pregion,PHZName,Records,PHZId))
				NumPHZsFound += 1
print(ERASE_LINE)
print(Fore.RED+"Found",NumPHZsFound,"Hosted Zones across",NumProfilesInvestigated,"profiles across",NumRegions,"regions"+Fore.RESET)
print()
