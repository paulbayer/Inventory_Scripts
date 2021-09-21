#!/usr/bin/env python3

import boto3
import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore, Back, Style
from botocore.exceptions import ClientError, ProfileNotFound

import logging

init()

parser = CommonArguments()
parser.multiregion()
parser.singleprofile()
parser.verbosity()
parser.my_parser.add_argument(
	"-f", "--file",
	dest="pFile",
	metavar="file of account numbers to read",
	default=None,
	help="File should consist of account numbers - 1 per line, with CR/LF as line ending")
parser.my_parser.add_argument(
	"+n", "--no-dry-run",
	dest="pDryRun",
	action="store_false",       # Defaults to dry-run, only changes if you specify the parameter
	help="Defaults to Dry-Run so it doesn't make any changes, unless you specify.")

args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Regions
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

aws_acct = aws_acct_access(pProfile)


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
		print(f"Account {my_account_number} isn't a root account. This script works best with an Org Management account")
		logging.warning(f"Account {my_account_number} doesn't represent an Org Root account")
		logging.debug(my_Error)
		return()


# def get_child_access2(fRootSessionObject, ParentAccountId, fChildAccount, fRegion='us-east-1', fRoleList=None):
# 	"""
# 	- fRootProfile is a string
# 	- fChildAccount expects an AWS account number (ostensibly of a Child Account)
# 	- rRegion expects a string representing one of the AWS regions ('us-east-1', 'eu-west-1', etc.)
# 	- fRoleList expects a list of roles to try, but defaults to a list of typical roles, in case you don't provide
#
# 	The first response object is a dict with account_credentials to pass onto other functions
# 	The min response object is the rolename that worked to gain access to the target account
#
# 	The format of the account credentials dict is here:
# 	account_credentials = {'Profile': fRootProfile,
# 							'AccessKeyId': ',
# 							'SecretAccessKey': None,
# 							'SessionToken': None,
# 							'AccountNumber': None}
# 	"""
#
# 	if not isinstance(fChildAccount, str):  # Make sure the passed in account number is a string
# 		fChildAccount = str(fChildAccount)
# 	sts_client = fRootSessionObject.client('sts', region_name=fRegion)
# 	if fChildAccount == ParentAccountId:
# 		explain_string = ("We're trying to get access to either the Root Account (which we already have access "
# 		                  "to via the profile)	or we're trying to gain access to a Standalone account. "
# 		                  "In either of these cases, we should just use the profile passed in, "
# 		                  "instead of trying to do anything fancy.")
# 		logging.info(explain_string)
# 		session_creds = fRootSessionObject._session.get_credentials()
# 		account_credentials = {'ParentAccount': ParentAccountId,
# 		                       'AccessKeyId': session_creds['access_key'],
# 		                       'SecretAccessKey': session_creds['secret_key'],
# 		                       'SessionToken': session_creds['token'],
# 		                       'AccountNumber': fChildAccount}
# 		return (account_credentials)
# 	if fRoleList is None:
# 		fRoleList = ['AWSCloudFormationStackSetExecutionRole', 'AWSControlTowerExecution',
# 					 'OrganizationAccountAccessRole', 'AdministratorAccess', 'Owner']
# 	account_credentials = {'ParentAccount': ParentAccountId,
# 	                       'AccessKeyId': None,
# 	                       'SecretAccessKey': None,
# 	                       'SessionToken': None,
# 						   'AccountNumber': None}
# 	for role in fRoleList:
# 		try:
# 			logging.info(f"Trying to access account {fChildAccount} from account {ParentAccountId} assuming role: {role}")
# 			role_arn = f"arn:aws:iam::{fChildAccount}:role/{role}"
# 			account_credentials = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="Find-ChildAccount-Things")['Credentials']
# 			# If we were successful up to this point, then we'll short-cut everything and just return the credentials that worked
# 			account_credentials['ParentAccount'] = ParentAccountId
# 			account_credentials['AccountNumber'] = fChildAccount
# 			return (account_credentials)
# 		except ClientError as my_Error:
# 			if my_Error.response['Error']['Code'] == 'ClientError':
# 				logging.info(my_Error)
# 			continue
# 	# Returns a dict object since that's what's expected
# 	# It will only get to the part below if the child isn't accessed properly using the roles already defined
# 	return (account_credentials)


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
			aws_session = aws_acct.session
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
		if 'AccessKeyId' in AcctDict.keys():
			logging.info("Creating credentials for child account %s ")
			aws_session = boto3.Session(aws_access_key_id=AcctDict['AccessKeyId'],
			                            aws_secret_access_key=AcctDict['SecretAccessKey'],
			                            aws_session_token=AcctDict['SessionToken'],
			                            region_name='us-east-1')
		else:
			aws_session = boto3.Session()
		s3_client = aws_session.client('s3control')
		logging.info("Enabling the public access block".format(AcctDict['AccountId']))
		response = s3_client.put_public_access_block(PublicAccessBlockConfiguration={
													'BlockPublicAcls': True,
													'IgnorePublicAcls': True,
													'BlockPublicPolicy': True,
													'RestrictPublicBuckets': True
												}, AccountId=AcctDict['AccountId'])
	return(f"{response}Updated")
##########################


ERASE_LINE = '\x1b[2K'

AccountList = None      # Makes the IDE Checker happy
# Get the accounts we're going to work on
if pFile is not None:
	AccountList = read_file(pFile)

if aws_acct.AccountType.lower() == 'root':
	AllChildAccountList = aws_acct.ChildAccounts
else:
	AllChildAccountList = [{
		'MgmntAccount': aws_acct.acct_number,
		'AccountId': aws_acct.acct_number,
		'AccountEmail': 'Child Account',
		'AccountStatus': aws_acct.AccountStatus}]
print(f"Found {len(AllChildAccountList)} accounts to look through")
for i in range(len(AllChildAccountList)):
	if AllChildAccountList[i]['AccountStatus'] == 'ACTIVE':
		print(ERASE_LINE, f"Getting credentials for account {AllChildAccountList[i]['AccountId']} -- {i + 1} of {len(AllChildAccountList)}", end="\r")
		try:
			credentials = Inventory_Modules.get_child_access3(aws_acct,
			                                AllChildAccountList[i]['AccountId'])
			logging.info(f"Successfully got credentials for account {AllChildAccountList[i]['AccountId']}")
			AllChildAccountList[i]['AccessKeyId'] = credentials['AccessKeyId']
			AllChildAccountList[i]['SecretAccessKey'] = credentials['SecretAccessKey']
			AllChildAccountList[i]['SessionToken'] = credentials['SessionToken']
		except Exception as e:
			print(str(e))
			print(f"Failed using root account {AllChildAccountList[i]['MgmntAccount']} to get credentials for acct {AllChildAccountList[i]['AccountId']}")
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
		try:
			Updated = "Skipped"
			Enabled = check_block_s3_public_access(item)
			logging.info(f"Checking account #{item['AccountId']} with Parent Account {item['MgmntAccount']}")
			if not Enabled:
				if pDryRun:
					Updated = "DryRun"
					pass
				else:
					Updated = enable_block_s3_public_access(item)
			print(fmt % (item['MgmntAccount'], item['AccountId'], Enabled, Updated))
		except ProfileNotFound as myError:
			logging.info(f"You've tried to update your own management account.")

print()
if pFile is not None:
	print(f"# of account in file provided: {len(AccountList)}")
print(f"# of Checked Accounts: {len(AllChildAccountList)}")
print()
print("Thank you for using this script.")
