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
	help="You need to specify the ROOT account with this profile.")
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

ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
session_gd=boto3.Session(profile_name=pProfile)
gd_regions=session_gd.get_available_regions(service_name='guardduty')

all_gd_detectors=[]
print("Searching {} profiles and {} regions".format(len(ChildAccounts),len(gd_regions)))

print()
fmt='%-20s %-15s %-20s'
print(fmt % ("Account ID","Region","Detector ID"))
print(fmt % ("----------","------","-----------"))

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
				all_gd_detectors.append({'AccountId':account['AccountId'],'Region':region,'DetectorIds':response['DetectorIds']})
				print("Found another detector in account {} in region {} bringing the total found to {}".format(account['AccountId'],region,NumObjectsFound))
			else:
				print(ERASE_LINE,"No luck in account: {} in region: {}".format(account['AccountId'],region),end='\r')

		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure")

for i in range(len(all_gd_detectors)):
	print(fmt % (all_gd_detectors[i]['AccountId'],all_gd_detectors[i]['Region'],all_gd_detectors[i]['DetectorIds']))

'''
			NumObjects=len(Output['DetectorIds'])
			logging.info("Profile: %s | Region: %s | Found %s Items",profile,region,NumObjects)
			print(ERASE_LINE,Fore.RED+"Profile: {} Region: {} Found {} Items".format(profile,region,NumObjects)+Fore.RESET,end='\r')
			if NumObjects == 1:
				DetectorsToDelete.append([profile,region,Output['DetectorIds'][0]])
			elif NumObjects == 0:
				#No Dectors Found
				logging.warning("Profile %s in region %s found no detectors",profile,region)
				continue
			else:
				logging.warning("Profile %s in region %s somehow has more than 1 Detector. Run!!",profile,region)
				break
			"""
			Format of DetectorsToDelete List:
				[0] = Profile name
				[1] = Region name
				[2] = Detector id to be deleted
			"""
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(ERASE_LINE+profile+": Authorization Failure")
		except TypeError as my_Error:
			# print(my_Error)
			pass
		except EndpointConnectionError as my_Error:
			# Can't connect to this particular region's endpoint - which may not exist.
			if str(my_Error).find("Could not connect to the endpoint URL") > 0:
				print(ERASE_LINE+profile+": Endpoint Connection Failure")
		except NewConnectionError as my_Error:
			# Can't connect to this particular region's endpoint - which may not exist.
			if str(my_Error).find("Failed to establish a new connection") > 0:
				print(ERASE_LINE+profile+": Endpoint Connection Failure")
		if len(Output['DetectorIds']) > 0:
			print(fmt % (profile,region,Output['DetectorIds'][0]))
			NumObjectsFound += 1
'''
print()
print("Found {} Detectors across {} profiles across {} regions".format(NumObjectsFound,len(ChildAccounts),len(gd_regions)))
print()
#
# if DeletionRun:
# 	for y in range(len(DetectorsToDelete)):
# 		logging.info("Deleting detector-id: %s from profile %s in region %s" % (DetectorsToDelete[y][0],DetectorsToDelete[y][1],DetectorsToDelete[y][2]))
# 		print("Deleting in profile {} in region {}".format(DetectorsToDelete[y][0],DetectorsToDelete[y][1]))
# 		Output=Inventory_Modules.del_gd_detectors(DetectorsToDelete[y][0],DetectorsToDelete[y][1],DetectorsToDelete[y][2])
