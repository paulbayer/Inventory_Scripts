#!/usr/bin/env python3

# import boto3
import Inventory_Modules
from Inventory_Modules import display_results
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from time import time
from botocore.exceptions import ClientError

import logging

init()
__version__ = "2023.05.10"

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.rootOnly()
parser.rolestouse()
parser.verbosity()
parser.timing()
parser.version(__version__)

parser.my_parser.add_argument(
	'+R', "--ReplaceRetention",
	help="The retention you want to update to on all groups that match.",
	default=None,
	metavar="retention days",
	type=int,
	choices=[0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 2192, 2557, 2922, 3288, 3653],
	dest="pRetentionDays")
parser.my_parser.add_argument(
	'-o', "--OldRetention",
	help="The retention you want to change on all groups that match. Use '0' for 'Never'",
	default=None,
	metavar="retention days",
	type=int,
	choices=[0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 2192, 2557, 2922, 3288, 3653],
	dest="pOldRetentionDays")
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pAccessRoles = args.AccessRoles
pRetentionDays = args.pRetentionDays
pOldRetentionDays = args.pOldRetentionDays
pRootOnly = args.RootOnly
pTiming = args.Time
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

##################

ERASE_LINE = '\x1b[2K'
logging.info(f"Profiles: {pProfiles}")
account_number_format = "12s"
if pTiming:
	begin_time = time()


##################


def check_cw_groups_retention(faws_acct, fRegionList=None, faccess_roles:list=None):
	ChildAccounts = faws_acct.ChildAccounts
	AllCWLogGroups = []
	account_credentials = {'Role': 'unset'}
	if fRegionList is None:
		fRegionList = ['us-east-1']
	for account in ChildAccounts:
		if account['MgmtAccount'] != account['AccountId'] and pRootOnly:
			continue
		logging.info(f"Connecting to account {account['AccountId']}")
		try:
			account_credentials = Inventory_Modules.get_child_access3(faws_acct, account['AccountId'], faws_acct.Region, faccess_roles)
			if account_credentials['Success']:
				logging.info(f"Connected to account {account['AccountId']} using role {account_credentials['Role']}")
			else:
				logging.info(f"Access to account {account['AccountId']} in region {faws_acct.Region} failed, after trying role {'' if len(account_credentials['RolesTried']) == 1 else 's'}{account_credentials['RolesTried']}")
				continue
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
			CW_Groups = dict()
			try:
				print(f"{ERASE_LINE}Checking account {account['AccountId']} in region {region}", end='\r')
				# TODO: Will eventually support a filter for string fragments, and retention periods
				CW_Groups = Inventory_Modules.find_cw_groups_retention2(account_credentials, region)
				logging.info(
					f"Root Account: {faws_acct.acct_number} Account: {account['AccountId']} Region: {region} | Found {len(CW_Groups['logGroups'])} groups")
			except ClientError as my_Error:
				if str(my_Error).find("AuthFailure") > 0:
					logging.error(f"Authorization Failure accessing account {account['AccountId']} in {region} region")
					logging.warning(f"It's possible that the region {region} hasn't been opted-into")
					pass
			if 'logGroups' in CW_Groups.keys():
				for y in range(len(CW_Groups['logGroups'])):
					if 'retentionInDays' in CW_Groups['logGroups'][y].keys():
						CW_Groups['logGroups'][y]['Retention'] = Retention = CW_Groups['logGroups'][y]['retentionInDays']
					else:
						CW_Groups['logGroups'][y]['Retention'] = Retention = "Never"
					CW_Groups['logGroups'][y]['Name'] = Name = CW_Groups['logGroups'][y]['logGroupName']
					CW_Groups['logGroups'][y]['Size'] = Size = CW_Groups['logGroups'][y]['storedBytes']
					CW_Groups['logGroups'][y]['AccessKeyId'] = account_credentials['AccessKeyId']
					CW_Groups['logGroups'][y]['SecretAccessKey'] = account_credentials['SecretAccessKey']
					CW_Groups['logGroups'][y]['SessionToken'] = account_credentials['SessionToken']
					CW_Groups['logGroups'][y]['ParentProfile'] = faws_acct.credentials['Profile'] if faws_acct.credentials['Profile'] is not None else 'default'
					CW_Groups['logGroups'][y]['MgmtAccount'] = faws_acct.MgmtAccount
					CW_Groups['logGroups'][y]['AccountId'] = account_credentials['AccountId']
					CW_Groups['logGroups'][y]['Region'] = region
				# fmt = f'%-12s %-{account_number_format} %-15s %-10s %15d %-50s'
				# print(fmt % (faws_acct.acct_number, account['AccountId'], region, Retention, Size, Name))
				# print(f"{str(faws_acct.acct_number):{account_number_format}} {str(account['AccountId']):{account_number_format}} {region:15s} "
				# 	  f"{str(Retention):10s} {'' if Retention == 'Never' else 'days'} {Size: >15,} {Name:50s}")
				AllCWLogGroups.extend(CW_Groups['logGroups'])

	return (AllCWLogGroups)


def update_cw_groups_retention(fCWGroups=None, fOldRetentionDays=None, fRetentionDays=None):
	import boto3

	if fOldRetentionDays is None:
		fOldRetentionDays = 0
	Success = True
	for item in fCWGroups:
		cw_session = boto3.Session(aws_access_key_id=item['AccessKeyId'],
		                           aws_secret_access_key=item['SecretAccessKey'],
		                           aws_session_token=item['SessionToken'],
		                           region_name=item['Region'])
		cw_client = cw_session.client('logs')
		logging.info(f"Connecting to account {item['AccountId']}")
		try:
			print(f"{ERASE_LINE}Updating log group {item['logGroupName']} account {item['AccountId']} in region {item['Region']}", end='\r')
			if 'retentionInDays' not in item.keys():
				retentionPeriod = 'Never'
			else:
				retentionPeriod = item['retentionInDays']
			if (fOldRetentionDays == 0 and 'retentionInDays' not in item.keys()) or retentionPeriod == fOldRetentionDays:
				result = cw_client.put_retention_policy(
					logGroupName=item['logGroupName'],
					retentionInDays=fRetentionDays
				)
				print(f"Account: {item['AccountId']} in Region: {item['Region']} updated {item['logGroupName']} from {retentionPeriod} to {fRetentionDays} days")
				Updated = True
			else:
				Updated = False
				logging.info(f"Skipped {item['logGroupName']} in account: {item['AccountId']} in Region: {item['Region']} as it didn't match criteria")
			Success = True
		except ClientError as my_Error:
			logging.error(my_Error)
			Success = False
			return (Success)
	return (Success)


##################


print()
print(f"Checking for CW Log Groups... ")
print()

print()
display_dict = {'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
                'MgmtAccount'  : {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
                'AccountId'    : {'DisplayOrder': 3, 'Heading': 'Acct Number'},
                'Region'       : {'DisplayOrder': 4, 'Heading': 'Region'},
                'Retention'    : {'DisplayOrder': 5, 'Heading': 'Days Retention', 'Condition': ['Never']},
                'Name'         : {'DisplayOrder': 7, 'Heading': 'CW Log Name'},
                'Size'         : {'DisplayOrder': 6, 'Heading': 'Size (Bytes)'}}

# print(f"{str(faws_acct.acct_number):{account_number_format}} {str(account['AccountId']):{account_number_format}} {region:15s} "
#       f"{str(Retention):10s} {'' if Retention == 'Never' else 'days'} {Size: >15,} {Name:50s}")

CWGroups = []
AllChildAccounts = []
RegionList = []

if pProfiles is None:  # Default use case from the classes
	logging.info("Using whatever the default profile is")
	aws_acct = aws_acct_access()
	RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
	logging.warning(f"Default profile will be used")
	CWGroups.extend(check_cw_groups_retention(aws_acct, RegionList, pAccessRoles))
# AllChildAccounts.extend(aws_acct.ChildAccounts)
else:
	logging.warning(f"These profiles are being checked {pProfiles}.")
	ProfileList = Inventory_Modules.get_profiles(fprofiles=pProfiles, fSkipProfiles="skipplus")
	logging.warning(ProfileList)
	for profile in ProfileList:
		aws_acct = aws_acct_access(profile)
		logging.warning(f"Looking at {profile} account now... ")
		RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
		CWGroups.extend(check_cw_groups_retention(aws_acct, RegionList, pAccessRoles))
	# AllChildAccounts.extend(aws_acct.ChildAccounts)

AllChildAccounts = list(set([(x['MgmtAccount'], x['AccountId']) for x in CWGroups]))

display_results(CWGroups, display_dict, None)

print(ERASE_LINE)
totalspace = 0
for i in CWGroups:
	totalspace += i['storedBytes']
print(f"Found {len(CWGroups)} log groups across {len(AllChildAccounts)} accounts across {len(RegionList)} regions, representing {totalspace / 1024 / 1024 / 1024:,.3f} GB")
print(f"To give you a small idea - in us-east-1 - it costs $0.03 per GB per month to store (after 5GB).")
if totalspace / 1024 / 1024 / 1024 <= 5.0:
	print("Which means this is essentially free for you...")
else:
	print(f"This means you're paying about ${((totalspace / 1024 / 1024 / 1024) - 5) * 0.03:,.2f} per month in CW storage charges")

if pRetentionDays is not None:
	print(f"As per your request - updating ALL retention periods to {pRetentionDays} days")
	print(f"")
	UpdateAllRetention = input(f"This is definitely an intrusive command, so please confirm you want to do this (y/n): ") in ['Y', 'y']
	if UpdateAllRetention:
		print(f"Updating all log groups to have a {pRetentionDays} retention period")
		update_cw_groups_retention(CWGroups, pOldRetentionDays, pRetentionDays)
	else:
		print(f"No changes made")
print()
if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
print()
print("Thank you for using this script")
print()
