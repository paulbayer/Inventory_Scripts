#!/usr/local/bin/python3

import os, sys, pprint, logging
import argparse
import boto3
import Inventory_Modules

from botocore.exceptions import ClientError, NoCredentialsError, InvalidConfigError
from colorama import init,Fore,Back,Style

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all accounts within any of the organizations we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="Profile",
	default="all",
	help="Which single profile do you want to run for?")
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const",
	dest="loglevel",
	const=logging.INFO,
    default=logging.CRITICAL)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.WARNING)
args=parser.parse_args()

pProfile=args.pProfile
verbose=args.loglevel
logging.basicConfig(level=args.loglevel)

SkipProfiles=["default","Shared-Fid"]

RootAccts=[]	# List of the Organization Root's Account Number
RootProfiles=[]	# List of the Organization Root's profiles

if pProfile=="all":
	logging.warning("Profile is set to all")
	ShowEverything=True
else:
	logging.warning("Profile is set to %s",pProfile)
	AcctNum = Inventory_Modules.find_account_number(pProfile)
	AcctAttr = Inventory_Modules.find_org_attr(pProfile)
	MasterAcct = AcctAttr['MasterAccountId']
	OrgId = AcctAttr['Id']
	if AcctNum==MasterAcct:
		logging.warning("This is a root account - showing info only for %s",pProfile)
		RootAcct=True
		ShowEverything=False
	else:
		print()
		print(Fore.RED + "If you're going to provide a profile, it's supposed to be a Master Billing Account profile!!" + Fore.RESET)
		print("Continuing to run the script - but for all profiles.")
		ShowEverything=True

if ShowEverything:
	fmt='%-23s %-15s %-27s %-12s %-10s'
	print ("------------------------------------")
	print (fmt % ("Profile Name","Account Number","Master Org Acct","Org ID","Root Acct?"))
	print (fmt % ("------------","--------------","---------------","------","----------"))
	for profile in Inventory_Modules.get_profiles(SkipProfiles,"all"):
		AcctNum = "Blank Acct"
		MasterAcct = "Blank Root"
		OrgId = "o-xxxxxxxxxx"
		Email = "Email not available"
		RootId = "r-xxxx"
		ErrorFlag = False
		try:
			AcctNum = Inventory_Modules.find_account_number(profile)
			AcctAttr = Inventory_Modules.find_org_attr(profile)
			MasterAcct = AcctAttr['MasterAccountId']
			OrgId = AcctAttr['Id']
		except ClientError as my_Error:
			ErrorFlag = True
			if str(my_Error).find("AWSOrganizationsNotInUseException") > 0:
				MasterAcct="Not an Org Account"
			elif str(my_Error).find("AccessDenied") > 0:
				MasterAcct="Acct not auth for Org API."
			elif str(my_Error).find("InvalidClientTokenId") > 0:
				MasterAcct="Credentials Invalid."
			elif str(my_Error).find("ExpiredToken") > 0:
				MasterAcct="Token Expired."
			else:
				print("Client Error")
				print(my_Error)
		except InvalidConfigError as my_Error:
			ErrorFlag = True
			if str(my_Error).find("does not exist") > 0:
				ErrorMessage=str(my_Error)[str(my_Error).find(":"):]
				print(ErrorMessage)
			else:
				print("Credentials Error")
				print(my_Error)

		except NoCredentialsError as my_Error:
			ErrorFlag = True
			if str(my_Error).find("Unable to locate credentials") > 0:
				MasterAcct="This profile doesn't have credentials."
			else:
				print("Credentials Error")
				print(my_Error)
		if (AcctNum==MasterAcct and not ErrorFlag):
			RootAcct=True
			RootAccts.append(MasterAcct)
			RootProfiles.append(profile)
			Email = AcctAttr['MasterAccountEmail']
			logging.info('Email: %s',Email)
		else:
			RootAcct=False

		# If I create a dictionary from the Root Accts and Root Profiles Lists - I can use that to determine which profile belongs to the root user of my (child) account. But this dictionary is only guaranteed to be valid after ALL profiles have been checked, so... it doesn't solve our issue - unless we don't write anything to the screen until *everything* is done, and we keep all output in another dictionary - where we can populate the missing data at the end... but that takes a long time, since nothing would be sent to the screen in the meantime.
		# dictionary.update(dict(zip(RootAccts, RootProfiles)))

	#	 Print results for this profile
		if RootAcct:
			print (Fore.RED + fmt % (profile,AcctNum,MasterAcct,OrgId,RootAcct)+Style.RESET_ALL)
		else:
			print (fmt % (profile,AcctNum,MasterAcct,OrgId,RootAcct))

	print ("-------------------")

	fmt='%-23s %-15s %-6s'
	child_fmt="\t\t%-20s %-20s"
	print()
	print(fmt % ("Organization's Profile","Root Account","ALZ"))
	print(fmt % ("----------------------","------------","---"))
	NumOfAccounts=0

	for profile in RootProfiles:
		child_accounts={}
		MasterAcct=Inventory_Modules.find_account_number(profile)
		child_accounts=Inventory_Modules.find_child_accounts(profile)
		landing_zone=Inventory_Modules.find_if_lz(profile)
		NumOfAccounts=NumOfAccounts + len(child_accounts)
		if landing_zone:
			fmt='%-23s '+Style.BRIGHT+'%-15s '+Style.RESET_ALL+Fore.RED+'%-6s '+Fore.RESET
		else:
			fmt='%-23s '+Style.BRIGHT+'%-15s '+Style.RESET_ALL+'%-6s'
		print(fmt % (profile,MasterAcct,landing_zone))
		print(child_fmt % ("Child Account Number","Child Email Address"))
		for account in sorted(child_accounts):
			print(child_fmt % (account,child_accounts[account]))
	print()
	print("Number of Organizations:",len(RootProfiles))
	print("Number of Organization Accounts:",NumOfAccounts)
elif not ShowEverything:
	fmt='%-23s %-15s %-6s'
	child_fmt="\t\t%-20s %-20s"
	print()
	print(fmt % ("Organization's Profile","Root Account","ALZ"))
	print(fmt % ("----------------------","------------","---"))
	NumOfAccounts=0

	child_accounts={}
	MasterAcct=Inventory_Modules.find_account_number(pProfile)
	child_accounts=Inventory_Modules.find_child_accounts(pProfile)
	landing_zone=Inventory_Modules.find_if_lz(pProfile)
	NumOfAccounts=NumOfAccounts + len(child_accounts)
	if landing_zone:
		fmt='%-23s '+Style.BRIGHT+'%-15s '+Style.RESET_ALL+Fore.RED+'%-6s '+Fore.RESET
	else:
		fmt='%-23s '+Style.BRIGHT+'%-15s '+Style.RESET_ALL+'%-6s'
	print(fmt % (pProfile,MasterAcct,landing_zone))
	print(child_fmt % ("Child Account Number","Child Email Address"))
	for account in sorted(child_accounts):
		print(child_fmt % (account,child_accounts[account]))
	print()
	print("Number of Organization Accounts:",NumOfAccounts)
