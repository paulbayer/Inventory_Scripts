#!/usr/bin/env python3

import Inventory_Modules
import argparse
import boto3
import logging
from colorama import init, Fore
from botocore.exceptions import ClientError

init()

parser = argparse.ArgumentParser(
	description="This script finds sns topics in all accounts within our Organization.",
	prefix_chars='-+/')
parser.my_parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="Preferred to specify a root profile. Default will be all Master profiles")
parser.my_parser.add_argument(
	"-r", "--region",
	dest="pRegion",
	metavar="region name string",
	nargs='*',
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
parser.my_parser.add_argument(
	"-t", "--topic",
	dest="pTopicFrag",
	default=["all"],
	nargs='*',
	metavar="topic name string",
	help="String fragment of the Topic you want to find.")
parser.my_parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,        # args.loglevel = 10
	default=logging.CRITICAL)   # args.loglevel = 50
parser.my_parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,        # args.loglevel = 20
	default=logging.CRITICAL)  # args.loglevel = 50
parser.my_parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,     # args.loglevel = 30
	default=logging.CRITICAL)  # args.loglevel = 50
parser.my_parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,        # args.loglevel = 40
	default=logging.CRITICAL)   # args.loglevel = 50
args = parser.my_parser.parse_args()

pProfile = args.pProfile
pRegionList = args.pRegion
pTopicFrag = args.pTopicFrag
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'
SkipProfiles = ["default"]

NumTopicsFound = 0
NumRegions = 0
print()
fmt = '%-20s %-15s %-25s'
print(fmt % ("Account", "Region", "SNS Topic"))
print(fmt % ("-------", "------", "---------"))
RegionList = Inventory_Modules.get_ec2_regions(pRegionList, pProfile)
ChildAccounts = Inventory_Modules.find_child_accounts2(pProfile)
# AdminRole = "AWSCloudFormationStackSetExecutionRole"

logging.info(f"# of Regions: {len(RegionList)}")
logging.info(f"# of Child Accounts: {len(ChildAccounts)}")

account_credentials = None
for i in range(len(ChildAccounts)):
	# aws_session = boto3.Session(profile_name=ChildAccounts[i]['ParentProfile'])
	# sts_client = aws_session.client('sts')
	logging.info("Connecting to account %s using Parent Profile %s:", ChildAccounts[i]['AccountId'], ChildAccounts[i]['ParentProfile'])
	# role_arn = "arn:aws:iam::{}:role/{}".format(ChildAccounts[i]['AccountId'], AdminRole)
	try:
		account_credentials, _ = Inventory_Modules.get_child_access2(ChildAccounts[i]['ParentProfile'], ChildAccounts[i]['AccountId'], 'us-east-1')
		# account_credentials = sts_client.assume_role(
		# 	RoleArn=role_arn,
		# 	RoleSessionName="Find-Instances")['Credentials']
		# account_credentials['AccountNumber'] = ChildAccounts[i]['AccountId']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{ChildAccounts[i]['ParentProfile']}: Authorization Failure for account {ChildAccounts[i]['AccountId']}")
		elif str(my_Error).find("AccessDenied") > 0:
			print(f"{ChildAccounts[i]['ParentProfile']}: Access Denied Failure for account {ChildAccounts[i]['AccountId']}")
			print(my_Error)
		else:
			print(f"{ChildAccounts[i]['ParentProfile']}: Other kind of failure for account {ChildAccounts[i]['AccountId']}")
			print(my_Error)
			break

	for region in RegionList:
		try:
			logging.info("Looking for Topics")
			Topics = Inventory_Modules.find_sns_topics(account_credentials, region, pTopicFrag)
			TopicNum = len(Topics)
			print(ERASE_LINE, f"Looking in account {Fore.RED}{ChildAccounts[i]['AccountId']}", f"{Fore.RESET}in {region} where we found {TopicNum} Topics", end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{pProfile} :Authorization Failure for account: {ChildAccounts[i]['AccountId']} in region {region}")
		except TypeError as my_Error:
			print("Error:", my_Error)
			pass
		for y in range(len(Topics)):
			print(fmt % (ChildAccounts[i]['AccountId'], region, Topics[y]))
			NumTopicsFound += 1
		else:
			continue

print()
print("Found {} Topics across {} accounts across {} regions".format(NumTopicsFound, len(ChildAccounts), len(RegionList)))
print()
print("Thank you for using this script.")
