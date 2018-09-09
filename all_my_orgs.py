#!/usr/local/bin/python3

#import os, sys
import argparse
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from colorama import init,Fore,Back,Style

init()

UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(description="We\'re going to find all accounts within any of the organizations we have access to.",prefix_chars='-+/')
parser.add_argument("-c","--creds", dest="plevel", metavar="Creds", default="1", help="Which credentials file to use for investigation.")

args=parser.parse_args()

# If plevel
	# 1: credentials file only
	# 2: config file only
	# 3: credentials and config files
plevel=args.plevel

def find_org_root(fProfile):

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_organization()
	root_org=response['Organization']['MasterAccountId']
	return (root_org)

def find_acct_email(fProfile,fAccount):

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_account(AccountId=fAccount)
	email_addr=response['Account']['Email']
	return (email_addr)

def find_child_accounts(fProfile):

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.list_accounts()
	for account in response['Accounts']:
		child_accounts.append(account['Id'])
	return (child_accounts)

def find_account_number(fProfile):

	session_sts = boto3.Session(profile_name=fProfile)
	client_sts = session_sts.client('sts')
	response=client_sts.get_caller_identity()
	acct_num=response['Account']
	return (acct_num)

def get_profiles(flevel):
	# If flevel
	# 1: credentials file only
	# 2: config file only
	# 3: credentials and config files
	from pathlib import Path
	home = str(Path.home())

	profiles = []

	if flevel == "3":	# Credentials and Config file
		with open(home+"/.aws/credentials","r") as creds_file:
			cred_data = creds_file.readlines()

		for line in cred_data:
			if ("[" in line and not line[0] == "#"):
				profile = (line[1:-2])
				# print (profile)
				profiles.append(profile)

		with open(home+"/.aws/config","r") as config_file:
			conf_data = config_file.readlines()

		for line in conf_data:
			if ("[profile" in line and not line[0] == "#"):
				profile = (line[9:-2])
				# print (profile)
				profiles.append(profile)

	elif flevel == "2": # Config file only
		with open(home+"/.aws/config","r") as config_file:
			conf_data = config_file.readlines()

		for line in conf_data:
			if ("[profile" in line and not line[0] == "#"):
				profile = (line[9:-2])
				# print (profile)
				profiles.append(profile)

	else: # Credentials file only
		with open(home+"/.aws/credentials","r") as creds_file:
			cred_data = creds_file.readlines()

		for line in cred_data:
			if ("[" in line and not line[0] == "#"):
				profile = (line[1:-2])
				# print (profile)
				profiles.append(profile)

	return(profiles)

fmt='%-20s %-20s %-30s %-35s %-10s'
print ("------------------------------------")
print (fmt % ("Profile Name","Account Number","Master Org Acct","Email","Root Acct?"))
print (fmt % ("------------","--------------","---------------","-----","----------"))

RootAccts=[]	# List of the Organization Root's Account Number
RootProfiles=[]	# List of the Organization Root's profiles
for profile in get_profiles(plevel):
	AcctNum = "Blank Acct"
	MasterAcct = "Blank Root"
	Email = "Email not available"
	ErrorFlag = False
	try:
		AcctNum = find_account_number(profile)
		MasterAcct = find_org_root(profile)
		Email = find_acct_email(profile,AcctNum)
	except ClientError as my_Error:
		ErrorFlag = True
		if str(my_Error).find("AWSOrganizationsNotInUseException") > 0:
			MasterAcct="Not an Org Account"
		elif str(my_Error).find("AccessDenied") > 0:
			MasterAcct="Acct not auth for Org API."
		else:
			print(my_Error)
	except NoCredentialsError as my_Error:
		ErrorFlag = True
		if str(my_Error).find("Unable to locate credentials") > 0:
			MasterAcct="This profile doesn't have credentials."
		else:
			print(my_Error)

	if (AcctNum==MasterAcct and not ErrorFlag):
		RootAcct=True
		RootAccts.append(MasterAcct)
		RootProfiles.append(profile)
	else:
		RootAcct=False

# Print results for this profile
	if RootAcct:
		print (Fore.RED + fmt % (profile,AcctNum,MasterAcct,Email,RootAcct)+Style.RESET_ALL)
	else:
		print (fmt % (profile,AcctNum,MasterAcct,Email,RootAcct))

print ("-------------------")

# print("Root Accounts found:",set(RootAccts))
# print("Root Profiles found:",set(RootProfiles))

fmt='%-25s'+ Style.BRIGHT +'%-15s'+ Style.RESET_ALL +'%-40s'
print()
print(fmt % ("Organization's Profile","Root Account","Set of Organization Accounts"))
print(fmt % ("----------------------","------------","----------------------------"))
for profile in RootProfiles:
	child_accounts=[]
	MasterAcct=find_org_root(profile)
	child_accounts=find_child_accounts(profile)
	print(fmt % (profile,MasterAcct,child_accounts))
