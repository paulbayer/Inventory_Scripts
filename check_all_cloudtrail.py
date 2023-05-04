#!/usr/bin/env python3


# import boto3
import Inventory_Modules
from Inventory_Modules import display_results, get_all_credentials
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from time import time
from botocore.exceptions import ClientError
from prettytable import PrettyTable

import logging

init()
__version__ = "2023.05.04"

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
parser.rootOnly()
parser.timing()
parser.verbosity()
parser.version(__version__)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pSkipAccounts = args.SkipAccounts
pAccounts = args.Accounts
pSkipProfiles = args.SkipProfiles
pRootOnly = args.RootOnly
pTiming = args.Time
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")


##################
def check_account_for_cloudtrail(credentials):
	"""
	Note that this function checks the passed in account credentials only
	"""
	Trails = dict()
	try:
		logging.info(f"Checking account {credentials['AccountId']} in region {credentials['Region']}")
		Trails = Inventory_Modules.find_account_cloudtrail2(credentials, credentials['Region'])
		logging.info(f"Root Account: {credentials['MgmtAccount']} Account: {credentials['AccountId']} Region: {credentials['Region']} | Found {len(Trails['trailList'])} trails")
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			logging.error(f"Authorization Failure accessing account {credentials['AccountId']} in {credentials['Region']} region")
			logging.warning(f"It's possible that the region {credentials['Region']} hasn't been opted-into")
			pass
	if 'trailList' in Trails.keys():
		for y in range(len(Trails['trailList'])):
			Trails['trailList'][y]['MgmtAccount'] = credentials['MgmtAccount']
			Trails['trailList'][y]['AccountId'] = credentials['AccountId']
			Trails['trailList'][y]['Region'] = credentials['Region']
			Trails['trailList'][y]['TrailName'] = Trails['trailList'][y]['Name']
			Trails['trailList'][y]['MultiRegion'] = Trails['trailList'][y]['IsMultiRegionTrail']
			Trails['trailList'][y]['OrgTrail'] = "OrgTrail" if Trails['trailList'][y]['IsOrganizationTrail'] else "Account Trail"
			Trails['trailList'][y]['Bucket'] = Trails['trailList'][y]['S3BucketName']
			Trails['trailList'][y]['KMS'] = Trails['trailList'][y]['KmsKeyId'] if 'KmsKeyId' in Trails.keys() else None
			Trails['trailList'][y]['CloudWatchLogArn'] = Trails['trailList'][y]['CloudWatchLogsLogGroupArn'] if 'CloudWatchLogsLogGroupArn' in Trails.keys() else None
			Trails['trailList'][y]['HomeRegion'] = Trails['trailList'][y]['HomeRegion'] if 'HomeRegion' in Trails.keys() else None
			Trails['trailList'][y]['SNSTopicName'] = Trails['trailList'][y]['SNSTopicName'] if 'SNSTopicName' in Trails.keys() else None
		# fmt = '%-12s %-12s %-10s %-15s %-20s %-20s %-12s'
		# print(fmt % (faws_acct.acct_number, account['AccountId'], region, InstanceType, Name, Engine, State))
		# print(f"{faws_acct.acct_number:12s} {account['AccountId']:12s} {region:15s} {TrailName:40s} {Trails['trailList'][y]['OrgTrail']:15s} {Bucket:45s} ")
	return (Trails['trailList'])


def check_accounts_for_cloudtrail(faws_acct, fRegionList=None):
	"""
	Note that this function checks the account AND any children accounts in the Org.
	"""
	ChildAccounts = faws_acct.AllCredentials
	AllTrails = []
	account_credentials = {'Role': 'Nothing'}
	Trails = dict()
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
				Trails = Inventory_Modules.find_account_cloudtrail2(account_credentials, region)
				logging.info(f"Root Account: {faws_acct.acct_number} Account: {account['AccountId']} Region: {region} | Found {len(Trails['trailList'])} trails")
			except ClientError as my_Error:
				if str(my_Error).find("AuthFailure") > 0:
					logging.error(f"Authorization Failure accessing account {account['AccountId']} in {region} region")
					logging.warning(f"It's possible that the region {region} hasn't been opted-into")
					pass
			if 'trailList' in Trails.keys():
				for y in range(len(Trails['trailList'])):
					Trails['trailList'][y]['MgmtAccount'] = account['MgmtAccount']
					Trails['trailList'][y]['AccountId'] = account['AccountId']
					Trails['trailList'][y]['Region'] = region
					TrailName = Trails['trailList'][y]['Name']
					MultiRegion = Trails['trailList'][y]['IsMultiRegionTrail']
					Trails['trailList'][y]['OrgTrail'] = "OrgTrail" if Trails['trailList'][y]['IsOrganizationTrail'] else "Account Trail"
					Bucket = Trails['trailList'][y]['S3BucketName']
					KMS = Trails['trailList'][y]['KmsKeyId'] if 'KmsKeyId' in Trails.keys() else None
					Trails['trailList'][y]['KMS'] = KMS
					CloudWatchLogArn = Trails['trailList'][y]['CloudWatchLogsLogGroupArn'] if 'CloudWatchLogsLogGroupArn' in Trails.keys() else None
					Trails['trailList'][y]['CloudWatchLogArn'] = CloudWatchLogArn
					HomeRegion = Trails['trailList'][y]['HomeRegion'] if 'HomeRegion' in Trails.keys() else None
					Trails['trailList'][y]['HomeRegion'] = HomeRegion
					SNSTopicName = Trails['trailList'][y]['SNSTopicName'] if 'SNSTopicName' in Trails.keys() else None
					Trails['trailList'][y]['SNSTopicName'] = SNSTopicName
					# fmt = '%-12s %-12s %-10s %-15s %-20s %-20s %-12s'
					# print(fmt % (faws_acct.acct_number, account['AccountId'], region, InstanceType, Name, Engine, State))
					print(f"{faws_acct.acct_number:12s} {account['AccountId']:12s} {region:15s} {TrailName:40s} {Trails['trailList'][y]['OrgTrail']:15s} {Bucket:45s} ")
			AllTrails.extend(Trails['trailList'])
	return (AllTrails)


##################

ERASE_LINE = '\x1b[2K'

logging.info(f"Profiles: {pProfiles}")
if pTiming:
	begin_time = time()

print()
print(f"Checking for CloudTrails... ")
print()

TrailsFound = []
AllChildAccounts = []
RegionList = ['us-east-1']
if pSkipAccounts is None:
	pSkipAccounts = []
account_num = 0

AllChildAccounts = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)
for credential in AllChildAccounts:
	account_num += 1
	print(f"{ERASE_LINE}Checking account {credential['AccountId']} in region {credential['Region']}- {account_num} of {len(AllChildAccounts)}", end='\r')
	TrailsFound.extend(check_account_for_cloudtrail(credential))

# if pProfiles is None:  # Default use case from the classes
# 	logging.info("Using whatever the default profile is")
# 	aws_acct = aws_acct_access()
# 	RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
# 	logging.warning(f"Default profile will be used")
# 	TrailsFound.extend(check_accounts_for_cloudtrail(aws_acct, RegionList))
# 	AllChildAccounts.extend(aws_acct.ChildAccounts)
# else:
# 	ProfileList = Inventory_Modules.get_profiles(fprofiles=pProfiles)
# 	logging.warning(f"These profiles are being checked {ProfileList}.")
# 	for profile in ProfileList:
# 		aws_acct = aws_acct_access(profile)
# 		logging.warning(f"Looking at {profile} account now... ")
# 		RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
# 		TrailsFound.extend(check_accounts_for_cloudtrail(aws_acct, RegionList))
# 		AllChildAccounts.extend(aws_acct.ChildAccounts)

ChildAccountList = [[item['MgmtAccount'], item['AccountId']] for item in AllChildAccounts]
ChildAccountsWithCloudTrail = [[item['MgmtAccount'], item['AccountId']] for item in TrailsFound]
ProblemAccounts = [item[1] for item in ChildAccountList if item not in ChildAccountsWithCloudTrail]
UniqueRegions = list(set([item['Region'] for item in AllChildAccounts]))

print()
# fmt = '%-12s %-12s %-15s %-40s %-15s %-45s'
# print(fmt % ("Root Acct #", "Account #", "Region", "Trail Name", "Org Trail", "Bucket Name"))
# print(fmt % ("-----------", "---------", "------", "----------", "---------", "-----------"))

display_dict = {'AccountId'  : {'Format': '15s', 'DisplayOrder': 2, 'Heading': 'Account Number'},
				'MgmtAccount': {'Format': '15s', 'DisplayOrder': 1, 'Heading': 'Parent Acct'},
				'Region'     : {'Format': '15s', 'DisplayOrder': 3, 'Heading': 'Region'},
				'TrailName'  : {'Format': '40s', 'DisplayOrder': 5, 'Heading': 'Trail Name'},
				'OrgTrail'   : {'Format': '15s', 'DisplayOrder': 4, 'Heading': 'Org Trail?'},
				'Bucket'     : {'Format': '20s', 'DisplayOrder': 6, 'Heading': 'S3 Bucket'}}
sorted_Results = sorted(TrailsFound, key=lambda d: (d['MgmtAccount'], d['AccountId'], d['Region'], d['TrailName']))
display_results(sorted_Results, display_dict, "None")

# print(ERASE_LINE)
# if verbose < 50:
# 	print(f"This table represents the summary of CloudTrail within the Org:")
# 	x = PrettyTable()
# 	x.field_names = ['Root Account', 'Account', 'Region', 'CloudTrail Name', 'Org Trail', 'Bucket Name']
# 	x.align["CloudTrail Name"] = "l"
# 	x.align["Bucket Name"] = "l"
# 	x.align["Org Trail"] = "l"
#
# 	# This is done to show which accounts DO NOT have a CloudTrail enabled...
# 	for item in ChildAccountList:
# 		MgmtAccount = item[0]
# 		ChildAccount = item[1]
# 		for region in RegionList:
# 			trailFound = False
# 			for trail in TrailsFound:
# 				if trail['AccountId'] == ChildAccount and trail['Region'] == region:
# 					x.add_row([trail['MgmtAccount'], trail['AccountId'], region, trail['Name'], trail['OrgTrail'], trail['S3BucketName']])
# 					trailFound = True
# 			if not trailFound:
# 				x.add_row([MgmtAccount, ChildAccount, region, 'None', 'None', 'None'])
# 	print()
# 	print(x)
print(f"These accounts were skipped - as requested: {pSkipAccounts}")
print(f"These accounts didn't seem to have a CloudTrail in the regions specified: {[acct for acct in ProblemAccounts if acct not in pSkipAccounts]}")
print()
print(f"Found {len(TrailsFound)} trails across {len(AllChildAccounts)} accounts across {len(UniqueRegions)} regions")
print()
if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time} seconds{Fore.RESET}")
print("Thank you for using this script")
print()
