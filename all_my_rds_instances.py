#!/usr/bin/env python3

# import boto3
import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.verbosity()
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

##################


ERASE_LINE = '\x1b[2K'

logging.info(f"Profiles: {pProfiles}")


##################
def check_accounts_for_instances(faws_acct, fRegionList=None):
	"""
	Note that this function checks the account AND any children accounts in the Org.
	"""
	ChildAccounts = faws_acct.ChildAccounts
	AllInstances = []
	Instances = dict()
	if fRegionList is None:
		fRegionList = ['us-east-1']
	for account in ChildAccounts:
		logging.info(f"Connecting to account {account['AccountId']}")
		try:
			account_credentials = Inventory_Modules.get_child_access3(faws_acct, account['AccountId'])
			logging.info(f"Connected to account {account['AccountId']} using role {account_credentials['Role']}")
		# TODO: We shouldn't refer to "account_credentials['Role']" below, if there was an error.
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"{account['AccountId']}: Authorization failure using role: {account_credentials['Role']}")
				logging.warning(my_Error)
			elif str(my_Error).find("AccessDenied") > 0:
				logging.error(f"{account['AccountId']}: Access Denied failure using role: {account_credentials['Role']}")
				logging.warning(my_Error)
			else:
				logging.error(f"{account['AccountId']}: Other kind of failure using role: {account_credentials['Role']}")
				logging.warning(my_Error)
			continue
		except AttributeError as my_Error:
			logging.error(f"Error: Likely that one of the supplied profiles {pProfiles} was wrong")
			logging.warning(my_Error)
			continue
		for region in fRegionList:
			try:
				print(f"{ERASE_LINE}Checking account {account['AccountId']} in region {region}", end='\r')
				Instances = Inventory_Modules.find_account_rds_instances2(account_credentials, region)
				logging.info(f"Root Account: {faws_acct.acct_number} Account: {account['AccountId']} Region: {region} | Found {len(Instances['DBInstances'])} instances")
			except ClientError as my_Error:
				if str(my_Error).find("AuthFailure") > 0:
					logging.error(f"Authorization Failure accessing account {account['AccountId']} in {region} region")
					logging.warning(f"It's possible that the region {region} hasn't been opted-into")
					pass
			if 'DBInstances' in Instances.keys():
				for y in range(len(Instances['DBInstances'])):
					InstanceType = Instances['DBInstances'][y]['DBInstanceClass']
					State = Instances['DBInstances'][y]['DBInstanceStatus']
					if 'DBName' in Instances['DBInstances'][y].keys():
						Name = Instances['DBInstances'][y]['DBName']
					else:
						Name = "No Name"
					Engine = Instances['DBInstances'][y]['Engine']
					fmt = '%-12s %-12s %-10s %-15s %-20s %-20s %-12s'
					print(fmt % (faws_acct.acct_number, account['AccountId'], region, InstanceType, Name, Engine, State))
		AllInstances.extend(Instances['DBInstances'])
	return (AllInstances)


##################


print()
print(f"Checking for instances... ")
print()

print()
fmt = '%-12s %-12s %-10s %-15s %-20s %-20s %-12s'
print(fmt % ("Root Acct #", "Account #", "Region", "InstanceType", "Name", "Engine", "State"))
print(fmt % ("-----------", "---------", "------", "------------", "----", "------", "-----"))

InstancesFound = []
AllChildAccounts = []
RegionList = ['us-east-1']

if pProfiles is None:  # Default use case from the classes
	logging.info("Using whatever the default profile is")
	aws_acct = aws_acct_access()
	RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
	logging.warning(f"Default profile will be used")
	InstancesFound.extend(check_accounts_for_instances(aws_acct, RegionList))
	AllChildAccounts.extend(aws_acct.ChildAccounts)
else:
	ProfileList = Inventory_Modules.get_profiles(fprofiles=pProfiles, fSkipProfiles="skipplus")
	logging.warning(f"These profiles are being checked {ProfileList}.")
	for profile in ProfileList:
		aws_acct = aws_acct_access(profile)
		logging.warning(f"Looking at {profile} account now... ")
		RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
		InstancesFound.extend(check_accounts_for_instances(aws_acct, RegionList))
		AllChildAccounts.extend(aws_acct.ChildAccounts)

print(ERASE_LINE)
print(f"Found {len(InstancesFound)} instances across {len(AllChildAccounts)} accounts across {len(RegionList)} regions")
print()
print("Thank you for using this script")
print()
