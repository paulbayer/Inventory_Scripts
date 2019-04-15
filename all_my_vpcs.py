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
	default=["default"],
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-r","--region",
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
	const=logging.INFO,
    default=logging.ERROR)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.WARNING)
args = parser.parse_args()

pProfiles=args.pProfiles
pRegionList=args.pregion
verbose=args.loglevel
logging.basicConfig(level=args.loglevel)

SkipProfiles=["default","Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

NumVpcsFound = 0
NumRegions = 0
print()
fmt='%-20s %-10s %-21s %-20s %-12s %-10s'
print(fmt % ("Profile","Region","Vpc ID","CIDR","Is Default?","Vpc Name"))
print(fmt % ("-------","------","------","----","-----------","--------"))
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList=Inventory_Modules.get_profiles(SkipProfiles,pProfiles)

logging.info("# of Regions: %s" % len(RegionList))
logging.info("# of Profiles: %s" % len(ProfileList))

for region in RegionList:
	NumRegions += 1
	NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for profile in ProfileList:
		NumProfilesInvestigated += 1
		try:
			Vpcs=Inventory_Modules.find_profile_vpcs(profile,region)
			VpcNum=len(Vpcs['Vpcs']) if Vpcs['Vpcs']==[] else 0
			print(ERASE_LINE,"Profile: {} | Region: {} | Found {} Vpcs".format(profile,region,VpcNum),end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(ERASE_LINE, profile,":Authorization Failure")
		except TypeError as my_Error:
			print(my_Error)
			pass
		if 'Vpcs' in Vpcs and len(Vpcs['Vpcs']) > 0:
			for y in range(len(Vpcs['Vpcs'])):
				VpcId=Vpcs['Vpcs'][y]['VpcId']
				IsDefault=Vpcs['Vpcs'][y]['IsDefault']
				CIDR=Vpcs['Vpcs'][y]['CidrBlock']
				if 'Tags' in Vpcs['Vpcs'][y]:
					for z in range(len(Vpcs['Vpcs'][y]['Tags'])):
						if Vpcs['Vpcs'][y]['Tags'][z]['Key']=="Name":
							VpcName=Vpcs['Vpcs'][y]['Tags'][z]['Value']
				else:
					VpcName="No name defined"
				print(fmt % (profile,region,VpcId,CIDR,IsDefault,VpcName))
				NumVpcsFound += 1
		else:
			continue

print(ERASE_LINE)
print("Found",NumVpcsFound,"Vpcs across",NumProfilesInvestigated,"profiles across",NumRegions,"regions")
print()
