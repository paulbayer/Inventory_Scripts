#!/usr/bin/env python3

import sys

import Inventory_Modules
import argparse
import boto3
from colorama import init, Fore, Back, Style
from botocore.exceptions import ClientError

import logging

init()

parser = argparse.ArgumentParser(
	description="This script enabled the Public S3 block for all accounts within your Org.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	default=None,
	help="Preferred to specify a root profile. Default will be all Master profiles")
parser.add_argument(
	"-f", "--file",
	dest="pFile",
	metavar="file of account numbers to read",
	default=None,
	help="File should consist of account numbers - 1 per line, with CR/LF as line ending")
parser.add_argument(
	"-n", "--dry-run",
	dest="pDryRun",
	metavar="Whether to actually enable the block or just report it.",
	action="store_const",
	const=False,
	default=True,
	help="Defaults to Dry-Run so it doesn't make any changes.")
parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,        # args.loglevel = 10
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,         # args.loglevel = 20
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,      # args.loglevel = 30
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,        # args.loglevel = 40
	default=logging.CRITICAL)   # args.loglevel = 50
args = parser.parse_args()

pProfile = args.pProfile
pFile = args.pFile
pDryRun = args.pDryRun
verbose = args.loglevel
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
if pProfile is not None:
	logging.error("Using the provided profile from the command line")
	SessionToken = False
	ProfileSupplied = True
	aws_session = boto3.Session(profile_name=pProfile)
elif pProfile is None:
	# They didn't provide a profile parameter at the command line
	aws_session = boto3.Session()


##########################
def read_file(filename):
	account_list = []
	with open(filename, 'r') as f:
		line = f.readline().rstrip()
		while line:
			account_list.append(line)
			line = f.readline().rstrip()
	return(account_list)


def find_all_accounts(session_object=None):
	child_accounts = []
	sts_client = session_object.client('sts')
	my_account_number = sts_client.get_caller_identity()['Account']
	org_client = session_object.client('organizations')
	try:
		response = org_client.list_accounts()
		theresmore = True
		while theresmore:
			for account in response['Accounts']:
				logging.warning(f"Account ID: {account['Id']} | Account Email: {account['Email']}")
				child_accounts.append({'ParentAccount': my_account_number,
				                       'AccountId': account['Id'],
				                       'AccountEmail': account['Email'],
				                       'AccountStatus': account['Status']})
			if 'NextToken' in response.keys():
				theresmore = True
				response = org_client.list_accounts(NextToken=response['NextToken'])
			else:
				theresmore = False
		return (child_accounts)
	except ClientError as my_Error:
		logging.warning(f"Account {my_account_number} doesn't represent an Org Root account")
		logging.debug(my_Error)
		return()

def get_child_access2(fRootSessionObject, ParentAccountId, fChildAccount, fRegion='us-east-1', fRoleList=None):
	"""
	- fRootProfile is a string
	- fChildAccount expects an AWS account number (ostensibly of a Child Account)
	- rRegion expects a string representing one of the AWS regions ('us-east-1', 'eu-west-1', etc.)
	- fRoleList expects a list of roles to try, but defaults to a list of typical roles, in case you don't provide

	The first response object is a dict with account_credentials to pass onto other functions
	The second response object is the rolename that worked to gain access to the target account

	The format of the account credentials dict is here:
	account_credentials = {'Profile': fRootProfile,
							'AccessKeyId': ',
							'SecretAccessKey': None,
							'SessionToken': None,
							'AccountNumber': None}
	"""

	if not isinstance(fChildAccount, str):  # Make sure the passed in account number is a string
		fChildAccount = str(fChildAccount)
	sts_client = fRootSessionObject.client('sts', region_name=fRegion)
	if fChildAccount == ParentAccountId:
		explain_string = ("We're trying to get access to either the Root Account (which we already have access "
		                  "to via the profile)	or we're trying to gain access to a Standalone account. "
		                  "In either of these cases, we should just use the profile passed in, "
		                  "instead of trying to do anything fancy.")
		logging.info(explain_string)
		# TODO: Wrap this in a try/except loop
		account_credentials = sts_client.get_session_token()['Credentials']
		account_credentials['AccountNumber'] = fChildAccount
		account_credentials['ParentAccount'] = ParentAccountId
		return (account_credentials)
	if fRoleList is None:
		fRoleList = ['AWSCloudFormationStackSetExecutionRole', 'AWSControlTowerExecution',
					 'OrganizationAccountAccessRole', 'AdministratorAccess', 'Owner']
	# Initializing the "Negative Use Case" string, returning the whole list instead of only the last role it tried.
	# This way the operator knows that NONE of the roles supplied worked.
	return_string = "{} failed. Try Again".format(str(fRoleList))

	account_credentials = {'ParentAccount': ParentAccountId,
	                       'AccessKeyId': None,
	                       'SecretAccessKey': None,
	                       'SessionToken': None,
						   'AccountNumber': None}
	for role in fRoleList:
		try:
			logging.info(f"Trying to access account {fChildAccount} from account {ParentAccountId} assuming role: {role}")
			role_arn = 'arn:aws:iam::' + fChildAccount + ':role/' + role
			account_credentials = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="Find-ChildAccount-Things")['Credentials']
			# If we were successful up to this point, then we'll short-cut everything and just return the credentials that worked
			account_credentials['ParentAccount'] = ParentAccountId
			account_credentials['AccountNumber'] = fChildAccount
			return (account_credentials)
		except ClientError as my_Error:
			if my_Error.response['Error']['Code'] == 'ClientError':
				logging.info(my_Error)
			continue
	# Returns a dict object since that's what's expected
	# It will only get to the part below if the child isn't accessed properly using the roles already defined
	return (account_credentials)


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
			aws_session = boto3.Session(profile_name=AcctDict['ParentAccount'])
		s3_client = aws_session.client('s3control')
		logging.info("Checking the public access block on account {}".format(AcctDict['AccountId']))
		try:
			response = s3_client.get_public_access_block(
				AccountId=AcctDict['AccountId']
			)['PublicAccessBlockConfiguration']
		except ClientError as my_Error:
			if my_Error.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
				logging.error('No Public Access Block enabled')
				return(False)
			elif my_Error.response['Error']['Code'] == 'AccessDenied':
				logging.error("Bad credentials on account %s" % (AcctDict['AccountId']))
				return("Access Failure")
			else:
				logging.error("unexpected error on account #%s: %s" % (AcctDict['AccountId'], my_Error.response))
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
		response = s3_client.put_public_access_block(PublicAccessBlockConfiguration={
													'BlockPublicAcls': True,
													'IgnorePublicAcls': True,
													'BlockPublicPolicy': True,
													'RestrictPublicBuckets': True
												}, AccountId=AcctDict['AccountId'])
	return(response+"Updated")
##########################


ERASE_LINE = '\x1b[2K'

# Get the accounts we're going to work on
if pFile is not None:
	AccountList = read_file(pFile)


AllChildAccountList = find_all_accounts(aws_session)
print("Found {} accounts to look through".format(len(AllChildAccountList)))
for i in range(len(AllChildAccountList)):
	if AllChildAccountList[i]['AccountStatus'] == 'ACTIVE':
		print(ERASE_LINE, f"Getting credentials for account {AllChildAccountList[i]['AccountId']}    {i + 1} of {len(AllChildAccountList)}", end="\r")
		try:
			credentials = get_child_access2(aws_session,
			                                AllChildAccountList[i]['ParentAccount'],
			                                AllChildAccountList[i]['AccountId'])
			logging.info(f"Successfully got credentials for account {AllChildAccountList[i]['AccountId']}")
			AllChildAccountList[i]['AccessKeyId'] = credentials['AccessKeyId']
			AllChildAccountList[i]['SecretAccessKey'] = credentials['SecretAccessKey']
			AllChildAccountList[i]['SessionToken'] = credentials['SessionToken']
		except Exception as e:
			print(str(e))
			print(f"Failed using root account {AllChildAccountList[i]['ParentAccount']} to get credentials for acct {AllChildAccountList[i]['AccountId']}")
	else:
		print(ERASE_LINE, f"Skipping account {AllChildAccountList[i]['AccountId']} since it's SUSPENDED or CLOSED    {i + 1} of {len(AllChildAccountList)}", end="\r")

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
		logging.info(f"Checking account #{item['AccountId']} with Parent Account {item['ParentAccount']}")
		if not Enabled:
			if pDryRun:
				Updated = "DryRun"
				pass
			else:
				Updated = enable_block_s3_public_access(item)
		print(fmt % (item['ParentAccount'], item['AccountId'], Enabled, Updated))

print()
if pFile is not None:
	print("# of account in file provided: {}".format(len(AccountList)))
# print("# of Root Accounts: {}".format(len(RootProfiles)))
print("# of Child Accounts: {}".format(len(AllChildAccountList)))
print()
print("Thank you for using this script.")
