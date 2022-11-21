#!/usr/bin/env python3


import Inventory_Modules
from ArgumentsClass import CommonArguments
# import boto3
from time import time
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
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
pTiming = args.Time
pDefault = args.pDefault
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'
SkipProfiles = ["default"]

if pTiming:
	begin_time = time()

NumVpcsFound = 0
NumRegions = 0
print()
fmt = '%-20s %-15s %-21s %-20s %-12s %-10s'
print(fmt % ("Account", "Region", "Vpc ID", "CIDR", "Is Default?", "Vpc Name"))
print(fmt % ("-------", "------", "------", "----", "-----------", "--------"))
# RegionList = Inventory_Modules.get_ec2_regions(pRegionList, pProfiles)
SoughtAllProfiles = False
AllChildAccounts = list()
NumOfRootProfiles = 0
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
# 	print("Since you specified 'all' profiles, we're going to look through ALL of your profiles. \
# 	Then we go through and determine which profiles represent the Master of an Organization and which are stand-alone accounts. \
# 	This will enable us to go through all accounts you have access to for inventorying.")
# 	logging.error("Time: %s", datetime.datetime.now())
# 	ProfileList = Inventory_Modules.get_parent_profiles('all', SkipProfiles)
# 	logging.error("Time: %s", datetime.datetime.now())
# 	logging.error("Found %s root profiles", len(ProfileList))
# 	# logging.info("Profiles Returned from function get_parent_profiles: %s",pProfile)
#
# else:
# 	ProfileList = [pProfiles]

aws_acct_list = []
if pProfiles is None:
	aws_acct = aws_acct_access()
	AllChildAccounts.extend(aws_acct.ChildAccounts)
	if aws_acct.AccountType.lower() == 'root':
		NumOfRootProfiles += 1
else:
	for profile in pProfiles:
		aws_acct = aws_acct_access()
		AllChildAccounts.extend(aws_acct.ChildAccounts)
		print(ERASE_LINE, f"Gathering all account data from account # {aws_acct.acct_number}", end="\r")
		if aws_acct.AccountType.lower() == 'root':
			NumOfRootProfiles += 1

NumOfTotalAccounts = len(AllChildAccounts)
AccountCounter = 0
logging.info(f"# of Regions: {len(pRegionList)}")
logging.info(f"# of Management Accounts: {NumOfRootProfiles}")
logging.info(f"# of Child Accounts: {NumOfTotalAccounts}")

print(f"Found {NumOfTotalAccounts} accounts to look through:")
print()
for i in range(len(AllChildAccounts)):
	# aws_acct = aws_acct_access(AllChildAccounts[i]['ParentProfile'])
	# sts_client = aws_acct.session.client('sts')
	# logging.info(f"Connecting to account {aws_acct.acct_number} using Parent Profile %s:", AllChildAccounts[i]['AccountId'], AllChildAccounts[i]['ParentProfile'])
	AccountCounter += 1
	print(f"{Fore.BLUE}{AccountCounter} of {NumOfTotalAccounts} looked at... {Fore.RESET}", end='')
	try:
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, AllChildAccounts[i]['AccountId'])
		if account_credentials['AccessError']:
			print(f"Accessing account {AllChildAccounts[i]['AccountId']} with {aws_acct.acct_number} failed...")
		aws_acct_child = aws_acct_access(ocredentials=account_credentials)
	except ClientError as my_error:
		if str(my_error).find("AuthFailure") > 0:
			print(f"Authorization Failure for account {AllChildAccounts[i]['AccountId']}")
		elif str(my_error).find("AccessDenied") > 0:
			print(f"Access Denied Failure for account {AllChildAccounts[i]['AccountId']}")
			print(my_error)
		else:
			print(f"Other kind of failure for account {AllChildAccounts[i]['AccountId']}")
			print(my_error)
			break

	# NumRegions += 1
	# NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for region in pRegionList:
		# NumProfilesInvestigated += 1
		Vpcs = dict()
		try:
			Vpcs = Inventory_Modules.find_account_vpcs3(aws_acct_child, region, pDefault)
			VpcNum = len(Vpcs['Vpcs']) if Vpcs['Vpcs'] == [] else 0
			print(f"{ERASE_LINE} Looking in account {Fore.RED}{AllChildAccounts[i]['AccountId']}{Fore.RESET} in {region} where we found {VpcNum} {vpctype} Vpcs", end='\r')
		except ClientError as my_error:
			if str(my_error).find("AuthFailure") > 0:
				logging.critical(ERASE_LINE, f"Authorization Failure for account: {AllChildAccounts[i]['AccountId']} in region {region}")
		except TypeError as my_error:
			logging.error(my_error)
			continue
		if 'Vpcs' in Vpcs.keys() and len(Vpcs['Vpcs']) > 0:
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

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time()-begin_time} seconds{Fore.RESET}")
print(ERASE_LINE)
print(f"Found {NumVpcsFound} {vpctype} Vpcs across {len(AllChildAccounts)} accounts across {len(pRegionList)} regions")
print()
print("Thank you for using this script.")
