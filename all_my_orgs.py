#!/usr/local/bin/python3

import os, sys, pprint
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

SkipProfiles=["default","Shared-Fid"]

def find_org_root(fProfile):

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_organization()
	root_org=response['Organization']['MasterAccountId']
	return (root_org)

def find_if_lz(fProfile):

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('ec2')
	response=client_org.describe_vpcs(
		Filters=[
        {
            'Name': 'tag:AWS_Solutions',
            'Values': [
                'LandingZoneStackSet',
            ]
        }
    	]
	)
	for vpc in response['Vpcs']:
		for tag in vpc['Tags']:
			if tag['Key']=="AWS_Solutions":
				return(True)
	return(False)

def find_acct_email(fOrgRootProfile,fAccountId):

	session_org = boto3.Session(profile_name=fOrgRootProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_account(AccountId=fAccountId)
	email_addr=response['Account']['Email']
	return (email_addr)

def find_acct_attr(fProfile):

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_organization()
	root_org=response['Organization']['MasterAccountId']
	org_id=response['Organization']['Id']
	# return {'root_org':root_org,'org_id':org_id}
	return (root_org,org_id)

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

def get_profiles(flevel,fSkipProfiles):
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

	for ProfileToSkip in fSkipProfiles:
		try:
			profiles.remove(ProfileToSkip)
		except:
			pass

	return(profiles)

# landing_zone=find_if_lz("LZRoot")
# pprint.pprint(landing_zone)
# sys.exit(99)

fmt='%-23s %-20s %-30s %-15s %-35s %-10s'
print ("------------------------------------")
print (fmt % ("Profile Name","Account Number","Master Org Acct","Org ID","Email","Root Acct?"))
print (fmt % ("------------","--------------","---------------","------","-----","----------"))

dictionary = dict()
RootAccts=[]	# List of the Organization Root's Account Number
RootProfiles=[]	# List of the Organization Root's profiles
for profile in get_profiles(plevel,SkipProfiles):
	AcctNum = "Blank Acct"
	MasterAcct = "Blank Root"
	OrgId = "o-xxxxxxxxxx"
	Email = "Email not available"
	ErrorFlag = False
	try:
		AcctNum = find_account_number(profile)
		# MasterAcct = find_org_root(profile)
		MasterAcct,OrgId = find_acct_attr(profile)
		# Email = find_acct_email(profile,AcctNum)
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
		Email = find_acct_email(profile,AcctNum)
	else:
		RootAcct=False
		# Email = find_acct_email(profile,AcctNum) ## Need to find a way to get Org Root Profile, when I only know the Org Root Account Number
		# I know it's probably in the List "RootProfiles", but how do I tell which one?

	# If I create a dictionary from the Root Accts and Root Profiles Lists - I can use that to determine which profile belongs to the root user of my (child) account. But this dictionary is only guaranteed to be valid after ALL profiles have been checked, so... it doesn't solve our issue - unless we don't write anything to the screen until *everything* is done, and we keep all output in another dictionary - where we can populate the missing data at the end... but that takes a long time, since nothing would be sent to the screen in the meantime.
	# dictionary.update(dict(zip(RootAccts, RootProfiles)))

# Print results for this profile
	if RootAcct:
		print (Fore.RED + fmt % (profile,AcctNum,MasterAcct,OrgId,Email,RootAcct)+Style.RESET_ALL)
	else:
		print (fmt % (profile,AcctNum,MasterAcct,OrgId,Email,RootAcct))

# print ("-------------------")
# pprint.pprint(dictionary)
print ("-------------------")

fmt='%-23s %-15s %-12s %-40s'
print()
print(fmt % ("Organization's Profile","Root Account","Landing Zone","Set of Organization Accounts"))
print(fmt % ("----------------------","------------","------------","----------------------------"))
for profile in RootProfiles:
	child_accounts=[]
	MasterAcct=find_org_root(profile)
	child_accounts=find_child_accounts(profile)
	landing_zone=find_if_lz(profile)
	if landing_zone:
		fmt='%-23s '+Style.BRIGHT+'%-15s '+Style.RESET_ALL+Fore.RED+'%-12s '+Fore.RESET+'%-40s'
	else:
		fmt='%-23s '+Style.BRIGHT+'%-15s '+Style.RESET_ALL+'%-12s %-40s'
	print(fmt % (profile,MasterAcct,landing_zone,child_accounts))
