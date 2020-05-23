#!/usr/local/bin/python3

import os, sys, pprint
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all vpcs within any of the profiles we have access to.",
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
	"--default",
	dest="pDefaultOnly",
	metavar="Default Only flag",
	action="store_const",
	const=True,	# args.loglevel = 10
	default=False, # args.loglevel = 50
	help="Flag to determine whether default VPCs are included in the output.")
parser.add_argument(
	'-dd', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 10
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-d',
	help="Print debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING, # args.loglevel = 30
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR, # args.loglevel = 40
	default=logging.CRITICAL) # args.loglevel = 50
args = parser.parse_args()

pProfiles=args.pProfiles
pRegionList=args.pregion
pDefaultOnly=args.pDefaultOnly
verbose=args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")

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
			Vpcs=Inventory_Modules.find_profile_vpcs(profile,region,pDefaultOnly)
			logging.info("Info - Profile %s | Region %s | Found %s vpcs",profile,region,len(Vpcs))
			VpcNum=len(Vpcs['Vpcs']) if 'Vpcs' in Vpcs else 0
			print(ERASE_LINE,"Profile: {} | Region: {} | Found {} Vpcs".format(profile,region,VpcNum),end='\r')
			# print("Profile: {} | Region: {} | Found {} Vpcs".format(profile,region,VpcNum))
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print("{}: Authorization Failure connecting to {}".format(profile,region))
			pass
		except TypeError as my_Error:
			print(my_Error)
			logging.info("There was an error")
			pass
		# if 'Vpcs' in Vpcs and len(Vpcs['Vpcs']) > 0:
		if 'Vpcs' in Vpcs:	# If there are no VPCs, you can't reference the index
			logging.info("Displaying profile %s",profile)
			for y in range(len(Vpcs['Vpcs'])):
				VpcId=Vpcs['Vpcs'][y]['VpcId']
				IsDefault=Vpcs['Vpcs'][y]['IsDefault']
				CIDR=Vpcs['Vpcs'][y]['CidrBlock']
				if 'Tags' in Vpcs['Vpcs'][y]:
					logging.debug("Looking for tags")
					for z in range(len(Vpcs['Vpcs'][y]['Tags'])):
						if Vpcs['Vpcs'][y]['Tags'][z]['Key']=="Name":
							VpcName=Vpcs['Vpcs'][y]['Tags'][z]['Value']
				else:
					VpcName="No name defined"
				print(fmt % (profile,region,VpcId,CIDR,IsDefault,VpcName))
				NumVpcsFound += 1
		else:
			continue

# print(ERASE_LINE)
print("Found",NumVpcsFound,"Vpcs across",NumProfilesInvestigated,"profiles across",NumRegions,"regions")
print()
