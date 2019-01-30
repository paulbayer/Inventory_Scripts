#!/usr/local/bin/python3

import os, sys, pprint
import Inventory_Modules, boto3
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from urllib3.exceptions import NewConnectionError

import logging

init()

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	help="You need to specify a profile that represents the ROOT account.")
parser.add_argument(
	"+delete", "+forreal",
	dest="flagDelete",
	default=False,
	action="store_const",
	const=True,
	help="Whether to delete the detectors it finds.")
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
pProfile=args.pProfile
DeletionRun=args.flagDelete
logging.basicConfig(level=args.loglevel)

##########################
ERASE_LINE = '\x1b[2K'

NumObjectsFound = 0
NumAccountsInvestigated = 0

# try:
ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
# except:

session_gd=boto3.Session(profile_name=pProfile)
gd_regions=session_gd.get_available_regions(service_name='guardduty')

all_gd_detectors=[]
print("Searching {} profiles and {} regions".format(len(ChildAccounts),len(gd_regions)))

sts_session = boto3.Session(profile_name=pProfile)
for region in gd_regions:
	NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for account in ChildAccounts:
		NumAccountsInvestigated += 1
		try:
			sts_client = sts_session.client('sts',region_name=region)
			role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(account['AccountId'])
			account_credentials = sts_client.assume_role(
				RoleArn=role_arn,
				RoleSessionName="Find-GuardDuty-Detectors")['Credentials']
			session_aws=boto3.Session(
				aws_access_key_id=account_credentials['AccessKeyId'],
				aws_secret_access_key=account_credentials['SecretAccessKey'],
				aws_session_token=account_credentials['SessionToken'],
				region_name=region)
			client_aws=session_aws.client('guardduty')
			# logging.warning("Command to be run: %s on account: %s" % (command_to_run,account['AccountId']))
			response=client_aws.list_detectors()
			if len(response['DetectorIds']) > 0:
				NumObjectsFound=NumObjectsFound + len(response['DetectorIds'])
				all_gd_detectors.append({
					'AccountId':account['AccountId'],
					'Region':region,
					'DetectorIds':response['DetectorIds'],
					'AccessKeyId':account_credentials['AccessKeyId'],
					'SecretAccessKey':account_credentials['SecretAccessKey'],
					'SessionToken':account_credentials['SessionToken']
				})
				print("Found another detector in account {} in region {} bringing the total found to {}".format(account['AccountId'],region,NumObjectsFound))
			else:
				print(ERASE_LINE,"No luck in account: {} in region: {}".format(account['AccountId'],region),end='\r')

		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure")

if args.loglevel < 50:
	print()
	fmt='%-20s %-15s %-20s'
	print(fmt % ("Account ID","Region","Detector ID"))
	print(fmt % ("----------","------","-----------"))
	for i in range(len(all_gd_detectors)):
		print(fmt % (all_gd_detectors[i]['AccountId'],all_gd_detectors[i]['Region'],all_gd_detectors[i]['DetectorIds']))

print()
print("Found {} Detectors across {} profiles across {} regions".format(NumObjectsFound,len(ChildAccounts),len(gd_regions)))
print()

if DeletionRun and (input ("Deletion of Guard Duty detectors has been requested. Are you still sure? (y/n): ") == 'y'):
	for y in range(len(all_gd_detectors)):
		logging.info("Deleting detector-id: %s from account %s in region %s" % (all_gd_detectors[y]['DetectorsIds'],all_gd_detectors[y][''],all_gd_detectors[y][2]))
		print("Deleting in profile {} in region {}".format(all_gd_detectors[y][0],all_gd_detectors[y][1]))
		# Output=
