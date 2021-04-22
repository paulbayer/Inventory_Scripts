#!/user/bin/env python3
import sys

import Inventory_Modules
import argparse, boto3
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError

import logging

init()

parser = argparse.ArgumentParser(
	description="This script finds vpcs (or only default vpcs) in all accounts within our Organization.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	default=None,
	help="Preferred to specify a root profile. Default will be all Master profiles")
parser.add_argument(
	"-f","--file",
	dest="pFile",
	metavar="file of account numbers to read",
	default=None,
	help="File should consist of account numbers - 1 per line, with CR/LF as line ending")
parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 10
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING, # args.loglevel = 30
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR, # args.loglevel = 40
	default=logging.CRITICAL) # args.loglevel = 50
args = parser.parse_args()

pProfile=args.pProfile
pFile=args.pFile
verbose=args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")


'''
Code Flow:

1. Find the accounts we're going to work on
	- This might be from reading in a file, or might be from interrogating the provided organization
		- How will that org be provided? Default profile? provided profile?

2. Make sure we know the Root account for every child account, and then create a dictionary of access credentials to get into that account
	- So how to find out how to access a child account? Determine profiles you have and then try each Master prpfile?
	
3. Ensure that Public Access Block is enabled on every account 
	- Maybe we check to see if it's already enabled and don't *re-enable* it?
	TODO: Maybe we find if the bucket is hosting a website, and then don't enable it on those buckets?
4. Report that we did what we were supposed to do, and any difficulties we had doing it.  
'''

##########################
def ReadFile(filename):
	account_list=[]
	with open(filename, 'r') as f:
		line = f.readline().rstrip()
		while line:
			account_list.append(line)
			line = f.readline().rstrip()
	return(account_list)

def get_root_profiles():
	RootProfiles=[]
	AllProfiles=Inventory_Modules.get_profiles2()
	try:
		for profile in AllProfiles:
			response=Inventory_Modules.find_if_org_root(profile)
			if response == 'Root':
				RootProfiles.append(profile)
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print("Authorization Failure for profile {}".format(profile))
			print(my_Error)
		elif str(my_Error).find("AccessDenied") > 0:
			print("Access Denied Failure for profile {}".format(profile))
			print(my_Error)
		else:
			print("Other kind of failure for profile {}".format(profile))
			print (my_Error)
	return(RootProfiles)

def find_all_accounts(fRootProfiles):
	AllChildAccounts=[]
	for profile in fRootProfiles:
		ChildAccounts=Inventory_Modules.find_child_accounts2(profile)
		AllChildAccounts.extend(ChildAccounts)
	return(AllChildAccounts)

def check_block_s3_public_access(AcctDict=None):
	if AcctDict == None:
		logging.info("The Account info wasn't passed into the function")
		pass
	else:
		aws_session = boto3.Session(aws_access_key_id=AcctDict['AccessKeyId'],
		                            aws_secret_access_key=AcctDict['SecretAccessKey'],
		                            aws_session_token=AcctDict['SessionToken'],
		                            region_name='us-east-1')
		s3_client = aws_session.client('s3control')
		logging.info("Checking the public access block on account {}".format(AcctDict['AccountId']))
		try:
			response = s3_client.get_public_access_block(
			AccountId=AcctDict['AccountId']
			)['PublicAccessBlockConfiguration']
		except ClientError as my_Error:
			if my_Error.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
				logging.error('No Public Access')
				return(False)
			else:
				logging.error("unexpected error: %s" % (my_Error.response))
				logging.info(my_Error)
				return(False)
		if response['BlockPublicAcls'] and response['IgnorePublicAcls'] and response['BlockPublicPolicy'] and response['RestrictPublicBuckets']:
			return(True)
		else:
			return(False)

def enable_block_s3_public_access(AcctDict=None):
	if AcctDict==None:
		logging.info("The Account info wasn't passed into the function")
		return("Skipped")
	else:
		aws_session=boto3.Session(aws_access_key_id=AcctDict['AccessKeyId'],
		                          aws_secret_access_key=AcctDict['SecretAccessKey'],
		                          aws_session_token=AcctDict['SessionToken'],
		                          region_name='us-east-1')
		s3_client=aws_session.client('s3control')
		logging.info("Enabling the public access block".format(AcctDict['AccountId']))
		response=s3_client.put_public_access_block(
			PublicAccessBlockConfiguration={
				'BlockPublicAcls': True,
				'IgnorePublicAcls': True,
				'BlockPublicPolicy': True,
				'RestrictPublicBuckets': True
			},
			AccountId=AcctDict['AccountId']
	)
	return("Updated")

##########################
ERASE_LINE = '\x1b[2K'

# Get the accounts we're going to work on
AccountList=ReadFile(pFile)

if pProfile==None:
	# Establish a dictionary of Root Accounts and get credentials for all accounts under the root
	RootProfiles=get_root_profiles()
else:
	# If a profile was provided, limit the work to just that profile
	RootProfiles=[pProfile]
AllChildAccountList=find_all_accounts(RootProfiles)
for i in range(len(AllChildAccountList)):
	if AllChildAccountList[i]['AccountStatus'] == 'ACTIVE':
		# if AllChildAccountList[i]['AccountStatus'] == 'ACTIVE' and AllChildAccountList[i]['AccountId'] in AccountList:
		print(ERASE_LINE,"Getting credentials for account {}".format(AllChildAccountList[i]['AccountId']),end="\r")
		try:
			credentials,role = Inventory_Modules.get_child_access2(AllChildAccountList[i]['ParentProfile'],AllChildAccountList[i]['AccountId'])
			logging.info("Successfully got credentials for account {}".format(AllChildAccountList[i]['AccountId']))
			AllChildAccountList[i]['AccessKeyId'] = credentials['AccessKeyId']
			AllChildAccountList[i]['SecretAccessKey'] = credentials['SecretAccessKey']
			AllChildAccountList[i]['SessionToken'] = credentials['SessionToken']
			AccountList.remove(AllChildAccountList[i]['AccountId'])
		except:
			print("Failed using root profile {} to get credentials for acct {}".format(AllChildAccountList[i]['ParentProfile'],AllChildAccountList[i]['AccountId']))

print()
fmt='%-20s %-15s %-20s %-15s'
print(fmt % ("Root Acct","Account","Was Block Enabled?","Blocked Now?"))
print(fmt % ("---------","-------","------------------","------------"))

print()
for item in AllChildAccountList:
	# print(ERASE_LINE, "Checking S3 public block for account {}".format(AllChildAccountList[i]['AccountId']), end="\r")
	if item['AccountStatus']=='SUSPENDED':
		continue
	else:
		Updated="Skipped"
		Enabled=check_block_s3_public_access(item)
		logging.info("Checking account #{} with Parent Profile {}".format(item['AccountId'],item['ParentProfile']))
		if not Enabled:
			# Updated="DryRun"
			Updated=enable_block_s3_public_access(item)
		print(fmt % (item['ParentProfile'],item['AccountId'],Enabled,Updated))

print()
print("# of account in file provided: {}".format(len(AccountList)))
print("# of Root Accounts: {}".format(len(RootProfiles)))
print("# of Child Accounts: {}".format(len(AllChildAccountList)))
print()
print("Thank you for using this script.")
