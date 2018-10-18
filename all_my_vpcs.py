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
parser.add_argument(
	"-c","--creds",
	dest="plevel",
	metavar="Creds",
	default="1",
	help="Which credentials file to use for investigation.")
parser.add_argument(
	"-p","--profile",
	dest="pProfiles",
	nargs="*",
	metavar="profile to use",
	default="all",
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
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

# If plevel
	# 1: credentials file only
	# 2: config file only
	# 3: credentials and config files
pProfiles=args.pProfiles
plevel=args.plevel
pRegionList=args.pregion
verbose=args.loglevel
logging.basicConfig(level=args.loglevel)
# RegionList=[]

# SkipProfiles=["default"]
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
ProfileList=Inventory_Modules.get_profiles(pProfiles,plevel,SkipProfiles)# pprint.pprint(RegionList)
# sys.exit(1)
for pregion in RegionList:
	NumRegions += 1
	NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for profile in ProfileList: #Inventory_Modules.get_profiles(pProfiles,plevel,SkipProfiles):
		NumProfilesInvestigated += 1
		try:
			Vpcs=Inventory_Modules.find_profile_vpcs(profile,pregion)
			VpcNum=len(Vpcs['Vpcs'])
			logging.info(ERASE_LINE,"Profile: ",profile,"Region: ",pregion,"Found",VpcNum,"Vpcs")
			print(ERASE_LINE,"Profile: ",profile,"Region: ",pregion,"Found",VpcNum,"Vpcs",end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(ERASE_LINE+profile+": Authorization Failure")
		except TypeError as my_Error:
			# print(my_Error)
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
				print(fmt % (profile,pregion,VpcId,CIDR,IsDefault,VpcName))
				NumVpcsFound += 1
print(ERASE_LINE)
print("Found",NumVpcsFound,"Vpcs across",NumProfilesInvestigated,"profiles across",NumRegions,"regions")
print()
