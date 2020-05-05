#!/usr/local/bin/python3

import os, sys, pprint, datetime
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

parser = argparse.ArgumentParser(
	description="This script finds vpcs (or only default vpcs) in all accounts within our Organization.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="Preferred to specify a root profile. Default will be all Master profiles")
parser.add_argument(
	"--default",
	dest="pDefault",
	metavar="Looking for default VPCs only",
	action="store_const",
	default=False,
	const=True,
	help="Flag to determine whether we're looking for default VPCs only.")
parser.add_argument(
	"-r","--region",
	nargs="*",
	dest="pRegion",
	metavar="region name string",
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
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

pProfile=args.pProfile
pRegionList=args.pRegion
pDefault=args.pDefault
verbose=args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'
SkipProfiles=["default"]

NumVpcsFound = 0
NumRegions = 0
print()
fmt='%-20s %-10s %-21s %-20s %-12s %-10s'
print(fmt % ("Profile","Region","Vpc ID","CIDR","Is Default?","Vpc Name"))
print(fmt % ("-------","------","------","----","-----------","--------"))
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
SoughtAllProfiles=False
AllChildAccounts=[]

if pProfile in ['all','ALL','All']:
	# print(Fore.RED+"Doesn't yet work to specify 'all' profiles, since it takes a long time to go through and find only those profiles that either Org Masters, or stand-alone accounts",Fore.RESET)
	# sys.exit(1)
	SoughtAllProfiles=True
	logging.info("Profiles sent to function get_profiles3: %s",pProfile)
	print("Since you specified 'all' profiles, we going to look through ALL of your profiles. Then we go through and determine which profiles represent the Master of an Organization and which are stand-alone accounts. This will enable us to go through all accounts you have access to for inventorying.")
	logging.error("Time: %s",datetime.datetime.now())
	ProfileList=Inventory_Modules.get_parent_profiles(SkipProfiles)
	logging.error("Time: %s",datetime.datetime.now())
	logging.error("Found %s root profiles",len(ProfileList))
	# logging.info("Profiles Returned from function get_parent_profiles: %s",pProfile)
else:
	ProfileList=[pProfile]

for profile in ProfileList:
	# if not SoughtAllProfiles:
	logging.info("Checking to see which profiles are root profiles")
	ProfileIsRoot=Inventory_Modules.find_if_org_root(profile)
	logging.info("---%s---",ProfileIsRoot)
	if ProfileIsRoot == 'Root':
		logging.info("Parent Profile name: %s",profile)
		ChildAccounts=Inventory_Modules.find_child_accounts2(profile)
		# ChildAccounts=Inventory_Modules.RemoveCoreAccounts(ChildAccounts,AccountsToSkip)
		AllChildAccounts=AllChildAccounts+ChildAccounts
	elif ProfileIsRoot == 'StandAlone':
		logging.info("Parent Profile name: %s",profile)
		MyAcctNumber=Inventory_Modules.find_account_number(profile)
		Accounts=[{'ParentProfile':profile,'AccountId':MyAcctNumber,'AccountEmail':'noonecares@doesntmatter.com'}]
		AllChildAccounts=AllChildAccounts+Accounts
	elif ProfileIsRoot == 'Child':
		logging.info("Parent Profile name: %s",profile)
		AllChildAccounts=AllChildAccounts

logging.info("# of Regions: %s" % len(RegionList))
logging.info("# of Master Accounts: %s" % len(ProfileList))
logging.info("# of Child Accounts: %s" % len(AllChildAccounts))

"""
logging.info("Passed as parameter %s:",pProfiles)
logging.info("Passed to function %s:",pProfile)
logging.info("ChildAccounts %s:",ChildAccounts)
logging.info("AllChildAccounts %s:",AllChildAccounts)
"""
sys.exit(99)

for profile in ProfileList:
	# NumRegions += 1
	# NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for region in RegionList:
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
print("Thank you for using this script.")
