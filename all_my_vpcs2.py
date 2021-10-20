#!/usr/bin/env python3

import os
import sys
import pprint
import datetime
import Inventory_Modules
from ArgumentsClass import CommonArguments
import boto3
from account_class import aws_acct_access
from colorama import init, Fore, Back, Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.verbosity()
parser.my_parser.add_argument(
	"--default",
	dest="pDefault",
	metavar="Looking for default VPCs only",
	action="store_const",
	default=False,
	const=True,
	help="Flag to determine whether we're looking for default VPCs only.")
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pDefault = args.pDefault
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'
SkipProfiles = ["default"]

NumVpcsFound = 0
NumRegions = 0
print()
fmt = '%-20s %-15s %-21s %-20s %-12s %-10s'
print(fmt % ("Account", "Region", "Vpc ID", "CIDR", "Is Default?", "Vpc Name"))
print(fmt % ("-------", "------", "------", "----", "-----------", "--------"))
# RegionList = Inventory_Modules.get_ec2_regions(pRegionList, pProfiles)
SoughtAllProfiles = False
AllChildAccounts = list()
AdminRole = "AWSCloudFormationStackSetExecutionRole"
if pDefault:
	vpctype = "default"
else:
	# I use the backspace character to make the sentence format work, since it backspaces over the prior space.
	# Totally cosmetic, but I'm an idiot that spends an hour to figure out how best to do this.
	vpctype = "\b"

# if pProfiles in ['all', 'ALL', 'All']:
# 	# print(Fore.RED+"Doesn't yet work to specify 'all' profiles, since it takes a long time to go through and find only those profiles that either Org Masters, or stand-alone accounts",Fore.RESET)
# 	# sys.exit(1)
# 	SoughtAllProfiles = True
# 	print("Since you specified 'all' profiles, we going to look through ALL of your profiles. Then we go through and determine which profiles represent the Master of an Organization and which are stand-alone accounts. This will enable us to go through all accounts you have access to for inventorying.")
# 	logging.error("Time: %s", datetime.datetime.now())
# 	ProfileList = Inventory_Modules.get_parent_profiles('all', SkipProfiles)
# 	logging.error("Time: %s", datetime.datetime.now())
# 	logging.error("Found %s root profiles", len(ProfileList))
# 	# logging.info("Profiles Returned from function get_parent_profiles: %s",pProfile)
# else:
# 	ProfileList = [pProfiles]

for profile in pProfiles:
	aws_acct = aws_acct_access(profile)
	print(ERASE_LINE, f"Gathering all account data from {profile} profile", end="\r")
	# if not SoughtAllProfiles:
	logging.info("Checking to see which profiles are root profiles")
	ProfileIsRoot = aws_acct.AccountType
	logging.info(f"---{ProfileIsRoot}---")
	if ProfileIsRoot == 'Root':
		logging.info(f"Parent Profile name: {profile}")
		ChildAccounts = aws_acct.ChildAccounts
		# ChildAccounts=Inventory_Modules.RemoveCoreAccounts(ChildAccounts,AccountsToSkip)
		AllChildAccounts.extend(ChildAccounts)
	elif ProfileIsRoot == 'StandAlone':
		logging.info(f"Parent Profile name: {profile}")
		MyAcctNumber = aws_acct.acct_number
		Accounts = [{'ParentProfile': profile,
		             'AccountId': MyAcctNumber,
		             'AccountEmail': 'noonecares@doesntmatter.com'}]
		AllChildAccounts.extend(Accounts)
	elif ProfileIsRoot == 'Child':
		logging.info(f"Profile name: {profile} is a child profile")
		MyAcctNumber = aws_acct.acct_number
		Accounts = [{'ParentProfile': profile,
		             'AccountId': MyAcctNumber,
		             'AccountEmail': 'noonecares@doesntmatter.com'}]
		AllChildAccounts.extend(Accounts)

logging.info(f"# of Regions: {len(pRegionList)}")
logging.info(f"# of Master Accounts: {len(pProfiles)}")
logging.info(f"# of Child Accounts: {len(AllChildAccounts)}")


for i in range(len(AllChildAccounts)):
	# aws_acct = aws_acct_access(AllChildAccounts[i]['ParentProfile'])
	# sts_client = aws_acct.session.client('sts')
	# logging.info(f"Connecting to account {aws_acct.acct_number} using Parent Profile %s:", AllChildAccounts[i]['AccountId'], AllChildAccounts[i]['ParentProfile'])
	try:
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, AllChildAccounts[i]['AccountId'])
		if account_credentials['AccessError']:
			print(f"Accessing account {AllChildAccounts[i]['AccountId']} with {aws_acct.acct_number} failed...")
		aws_acct_child = aws_acct_access(ocredentials=account_credentials)
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"Authorization Failure for account {AllChildAccounts[i]['AccountId']}")
		elif str(my_Error).find("AccessDenied") > 0:
			print(f"Access Denied Failure for account {AllChildAccounts[i]['AccountId']}")
			print(my_Error)
		else:
			print(f"Other kind of failure for account {AllChildAccounts[i]['AccountId']}")
			print(my_Error)
			break

	# NumRegions += 1
	# NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for region in pRegionList:
		# NumProfilesInvestigated += 1
		try:
			Vpcs = Inventory_Modules.find_account_vpcs2(aws_acct_child, region, pDefault)
			VpcNum = len(Vpcs['Vpcs']) if Vpcs['Vpcs'] == [] else 0
			print(ERASE_LINE, f"Looking in account {Fore.RED}{AllChildAccounts[i]['AccountId']}", f"{Fore.RESET}in {region} where we found {VpcNum} {vpctype} Vpcs", end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(ERASE_LINE, f"Authorization Failure for account: {AllChildAccounts[i]['AccountId']} in region {region}")
		except TypeError as my_Error:
			print(my_Error)
			pass
		if 'Vpcs' in Vpcs and len(Vpcs['Vpcs']) > 0:
			for y in range(len(Vpcs['Vpcs'])):
				VpcId = Vpcs['Vpcs'][y]['VpcId']
				IsDefault = Vpcs['Vpcs'][y]['IsDefault']
				CIDR = Vpcs['Vpcs'][y]['CidrBlock']
				if 'Tags' in Vpcs['Vpcs'][y]:
					for z in range(len(Vpcs['Vpcs'][y]['Tags'])):
						if Vpcs['Vpcs'][y]['Tags'][z]['Key'] == "Name":
							VpcName = Vpcs['Vpcs'][y]['Tags'][z]['Value']
				else:
					VpcName = "No name defined"
				print(fmt % (Vpcs['Vpcs'][y]['OwnerId'], region, VpcId, CIDR, IsDefault, VpcName))
				NumVpcsFound += 1
		else:
			continue

print(ERASE_LINE)
print("Found {} {} Vpcs across {} accounts across {} regions".format(NumVpcsFound, vpctype, len(AllChildAccounts), len(pRegionList)))
print()
print("Thank you for using this script.")
