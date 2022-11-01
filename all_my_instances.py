#!/usr/bin/env python3

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
	ChildAccounts = faws_acct.ChildAccounts
	AllInstances = []
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
				logging.error(
					f"{account['AccountId']}: Authorization failure using role: {account_credentials['Role']}")
				logging.warning(my_Error)
			elif str(my_Error).find("AccessDenied") > 0:
				logging.error(
					f"{account['AccountId']}: Access Denied failure using role: {account_credentials['Role']}")
				logging.warning(my_Error)
			else:
				logging.error(
					f"{account['AccountId']}: Other kind of failure using role: {account_credentials['Role']}")
				logging.warning(my_Error)
			continue
		for region in fRegionList:
			try:
				Instances = None
				print(f"{ERASE_LINE}Checking account {account['AccountId']} in region {region}", end='\r')
				Instances = Inventory_Modules.find_account_instances2(account_credentials, region)
				logging.info(
					f"Root Account: {faws_acct.acct_number} Account: {account['AccountId']} Region: {region} | Found {len(Instances['Reservations'])} instances")
			except ClientError as my_Error:
				if str(my_Error).find("AuthFailure") > 0:
					logging.error(f"Authorization Failure accessing account {account['AccountId']} in {region} region")
					logging.warning(f"It's possible that the region {region} hasn't been opted-into")
					pass
			if 'Reservations' in Instances.keys():
				for y in range(len(Instances['Reservations'])):
					for z in range(len(Instances['Reservations'][y]['Instances'])):
						InstanceType = Instances['Reservations'][y]['Instances'][z]['InstanceType']
						InstanceId = Instances['Reservations'][y]['Instances'][z]['InstanceId']
						PublicDnsName = Instances['Reservations'][y]['Instances'][z]['PublicDnsName']
						State = Instances['Reservations'][y]['Instances'][z]['State']['Name']
						Name = "No Name Tag"
						try:
							for x in range(len(Instances['Reservations'][y]['Instances'][z]['Tags'])):
								if Instances['Reservations'][y]['Instances'][z]['Tags'][x]['Key'] == "Name":
									Name = Instances['Reservations'][y]['Instances'][z]['Tags'][x]['Value']
						except KeyError as my_Error:  # This is needed for when there is no "Tags" key within the describe-instances output
							logging.info(my_Error)
							pass
						if State == 'running':
							fmt = f"%-12s %-12s %-10s %-15s %-20s %-20s %-42s {Fore.RED}%-12s{Fore.RESET}"
						else:
							fmt = '%-12s %-12s %-10s %-15s %-20s %-20s %-42s %-12s'
						print(fmt % (
						faws_acct.acct_number, account['AccountId'], region, InstanceType, Name, InstanceId,
						PublicDnsName, State))
		AllInstances.extend(Instances['Reservations'])
	return (AllInstances)


##################


print()
print(f"Checking for instances... ")
print()

print()
fmt = '%-12s %-12s %-10s %-15s %-20s %-20s %-42s %-12s'
print(fmt % ("Root Acct #", "Account #", "Region", "InstanceType", "Name", "Instance ID", "Public DNS Name", "State"))
print(fmt % ("-----------", "---------", "------", "------------", "----", "-----------", "---------------", "-----"))

InstancesFound = []
AllChildAccounts = []

if pProfiles is None:  # Default use case from the classes
	logging.info("Using whatever the default profile is")
	aws_acct = aws_acct_access()
	RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
	logging.warning(f"Default profile will be used")
	InstancesFound.extend(check_accounts_for_instances(aws_acct, RegionList))
	AllChildAccounts.extend(aws_acct.ChildAccounts)
else:
	logging.warning(f"These profiles are being checked {pProfiles}.")
	ProfileList = Inventory_Modules.get_profiles(fprofiles=pProfiles, fSkipProfiles="skipplus")
	logging.warning(ProfileList)
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
