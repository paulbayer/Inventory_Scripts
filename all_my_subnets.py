#!/usr/bin/env python3

# import boto3
import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError
from prettytable import PrettyTable

import logging

init()

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
parser.rootOnly()
parser.verbosity()
parser.my_parser.add_argument(
	"--ipaddress", "--ip",
	dest="pipaddresses",
	nargs="*",
	metavar="IP address",
	default=None,
	help="IP address(es) you're looking for within your VPCs")
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pSkipAccounts = args.SkipAccounts
pRootOnly = args.RootOnly
pIPaddressList = args.pipaddresses
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

##################


ERASE_LINE = '\x1b[2K'

logging.info(f"Profiles: {pProfiles}")


##################
def check_accounts_for_subnets(faws_acct, fRegionList=None, fip=None):
	"""
	Note that this function checks the account AND any children accounts in the Org.
	"""
	ChildAccounts = faws_acct.ChildAccounts
	AllSubnets = []
	account_credentials = {'Role': 'Nothing'}
	Subnets = dict()
	AccountNum = 0
	if fRegionList is None:
		fRegionList = ['us-east-1']
	for account in ChildAccounts:
		SkipAccounts = pSkipAccounts
		if account['AccountId'] in SkipAccounts:
			continue
		elif pRootOnly and not account['AccountId'] == account['MgmtAccount']:
			continue
		logging.info(f"Connecting to account {account['AccountId']}")
		AccountNum += 1
		try:
			account_credentials = Inventory_Modules.get_child_access3(faws_acct, account['AccountId'])
			logging.info(f"Connected to account {account['AccountId']} using role {account_credentials['Role']}")
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
		except KeyError as my_Error:
			logging.error(f"Account Access failed - trying to access {account['AccountId']}")
			logging.info(f"Actual Error: {my_Error}")
			pass
		except AttributeError as my_Error:
			logging.error(f"Error: Likely that one of the supplied profiles {pProfiles} was wrong")
			logging.warning(my_Error)
			continue
		for region in fRegionList:
			try:
				print(f"{ERASE_LINE}{AccountNum} / {len(ChildAccounts)}: Checking account {account['AccountId']} in region {region}", end='\r')
				Subnets = Inventory_Modules.find_account_subnets2(account_credentials, region, fip)
				logging.info(f"Root Account: {faws_acct.acct_number} Account: {account['AccountId']} Region: {region} | Found {len(Subnets['Subnets'])} subnets")
			except ClientError as my_Error:
				if str(my_Error).find("AuthFailure") > 0:
					logging.error(f"Authorization Failure accessing account {account['AccountId']} in {region} region")
					logging.warning(f"It's possible that the region {region} hasn't been opted-into")
					pass
			if 'Subnets' in Subnets.keys():
				for y in range(len(Subnets['Subnets'])):
					Subnets['Subnets'][y]['MgmtAccount'] = account['MgmtAccount']
					Subnets['Subnets'][y]['AccountId'] = account['AccountId']
					Subnets['Subnets'][y]['Region'] = region
					SubnetName = "None"
					if 'Tags' in Subnets['Subnets'][y].keys():
						for tag in Subnets['Subnets'][y]['Tags']:
							if tag['Key'] == 'Name':
								SubnetName = tag['Value']
					MapPublicIpOnLaunch = Subnets['Subnets'][y]['MapPublicIpOnLaunch']
					CIDR = Subnets['Subnets'][y]['CidrBlock']
					SubnetId = Subnets['Subnets'][y]['SubnetId']
					State = Subnets['Subnets'][y]['State']
					AvailableIpAddressCount = Subnets['Subnets'][y]['AvailableIpAddressCount']
					AvailabilityZone = Subnets['Subnets'][y]['AvailabilityZone']
					VPCId = Subnets['Subnets'][y]['VpcId'] if 'VpcId' in Subnets.keys() else None
					# fmt = '%-12s %-12s %-10s %-15s %-20s %-20s %-12s'
					# print(fmt % (faws_acct.acct_number, account['AccountId'], region, InstanceType, Name, Engine, State))
					print(f"{faws_acct.acct_number:12s} {account['AccountId']:12s} {region:15s} {SubnetName:40s} {CIDR:18s} {AvailableIpAddressCount:5d}")
			AllSubnets.extend(Subnets['Subnets'])
	return (AllSubnets)


##################


print()
print(f"Checking for CloudTrails... ")
print()

print()
fmt = '%-12s %-12s %-15s %-40s %-18s %-5s'
print(fmt % ("Root Acct #", "Account #", "Region", "Subnet Name", "CIDR", "Available IPs"))
print(fmt % ("-----------", "---------", "------", "-----------", "----", "-------------"))

SubnetsFound = []
AllChildAccounts = []
RegionList = ['us-east-1']

if pProfiles is None:  # Default use case from the classes
	logging.info("Using whatever the default profile is")
	aws_acct = aws_acct_access()
	RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
	logging.warning(f"Default profile will be used")
	SubnetsFound.extend(check_accounts_for_subnets(aws_acct, RegionList, fip=pIPaddressList))
	AllChildAccounts.extend(aws_acct.ChildAccounts)
else:
	ProfileList = Inventory_Modules.get_profiles(fprofiles=pProfiles)
	logging.warning(f"These profiles are being checked {ProfileList}.")
	for profile in ProfileList:
		aws_acct = aws_acct_access(profile)
		logging.warning(f"Looking at {profile} account now... ")
		RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
		SubnetsFound.extend(check_accounts_for_subnets(aws_acct, RegionList, fip=pIPaddressList))
		AllChildAccounts.extend(aws_acct.ChildAccounts)

print(ERASE_LINE)
print()
print(f"These accounts were skipped - as requested: {pSkipAccounts}")
print()
print(f"Found {len(SubnetsFound)} subnets across {len(AllChildAccounts)} accounts across {len(RegionList)} regions")
print()
print("Thank you for using this script")
print()
