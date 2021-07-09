#!/usr/bin/env python3

import sys

import Inventory_Modules
import argparse
from ArgumentsClass import CommonArguments
import boto3
from colorama import init, Fore, Back, Style
from botocore.exceptions import ClientError

import logging

init()

parser = CommonArguments()
parser.singleprofile()
parser.multiregion()
parser.verbosity()
parser.extendedargs()
parser.my_parser.add_argument(
	"-f", "--file",
	dest="pFile",
	metavar="file of account numbers to read",
	default=None,
	help="File should consist of account numbers - 1 per line, with CR/LF as line ending")
parser.my_parser.add_argument(
	"+n", "--no-dry-run",
	dest="pDryRun",
	action="store_false",   # If supplied, it will become false, meaning it will make changes
	help="Defaults to Dry-Run so it doesn't make any changes.")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegionList = args.Regions
AccountsToSkip = args.SkipAccounts
verbose = args.loglevel
pFile = args.pFile
pDryRun = args.pDryRun
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")

'''
Code Flow:

1. Find the accounts we're going to work on
	- This might be from reading in a file, or might be from interrogating the provided organization (profile) or from scanning all the profiles available and picking out the root profiles.
		- The code is there to read in the file, but it was too much effort to try to find which profiles enabled access to those accounts, so I just found all accounts you might have access to - and we'll enable the block on everything.
	TODO: Allow for a "skip" parameter to skip specific accounts known to host websites or something. 

2. Make sure we know the Root account for every child account, and then create a dictionary of access credentials to get into that account
	- So how to find out how to access a child account? Determine profiles you have and then try each Master prpfile?
	
3. Ensure that Public Access Block is enabled on every account 
	- We check to see if it's already enabled and don't *re-enable* it.
	TODO: Maybe we find if the bucket is hosting a website, and then don't enable it on those buckets?

4. Report that we did what we were supposed to do, and any difficulties we had doing it.  
'''


##########################
def read_file(filename):
	account_list = []
	with open(filename, 'r') as f:
		line = f.readline().rstrip()
		while line:
			account_list.append(line)
			line = f.readline().rstrip()
	return(account_list)


def get_root_profiles():
	fRootProfiles = []
	AllProfiles = Inventory_Modules.get_profiles2()
	try:
		for profile in AllProfiles:
			print(ERASE_LINE, f"Checking profile {profile} to see if it's an Org Root profile", end="\r")
			response = Inventory_Modules.find_if_org_root(profile)
			if response == 'Root':
				fRootProfiles.append(profile)
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"Authorization Failure for profile {profile}")
			print(my_Error)
		elif str(my_Error).find("AccessDenied") > 0:
			print(f"Access Denied Failure for profile {profile}")
			print(my_Error)
		else:
			print(f"Other kind of failure for profile {profile}")
			print(my_Error)
	return(fRootProfiles)


def find_all_accounts(fRootProfiles):
	AllChildAccounts = []
	for profile in fRootProfiles:
		logging.error(f"Finding all accounts under Management Profile: {profile}")
		ChildAccounts = Inventory_Modules.find_child_accounts2(profile)
		AllChildAccounts.extend(ChildAccounts)
	logging.warning(f"Found {len(AllChildAccounts)} accounts")
	return(AllChildAccounts)


def check_block_s3_public_access(AcctDict=None):
	if AcctDict is None:
		logging.info("The Account info wasn't passed into the function")
		pass
	else:
		if 'AccessKeyId' in AcctDict.keys():
			logging.info("Creating credentials for child account %s ")
			aws_session = boto3.Session(aws_access_key_id=AcctDict['AccessKeyId'],
			                            aws_secret_access_key=AcctDict['SecretAccessKey'],
			                            aws_session_token=AcctDict['SessionToken'],
			                            region_name='us-east-1')
		else:
			aws_session = boto3.Session(profile_name=AcctDict['ParentProfile'])
		s3_client = aws_session.client('s3control')
		logging.info(f"Checking the public access block on account {AcctDict['AccountId']}")
		try:
			response = s3_client.get_public_access_block(
				AccountId=AcctDict['AccountId']
			)['PublicAccessBlockConfiguration']
		except ClientError as my_Error:
			if my_Error.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
				logging.error('No Public Access Block enabled')
				return(False)
			elif my_Error.response['Error']['Code'] == 'AccessDenied':
				logging.error(f"Bad credentials on account {AcctDict['AccountId']}")
				return("Access Failure")
			else:
				logging.error(f"unexpected error on account #{AcctDict['AccountId']}: {my_Error.response}")
				return("Access Failure")
		if response['BlockPublicAcls'] and response['IgnorePublicAcls'] and response['BlockPublicPolicy'] and response['RestrictPublicBuckets']:
			logging.info("Block was already enabled")
			return(True)
		else:
			logging.info("Block is not already enabled")
			return(False)


def enable_block_s3_public_access(AcctDict=None):
	if AcctDict is None:
		logging.info("The Account info wasn't passed into the function")
		return("Skipped")
	else:
		aws_session = boto3.Session(aws_access_key_id=AcctDict['AccessKeyId'],
		                          aws_secret_access_key=AcctDict['SecretAccessKey'],
		                          aws_session_token=AcctDict['SessionToken'],
		                          region_name='us-east-1')
		s3_client = aws_session.client('s3control')
		logging.info("Enabling the public access block".format(AcctDict['AccountId']))
		response = s3_client.put_public_access_block(
			PublicAccessBlockConfiguration={
				'BlockPublicAcls': True,
				'IgnorePublicAcls': True,
				'BlockPublicPolicy': True,
				'RestrictPublicBuckets': True
			},
			AccountId=AcctDict['AccountId']
		)
	return(f"{response}Updated")
##########################


ERASE_LINE = '\x1b[2K'

# Get the accounts we're going to work on
if pFile is not None:
	AccountList = read_file(pFile)

if pProfile is None:
	# Establish a dictionary of Root Accounts and get credentials for all accounts under the root
	print("No profile provided, so finding ALL accounts you have access to")
	RootProfiles = get_root_profiles()
else:
	# If a profile was provided, limit the work to just that profile
	RootProfiles = [pProfile]
AllChildAccountList = find_all_accounts(RootProfiles)
print("Found {} accounts to look through".format(len(AllChildAccountList)))
for i in range(len(AllChildAccountList)):
	if AllChildAccountList[i]['AccountStatus'] == 'ACTIVE':
		# if AllChildAccountList[i]['AccountStatus'] == 'ACTIVE' and AllChildAccountList[i]['AccountId'] in AccountList:
		print(ERASE_LINE, "Getting credentials for account {}    {} of {}".format(AllChildAccountList[i]['AccountId'], i+1, len(AllChildAccountList)), end="\r")
		try:
			credentials, _ = Inventory_Modules.get_child_access2(AllChildAccountList[i]['ParentProfile'], AllChildAccountList[i]['AccountId'])
			logging.info(f"Successfully got credentials for account {AllChildAccountList[i]['AccountId']}")
			AllChildAccountList[i]['AccessKeyId'] = credentials['AccessKeyId']
			AllChildAccountList[i]['SecretAccessKey'] = credentials['SecretAccessKey']
			AllChildAccountList[i]['SessionToken'] = credentials['SessionToken']
			# AccountList.remove(AllChildAccountList[i]['AccountId'])
		except Exception as e:
			print(str(e))
			print(f"Failed using root profile {AllChildAccountList[i]['ParentProfile']} to get credentials for acct {AllChildAccountList[i]['AccountId']}")
	else:
		print(ERASE_LINE,
		      "Skipping account {} since it's SUSPENDED or CLOSED    {} of {}".format(AllChildAccountList[i]['AccountId'], i + 1, len(AllChildAccountList)), end="\r")

print()
fmt = '%-20s %-15s %-20s %-15s'
print(fmt % ("Root Acct", "Account", "Was Block Enabled?", "Blocked Now?"))
print(fmt % ("---------", "-------", "------------------", "------------"))

print()
for item in AllChildAccountList:
	if item['AccountStatus'] == 'SUSPENDED':
		continue
	else:
		Updated = "Skipped"
		Enabled = check_block_s3_public_access(item)
		logging.info(f"Checking account #{item['AccountId']} with Parent Profile {item['ParentProfile']}")
		if not Enabled:
			if pDryRun:
				Updated = "DryRun"
				pass
			else:
				Updated = enable_block_s3_public_access(item)
		print(fmt % (item['ParentProfile'], item['AccountId'], Enabled, Updated))

print()
if pFile is not None:
	print("# of account in file provided: {}".format(len(AccountList)))
print("# of Root Accounts: {}".format(len(RootProfiles)))
print("# of Child Accounts: {}".format(len(AllChildAccountList)))
print()
print("Thank you for using this script.")
