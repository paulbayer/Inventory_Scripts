#!/usr/bin/env python3

import Inventory_Modules
import logging
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

init()

parser = CommonArguments()
parser.verbosity()
parser.singleprofile()
parser.multiregion()
parser.my_parser.add_argument(
	"-f", "--topic", "--fragment",
	dest="pTopicFrag",
	default=["all"],
	nargs='*',
	metavar="topic name string",
	help="String fragment of the Topic you want to find.")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegionList = args.Regions
verbose = args.loglevel
pTopicFrag = args.pTopicFrag
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'
SkipProfiles = ["default"]

aws_acct = aws_acct_access(pProfile)
NumTopicsFound = 0
NumRegions = 0
print()
fmt = '%-20s %-15s %-25s'
print(fmt % ("Account", "Region", "SNS Topic"))
print(fmt % ("-------", "------", "---------"))
RegionList = Inventory_Modules.get_ec2_regions3(aws_acct, pRegionList)
ChildAccounts = aws_acct.ChildAccounts

logging.info(f"# of Regions: {len(RegionList)}")
logging.info(f"# of Child Accounts: {len(ChildAccounts)}")

account_credentials = None
for i in range(len(ChildAccounts)):
	logging.info(f"Connecting to child account {ChildAccounts[i]['AccountId']} using account {aws_acct.acct_number}")
	try:
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, ChildAccounts[i]['AccountId'], 'us-east-1')
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{ChildAccounts[i]['MgmtAccount']}: Authorization Failure for account {ChildAccounts[i]['AccountId']}")
			print(my_Error)
		elif str(my_Error).find("AccessDenied") > 0:
			print(f"{ChildAccounts[i]['MgmtAccount']}: Access Denied Failure for account {ChildAccounts[i]['AccountId']}")
			print(my_Error)
		else:
			print(f"{ChildAccounts[i]['MgmtAccount']}: Other kind of failure for account {ChildAccounts[i]['AccountId']}")
			print(my_Error)
			break

	regionNum = 0
	for region in RegionList:
		regionNum += 1
		try:
			logging.info(f"Looking for Topics in acct {ChildAccounts[i]['AccountId']} in region {region}")
			Topics = Inventory_Modules.find_sns_topics2(account_credentials, region, pTopicFrag)
			print(f"{ERASE_LINE}On account {i+1} of {len(ChildAccounts)} in region {regionNum} of {len(RegionList)}", end='\r')
			logging.error(f"Found {len(Topics)} topics in account {Fore.RED}{ChildAccounts[i]['AccountId']}{Fore.RESET} in {region}")
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{aws_acct.acct_number} :Authorization Failure for account: {ChildAccounts[i]['AccountId']} in region {region}")
			continue
		for y in range(len(Topics)):
			print(fmt % (ChildAccounts[i]['AccountId'], region, Topics[y]))
			NumTopicsFound += 1

print(ERASE_LINE)
print(f"Found {NumTopicsFound} Topics across {len(ChildAccounts)} accounts across {len(RegionList)} regions")
print()
print("Thank you for using this script.")
