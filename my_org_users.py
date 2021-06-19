#!/usr/bin/env python3

import os
import sys
import pprint
import boto3
import Inventory_Modules
import argparse
from colorama import init, Fore, Back, Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(
	description="We\'re going to find all users and their access keys.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="To specify a specific profile, use this parameter. Default is your 'default' parameter")
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const",
	dest="loglevel",
	const=logging.DEBUG,
    default=logging.CRITICAL)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.INFO)
args = parser.parse_args()

# If plevel
	# 1: credentials file only
	# 2: config file only
	# 3: credentials and config files
pProfile = args.pProfile
verbose = args.loglevel
logging.basicConfig(level=args.loglevel)
# RegionList=[]

# SkipProfiles=["default"]
SkipProfiles = ["default", "Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

ChildAccounts = Inventory_Modules.find_child_accounts2(pProfile)

NumUsersFound = 0
print()
fmt = '%-15s %-20s'
print(fmt % ("Account Number", "User Name"))
print(fmt % ("--------------", "---------"))

sts_session = boto3.Session(profile_name=pProfile)
sts_client = sts_session.client('sts')
for account in ChildAccounts:
	role_arn = f"arn:aws:iam::{account['AccountId']}:role/AWSCloudFormationStackSetExecutionRole"
	logging.info(f"Role ARN: {role_arn}")
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-Users")['Credentials']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{account}: Authorization Failure for account {account['AccountId']}")
		break
	try:
		Users = Inventory_Modules.find_users(account_credentials)
		NumUsersFound += len(Users)
		logging.info(ERASE_LINE, "Account:", account['AccountId'], "Found", len(Users), "users")
		print(ERASE_LINE, "Account:", account['AccountId'], "Found", len(Users), "users", end='\r')
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{ERASE_LINE + profile}: Authorization Failure")
	except TypeError as my_Error:
		# print(my_Error)
		pass
	for y in range(len(Users)):
		print(fmt % (account['AccountId'], Users[y]['UserName']))
print(ERASE_LINE)
print("Found", NumUsersFound, "users across", len(ChildAccounts), "accounts")
print()
