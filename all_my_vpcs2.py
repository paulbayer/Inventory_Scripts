#!/usr/local/bin/python3

import os, sys, pprint, datetime
import Inventory_Modules
import argparse, boto3
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
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 10
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
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
fmt='%-20s %-15s %-21s %-20s %-12s %-10s'
print(fmt % ("Account","Region","Vpc ID","CIDR","Is Default?","Vpc Name"))
print(fmt % ("-------","------","------","----","-----------","--------"))
RegionList=Inventory_Modules.get_ec2_regions(pRegionList,pProfile)
SoughtAllProfiles=False
AllChildAccounts=[]
AdminRole="AWSCloudFormationStackSetExecutionRole"
if pDefault:
	vpctype="default"
else:
	# I use the backspace character to make the sentence format work, since it backspaces over the prior space.
	# Totally cosmetic, but I'm an idiot that spends an hour to figure out how best to do this.
	vpctype="\b"

if pProfile in ['all','ALL','All']:
	# print(Fore.RED+"Doesn't yet work to specify 'all' profiles, since it takes a long time to go through and find only those profiles that either Org Masters, or stand-alone accounts",Fore.RESET)
	# sys.exit(1)
	SoughtAllProfiles=True
	print("Since you specified 'all' profiles, we going to look through ALL of your profiles. Then we go through and determine which profiles represent the Master of an Organization and which are stand-alone accounts. This will enable us to go through all accounts you have access to for inventorying.")
	logging.error("Time: %s",datetime.datetime.now())
	ProfileList=Inventory_Modules.get_parent_profiles(SkipProfiles)
	logging.error("Time: %s",datetime.datetime.now())
	logging.error("Found %s root profiles",len(ProfileList))
	# logging.info("Profiles Returned from function get_parent_profiles: %s",pProfile)
else:
	ProfileList=[pProfile]

for profile in ProfileList:
	print(ERASE_LINE,"Gathering all account data from {} profile".format(profile),end="\r")
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
		logging.info("Profile name: %s is a child profile",profile)
		MyAcctNumber=Inventory_Modules.find_account_number(profile)
		Accounts=[{'ParentProfile':profile,'AccountId':MyAcctNumber,'AccountEmail':'noonecares@doesntmatter.com'}]
		AllChildAccounts=Accounts

logging.info("# of Regions: %s" % len(RegionList))
logging.info("# of Master Accounts: %s" % len(ProfileList))
logging.info("# of Child Accounts: %s" % len(AllChildAccounts))


for i in range(len(AllChildAccounts)):
	aws_session = boto3.Session(profile_name=AllChildAccounts[i]['ParentProfile'])
	sts_client = aws_session.client('sts')
	logging.info("Connecting to account %s using Parent Profile %s:",AllChildAccounts[i]['AccountId'],AllChildAccounts[i]['ParentProfile'])
	role_arn = "arn:aws:iam::{}:role/{}".format(AllChildAccounts[i]['AccountId'],AdminRole)
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-Instances")['Credentials']
		account_credentials['AccountNumber']=AllChildAccounts[i]['AccountId']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print("{}: Authorization Failure for account {}".format(AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId']))
		elif str(my_Error).find("AccessDenied") > 0:
			print("{}: Access Denied Failure for account {}".format(AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId']))
			print(my_Error)
		else:
			print("{}: Other kind of failure for account {}".format(AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId']))
			print (my_Error)
			break

	# NumRegions += 1
	# NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for region in RegionList:
		# NumProfilesInvestigated += 1
		try:
			Vpcs=Inventory_Modules.find_account_vpcs(account_credentials,region,pDefault)
			VpcNum=len(Vpcs['Vpcs']) if Vpcs['Vpcs']==[] else 0
			print(ERASE_LINE,"Looking in account "+Fore.RED+"{}".format(AllChildAccounts[i]['AccountId']),Fore.RESET+"in {} where we found {} {} Vpcs".format(region,VpcNum,vpctype),end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(ERASE_LINE, "{} :Authorization Failure for account: {} in region {}".format(profile,AllChildAccounts[i]['AccountId'],region))
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
				print(fmt % (Vpcs['Vpcs'][y]['OwnerId'],region,VpcId,CIDR,IsDefault,VpcName))
				NumVpcsFound += 1
		else:
			continue

print(ERASE_LINE)
print("Found {} {} Vpcs across {} accounts across {} regions".format(NumVpcsFound,vpctype,len(AllChildAccounts),len(RegionList)))
print()
print("Thank you for using this script.")
