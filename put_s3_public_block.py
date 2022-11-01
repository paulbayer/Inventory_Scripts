#!/usr/bin/env python3

import boto3
import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError, ProfileNotFound

import logging

init()

parser = CommonArguments()
parser.singleregion()
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
		action="store_false",  # Defaults to dry-run, only changes if you specify the parameter
		help="Defaults to Dry-Run so it doesn't make any changes, unless you specify.")
parser.my_parser.add_argument(
		"--Role",
		dest="pRoleList",
		nargs="*",
		default=None,
		metavar="list of roles to access child accounts",
		help="Defaults to common list, so it's ok to trust the list we have, unless you use something different.")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Region
verbose = args.loglevel
pFile = args.pFile
pDryRun = args.pDryRun
pRoleList = args.pRoleList
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
AllChildAccountList = []


##########################
def read_file(filename):
	account_list = []
	with open(filename, 'r') as f:
		line = f.readline().rstrip()
		while line:
			account_list.append(line)
			line = f.readline().rstrip()
	return (account_list)


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
				                       'AccountId'    : account['Id'],
				                       'AccountEmail' : account['Email'],
				                       'AccountStatus': account['Status']})
			if 'NextToken' in response.keys():
				theresmore = True
				response = org_client.list_accounts(NextToken=response['NextToken'])
			else:
				theresmore = False
		return (child_accounts)
	except ClientError as my_Error:
		print(
				f"Account {my_account_number} isn't a root account. This script works best with an Org Management account")
		logging.warning(f"Account {my_account_number} doesn't represent an Org Root account")
		logging.debug(my_Error)
		return ()


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
				return (False)
			elif my_Error.response['Error']['Code'] == 'AccessDenied':
				logging.error(f"Bad credentials on account {AcctDict['AccountId']}")
				return ("Access Failure")
			else:
				logging.error(f"unexpected error on account #{AcctDict['AccountId']}: {my_Error.response}")
				return ("Access Failure")
		if response['BlockPublicAcls'] and response['IgnorePublicAcls'] and response['BlockPublicPolicy'] and response[
			'RestrictPublicBuckets']:
			logging.info("Block was already enabled")
			return (True)
		else:
			logging.info("Block is not already enabled")
			return (False)


def enable_block_s3_public_access(AcctDict=None):
	if AcctDict is None:
		logging.info("The Account info wasn't passed into the function")
		return ("Skipped")
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
			'BlockPublicAcls'      : True,
			'IgnorePublicAcls'     : True,
			'BlockPublicPolicy'    : True,
			'RestrictPublicBuckets': True
			}, AccountId=AcctDict['AccountId'])
		return_response = {'Success': True, 'Payload': response, 'Status': 'Updated'}
	return (return_response)


##########################


ERASE_LINE = '\x1b[2K'

AccountList = None  # Makes the IDE Checker happy
# Get the accounts we're going to work on
if pFile is not None:
	AccountList = read_file(pFile)

if pFile is not None:
	for accountnumber in AccountList:
		AllChildAccountList.append({'AccountId'    : accountnumber,
		                            'AccountStatus': 'ACTIVE',
		                            'MgmtAccount' : aws_acct.acct_number})
elif aws_acct.AccountType.lower() == 'root':
	AllChildAccountList = aws_acct.ChildAccounts
else:
	AllChildAccountList = [{
		'MgmtAccount' : aws_acct.acct_number,
		'AccountId'    : aws_acct.acct_number,
		'AccountEmail' : 'Child Account',
		'AccountStatus': aws_acct.AccountStatus}]
print(f"Found {len(AllChildAccountList)} accounts to look through")

for i in range(len(AllChildAccountList)):
	if AllChildAccountList[i]['AccountStatus'] == 'ACTIVE':
		print(ERASE_LINE,
		      f"Getting credentials for account {AllChildAccountList[i]['AccountId']} -- {i + 1} of {len(AllChildAccountList)}",
		      end="\r")
		try:
			if pRoleList is None:
				credentials = Inventory_Modules.get_child_access3(aws_acct,
				                                                  AllChildAccountList[i]['AccountId'])
			else:
				credentials = Inventory_Modules.get_child_access3(aws_acct,
				                                                  AllChildAccountList[i]['AccountId'], 'us-east-1',
				                                                  pRoleList)
			logging.info(f"Successfully got credentials for account {AllChildAccountList[i]['AccountId']}")
			AllChildAccountList[i]['AccessKeyId'] = credentials['AccessKeyId']
			AllChildAccountList[i]['SecretAccessKey'] = credentials['SecretAccessKey']
			AllChildAccountList[i]['SessionToken'] = credentials['SessionToken']
		except Exception as e:
			print(str(e))
			print(
					f"Failed using root account {AllChildAccountList[i]['MgmtAccount']} to get credentials for acct {AllChildAccountList[i]['AccountId']}")
	else:
		print(ERASE_LINE,
		      f"Skipping account {AllChildAccountList[i]['AccountId']} since it's SUSPENDED or CLOSED    {i + 1} of {len(AllChildAccountList)}",
		      end="\r")

print()
fmt = '%-20s %-15s %-20s %-15s'
print(fmt % ("Root Acct", "Account", "Was Block Enabled?", "Blocked Now?"))
print(fmt % ("---------", "-------", "------------------", "------------"))

print()
NotEnabledList = []
BlockEnabledList = []
for item in AllChildAccountList:
	if item['AccountStatus'].upper() == 'SUSPENDED':
		continue
	else:
		try:
			Updated = "Skipped"
			Enabled = check_block_s3_public_access(item)
			logging.info(f"Checking account #{item['AccountId']} with Parent Account {item['MgmtAccount']}")
			if not Enabled:
				NotEnabledList.append(item['AccountId'])
				if pDryRun:
					Updated = "DryRun"
					pass
				else:
					response = enable_block_s3_public_access(item)
					Updated = response['Status']
					NotEnabledList.remove(item['AccountId'])
					BlockEnabledList.append(item['AccountId'])
			print(fmt % (item['MgmtAccount'], item['AccountId'], Enabled, Updated))
		except ProfileNotFound as myError:
			logging.info(f"You've tried to update your own management account.")

print()
if pFile is not None:
	print(f"# of account in file provided: {len(AccountList)}")
print(f"# of Checked Accounts: {len(AllChildAccountList)}")
for account in NotEnabledList:
	print(f"{Fore.RED}Account {account} needs the S3 public block to be enabled{Fore.RESET}")
print()
for account in BlockEnabledList:
	print(f"{Fore.GREEN}Account {account} has had the S3 public block enabled{Fore.RESET}")
print()
print("Thank you for using this script.")
print()
