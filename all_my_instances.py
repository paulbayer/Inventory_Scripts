#!/usr/bin/env python3

import os
import sys
import boto3
import Inventory_Modules
import argparse
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	default=None,
	help="To specify a specific profile, use this parameter. Default will be to use Environment Variables, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-r", "--region",
	nargs="*",
	dest="pRegion",
	metavar="region name string",
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
	'-d', '--debug',
	help="Print debugging statements - only for developers",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,        # args.loglevel = 10
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print info statements - mainly for developers",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,         # args.loglevel = 20
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-vv',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,      # args.loglevel = 30
	default=logging.CRITICAL)   # args.loglevel = 50
parser.add_argument(
	'-v', '--verbose',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,        # args.loglevel = 40
	default=logging.CRITICAL)   # args.loglevel = 50
args = parser.parse_args()

pProfile = args.pProfile
pRegionList = args.pRegion
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

EnvVars = {'Profile': os.getenv('AWS_PROFILE'),
          'AccessKey': os.getenv('AWS_ACCESS_KEY_ID'),
          'SecretKey': os.getenv('AWS_SECRET_ACCESS_KEY'),
          'SessionToken': os.getenv('AWS_SESSION_TOKEN'),
          'DefaultRegion': os.getenv('AWS_DEFAULT_REGION')}
# Get environment variables

logging.warning("EnvVars: %s" % str(EnvVars))
account_credentials = {'Profile': None,
                      'AccessKeyId': None,
                      'SecretAccessKey': None,
                      'SessionToken': None,
                      'AccountNumber': None}

'''
Possible Use Cases:

User supplies a profile that represents: 
	1) an IAM user (This is a persistent session, using key and secret)
	2) an IAM role
	3) an IAM role authenticated via another account (This would be using a a session token)

User supplies persistent credentials (Access_Key and Secret_Key)
	1) If there's no Session Token, one could be created via an STS call

User supplies ephemeral credentials (Access_Key, Secret_Key and Session Token)
	1) Since there's a session token, we can simply use that 
'''

ProfileSupplied = False
# They provided a profile (or more than one) at the command line
if pProfile is not None:
	logging.error("Using the provided profile from the command line")
	SessionToken = False
	ProfileSupplied = True
	pass
# They didn't provide a profile parameter
elif pProfile is None:
	# They provided the profile name in the Environment Variables
	if EnvVars['Profile'] is not None:
		pProfile = EnvVars['Profile']
		SessionToken = False
		ProfileSupplied = True
		logging.error("Using profile from env vars: %s", pProfile)
	# They provided the Persistent Access Key and Secret in the Environment Variables
	elif EnvVars['AccessKey'] is not None and EnvVars['SessionToken'] is None:
		pProfile = EnvVars['Profile']
		SessionToken = False
		ProfileSupplied = False
		account_credentials['AccessKeyId'] = EnvVars['AccessKey']
		account_credentials['SecretAccessKey'] = EnvVars['SecretKey']
		logging.error("Using provided access key: %s", pProfile)
	# They provided the ephemeral Access Key and Token in the Environment Variables
	elif EnvVars['AccessKey'] is not None and EnvVars['SessionToken'] is not None:
		pProfile = EnvVars['Profile']
		SessionToken = True
		ProfileSupplied = False
		account_credentials['AccessKeyId'] = EnvVars['AccessKey']
		account_credentials['SecretAccessKey'] = EnvVars['SecretKey']
		account_credentials['SessionToken'] = EnvVars['SessionToken']
		logging.error("Using provided access key with a session token: %s", pProfile)
# They provided no credentials at all
else:
	ProfileSupplied = False
	print("No authentication mechanisms left!")
	sys.exit("No authentication mechanisms left")
##########################


ERASE_LINE = '\x1b[2K'

NumInstancesFound = 0
print()
if ProfileSupplied:
	fmt = '%-12s %-15s %-10s %-15s %-25s %-20s %-42s %-12s'
	print(fmt % ("Profile", "Account #", "Region", "InstanceType", "Name", "Instance ID", "Public DNS Name", "State"))
	print(fmt % ("-------", "---------", "------", "------------", "----", "-----------", "---------------", "-----"))
elif not ProfileSupplied:
	fmt = '%-15s %-10s %-15s %-25s %-20s %-42s %-12s'
	print(fmt % ("Account #", "Region", "InstanceType", "Name", "Instance ID", "Public DNS Name", "State"))
	print(fmt % ("---------", "------", "------------", "----", "-----------", "---------------", "-----"))

RegionList = Inventory_Modules.get_regions(pRegionList)
AllChildAccounts = []
SoughtAllProfiles = False

ProfileIsRoot = Inventory_Modules.find_if_org_root(pProfile)

if ProfileIsRoot == 'Root':
	logging.info("Profile %s is a Root account", pProfile)
	Creds = Inventory_Modules.find_calling_identity(pProfile)
	AllChildAccounts = Inventory_Modules.find_child_accounts2(pProfile)
elif ProfileIsRoot == 'StandAlone':
	logging.info("Profile %s is a Standalone account", pProfile)
	Creds = Inventory_Modules.find_calling_identity(pProfile)
	AllChildAccounts = [{
		'ParentProfile': pProfile,
		'AccountId': Creds['AccountId'],
		'Arn': Creds['Arn'],
		'AccountStatus': 'ACTIVE',
		'AccountEmail': 'noonecares@doesntmatter.com'}]
	account_credentials['Profile'] = pProfile
elif ProfileIsRoot == 'Child':
	logging.info("Profile %s is a Child Account", pProfile)
	Creds = Inventory_Modules.find_calling_identity(pProfile)
	AllChildAccounts = [{
		'ParentProfile': pProfile,
		'AccountId': Creds['AccountId'],
		'Arn': Creds['Arn'],
		'AccountStatus': 'ACTIVE',
		'AccountEmail': 'noonecares@doesntmatter.com'}]
	account_credentials['Profile'] = pProfile

Instances = {}
# Removing all accounts which are SUSPENDED
for i in reversed(range(len(AllChildAccounts))):
	if AllChildAccounts[i]['AccountStatus'] == 'SUSPENDED':
		del AllChildAccounts[i]
for i in range(len(AllChildAccounts)):
	aws_session = boto3.Session(profile_name=AllChildAccounts[i]['ParentProfile'])
	sts_client = aws_session.client('sts')
	logging.info("Single account record %s:", AllChildAccounts[i])
	# TODO - figure a way to find out whether this rolename is correct for every account?
	role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(AllChildAccounts[i]['AccountId'])
	logging.info("Role ARN: %s" % role_arn)
	try:
		# This is a standalone or child account and the profile provided is all we need
		if len(AllChildAccounts) == 1 and pProfile == AllChildAccounts[i]['ParentProfile']:
			pass    # We've already populated the account_credentials dict above
		# The profile provided is of a root account, which has access to the member accounts via some role
		else:
			account_credentials, _ = Inventory_Modules.get_child_access2(AllChildAccounts[i]['ParentProfile'],
			                                                             AllChildAccounts[i]['AccountId'])
			account_credentials['Profile'] = pProfile
		account_credentials['AccountNumber'] = AllChildAccounts[i]['AccountId']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			logging.error("%s: Authorization Failure for account %s", AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId'])
		elif str(my_Error).find("AccessDenied") > 0:
			logging.error("%s: Access Denied Failure for account %s", AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId'])
			logging.warning(my_Error)
		else:
			logging.error("%s: Other kind of failure for account %s", AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId'])
			logging.warning(my_Error)
		continue
	for pRegion in RegionList:
		try:
			Instances = Inventory_Modules.find_account_instances(account_credentials, pRegion)
			logging.warning("Account %s being looked at now", account_credentials['AccountNumber'])
			InstanceNum = len(Instances['Reservations'])
			print(ERASE_LINE+"Org Profile: {} Account: {} Region: {} Found {} instances".format(AllChildAccounts[i]['ParentProfile'], account_credentials['AccountNumber'], pRegion, InstanceNum), end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error("Authorization Failure using {} parent profile to access {} account in {} region".format(AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId'], pRegion))
				logging.warning("It's possible that the region %s hasn't been opted-into", pRegion)
				pass
		if 'Reservations' in Instances.keys():
			for y in range(len(Instances['Reservations'])):
				for z in range(len(Instances['Reservations'][y]['Instances'])):
					InstanceType = Instances['Reservations'][y]['Instances'][z]['InstanceType']
					InstanceId = Instances['Reservations'][y]['Instances'][z]['InstanceId']
					PublicDnsName = Instances['Reservations'][y]['Instances'][z]['PublicDnsName']
					State = Instances['Reservations'][y]['Instances'][z]['State']['Name']
					# print("Length:", len(Instances['Reservations'][y]['Instances'][z]['Tags']))
					Name = "No Name Tag"
					try:
						for x in range(len(Instances['Reservations'][y]['Instances'][z]['Tags'])):
							if Instances['Reservations'][y]['Instances'][z]['Tags'][x]['Key'] == "Name":
								Name = Instances['Reservations'][y]['Instances'][z]['Tags'][x]['Value']
					except KeyError as my_Error:    # This is needed for when there is no "Tags" key within the describe-instances output
						logging.info(my_Error)
						pass
					if State == 'running':
						fmt = '%-12s %-15s %-10s %-15s %-20s %-20s %-42s '+Fore.RED+'%-12s'+Fore.RESET
					else:
						fmt = '%-12s %-15s %-10s %-15s %-20s %-20s %-42s %-12s'
					print(fmt % (AllChildAccounts[i]['ParentProfile'], account_credentials['AccountNumber'], pRegion, InstanceType, Name, InstanceId, PublicDnsName, State))
					NumInstancesFound += 1
print(ERASE_LINE)
print("Found {} instances across {} profiles across {} regions".format(NumInstancesFound, len(AllChildAccounts), len(RegionList)))
print()
