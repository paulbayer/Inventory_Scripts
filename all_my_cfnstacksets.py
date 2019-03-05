#!/usr/local/bin/python3

import os, sys, pprint
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
# parser.add_argument(
# 	"-c","--creds",
# 	dest="plevel",
# 	metavar="Creds",
# 	default="1",
# 	help="Which credentials file to use for investigation.")
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
	const=logging.INFO,
    default=logging.CRITICAL)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.WARNING)
args = parser.parse_args()

# If plevel
	# 1: credentials file only
	# 2: config file only
	# 3: credentials and config files
pProfiles=args.pProfiles
# plevel=args.plevel
pRegionList=args.pregion
pstackfrag=args.pstackfrag
pstatus=args.pstatus
verbose=args.loglevel
logging.basicConfig(level=args.loglevel)
# RegionList=[]

# if pRegionList

# SkipProfiles=["default"]
SkipProfiles=["default","Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

print()
fmt='%-20s %-15s %-15s %-50s'
print(fmt % ("Profile","Region","Status","StackSet Name"))
print(fmt % ("-------","------","------","-------------"))
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList=Inventory_Modules.get_profiles(pProfiles,SkipProfiles)# pprint.pprint(RegionList)
# sys.exit(1)
for region in RegionList:
	for profile in ProfileList: #Inventory_Modules.get_profiles(pProfiles,plevel,SkipProfiles):
		try:
			StackSets=Inventory_Modules.find_stacksets(profile,region,pstackfrag)
			logging.warning("Profile: %s | Region: %s | Found %s Stacksets", profile, region, len(StackSets))
			print(ERASE_LINE,Fore.RED+"Profile: ",profile,"Region: ",pregion,"Found",StackNum,"Stacks"+Fore.RESET,end="\r")
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure")
		if len(Stacks) > 0:
			for y in range(len(Stacks)):
				StackName=Stacks[y]['StackName']
				StackStatus=Stacks[y]['StackStatus']
		# 		IsDefault=Stacks['StackSummaries'][y]['IsDefault']
		# 		CIDR=Stacks['Stacks'][y]['CidrBlock']
		# 		if 'Tags' in Stacks['StackSummaries'][y]:
		# 			for z in range(len(Stacks['StackSummaries'][y]['Tags'])):
		# 				if Stacks['StackSummaries'][y]['Tags'][z]['Key']=="Name":
		# 					VpcName=Stacks['StackSummaries'][y]['Tags'][z]['Value']
		# 		else:
		# 			VpcName="No name defined"
				print(fmt % (profile,pregion,StackStatus,StackName))
				NumStacksFound += 1
print(ERASE_LINE)
print(Fore.RED+"Found",NumStacksFound,"Stacks across",NumProfilesInvestigated,"profiles across",NumRegions,"regions"+Fore.RESET)
print()
