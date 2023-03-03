#!/usr/bin/env python3

import sys
import pprint
import boto3
import Inventory_Modules
from Inventory_Modules import get_credentials_for_accounts_in_org
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError
from queue import Queue
from threading import Thread
from time import time

import logging

init()

"""
TODO:
- Enable the deletion of the config recorders / delivery channels from specific accounts (or all?) at the end.
"""
parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()  # This adds additional *optional* arguments to the listing
parser.rootOnly()
parser.verbosity()
parser.my_parser.add_argument(
		"+delete", "+forreal",
		dest="flagDelete",
		action="store_true",  # If the parameter is supplied, it will be true, otherwise it's false
		help="Whether to delete the configuration recorders and delivery channels it finds.")
parser.my_parser.add_argument(
		"-a", "--account",
		dest="pAccounts",
		default=None,
		nargs="*",
		metavar="Account",
		help="Just the accounts you want to check")
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pAccounts = args.pAccounts
pSkipAccounts = args.SkipAccounts
pRootOnly = args.RootOnly
pTiming = args.Time
verbose = args.loglevel
DeletionRun = args.flagDelete
ForceDelete = args.Force
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")

##########################


def display_found_resources(resources_list):
	"""
	Note that this function simply formats the output of the data within the list provided
	"""
	for found_resource in resources_list:
		print(f"{found_resource['MgmtAccount']:12s} {found_resource['AccountId']:12s} {found_resource['Region']:15s} {found_resource['SubnetName']:40s} {found_resource['CidrBlock']:18s} {found_resource['AvailableIpAddressCount']:5d}")


def check_accounts_for_delivery_channels_and_config_recorders(CredentialList, fRegionList=None, fip=None):
	"""
	Note that this function takes a list of Credentials and checks for config recorder and delivery channel in every account it has creds for
	"""

	class Find_Config_Recorders_and_Delivery_Channels(Thread):

		def __init__(self, queue):
			Thread.__init__(self)
			self.queue = queue

		def run(self):
			while True:
				# Get the work from the queue and expand the tuple
				account_crs_and_dcs = []
				c_account_credentials, c_region, c_fip, c_PlacesToLook, c_PlaceCount = self.queue.get()
				logging.info(f"De-queued info for account {c_account_credentials['AccountId']}")
				try:
					logging.info(f"Attempting to connect to {c_account_credentials['AccountId']}")
					account_dcs = Inventory_Modules.find_delivery_channels2(c_account_credentials, c_region)
					account_crs = Inventory_Modules.find_config_recorders2(c_account_credentials, c_region)
					account_crs_and_dcs.extend(account_crs['ConfigurationRecorders'])
					account_crs_and_dcs.extend(account_dcs['DeliveryChannels'])
					logging.info(f"Successfully connected to account {c_account_credentials['AccountId']}")
					for y in range(len(account_crs_and_dcs['Subnets'])):
						account_crs_and_dcs['Subnets'][y]['MgmtAccount'] = c_account_credentials['MgmtAccount']
						account_crs_and_dcs['Subnets'][y]['AccountId'] = c_account_credentials['AccountId']
						account_crs_and_dcs['Subnets'][y]['Region'] = c_region
						account_crs_and_dcs['Subnets'][y]['SubnetName'] = "None"
						if 'Tags' in account_crs_and_dcs['Subnets'][y].keys():
							for tag in account_crs_and_dcs['Subnets'][y]['Tags']:
								if tag['Key'] == 'Name':
									account_crs_and_dcs['Subnets'][y]['SubnetName'] = tag['Value']
						account_crs_and_dcs['Subnets'][y]['VPCId'] = account_crs_and_dcs['Subnets'][y]['VpcId'] if 'VpcId' in account_crs_and_dcs['Subnets'][y].keys() else None
					if len(account_crs_and_dcs['Subnets']) > 0:
						AllSubnets.extend(account_crs_and_dcs['Subnets'])
				except KeyError as my_Error:
					logging.error(f"Account Access failed - trying to access {c_account_credentials['AccountId']}")
					logging.info(f"Actual Error: {my_Error}")
					pass
				except AttributeError as my_Error:
					logging.error(f"Error: Likely that one of the supplied profiles {pProfiles} was wrong")
					logging.warning(my_Error)
					continue
				finally:
					print(f"{ERASE_LINE}Finished finding subnets in account {c_account_credentials['AccountId']} in region {c_region} - {c_PlaceCount} / {c_PlacesToLook}", end='\r')
					self.queue.task_done()

	AllSubnets = []
	PlaceCount = 0
	PlacesToLook = len(CredentialList) * len(fRegionList)

	if fRegionList is None:
		fRegionList = ['us-east-1']
	checkqueue = Queue()

	for x in range(WorkerThreads):
		worker = Find_Config_Recorders_and_Delivery_Channels(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	for credential in CredentialList:
		logging.info(f"Connecting to account {credential['AccountId']}")
		for region in fRegionList:
			try:
				# print(f"{ERASE_LINE}Queuing account {credential['AccountId']} in region {region}", end='\r')
				checkqueue.put((credential, region, fip, PlacesToLook, PlaceCount))
				PlaceCount += 1
			except ClientError as my_Error:
				if str(my_Error).find("AuthFailure") > 0:
					logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {region} region")
					logging.warning(f"It's possible that the region {region} hasn't been opted-into")
					pass
	checkqueue.join()
	return (AllSubnets)


def delete_config_recorders_and_delivery_channels(all_config_recorders_and_delivery_channels):
	MemberList = []
	logging.warning("Deleting all Config Recorders")
	for y in range(len(all_config_recorders)):
		session_cf_child = boto3.Session(
			aws_access_key_id=all_config_recorders[y]['AccessKeyId'],
			aws_secret_access_key=all_config_recorders[y]['SecretAccessKey'],
			aws_session_token=all_config_recorders[y]['SessionToken'],
			region_name=all_config_recorders[y]['Region'])
		client_cf_child = session_cf_child.client('config')
		# Delete ConfigurationRecorders
		try:
			print(ERASE_LINE,
				  f"Deleting recorder from Account {all_config_recorders[y]['AccountId']} in region {all_config_recorders[y]['Region']}",
				  end="\r")
			Output = client_cf_child.delete_configuration_recorder(
				ConfigurationRecorderName=all_config_recorders[y]['ConfigurationRecorder']
			)
		# pprint.pprint(Output)
		except Exception as e:
			# if e.response['Error']['Code'] == 'BadRequestException':
			# 	logging.warning("Caught exception 'BadRequestException', handling the exception...")
			# 	pass
			# else:
			print("Caught unexpected error regarding deleting config recorders. Exiting...")
			pprint.pprint(e)
			sys.exit(9)
	print(f"Removed {len(all_config_recorders)} config recorders")
	for y in range(len(all_config_delivery_channels)):
		logging.info(f"Deleting delivery channel: {all_config_delivery_channels[y]['DeliveryChannel']} from account "
					 f"{all_config_delivery_channels[y]['AccountId']} in region {all_config_delivery_channels[y]['Region']}")
		print(f"Deleting delivery channel in account {all_config_delivery_channels[y]['AccountId']} in "
			  f"region {all_config_delivery_channels[y]['Region']}", end='\r')
		session_cf_child = boto3.Session(
			aws_access_key_id=all_config_delivery_channels[y]['AccessKeyId'],
			aws_secret_access_key=all_config_delivery_channels[y]['SecretAccessKey'],
			aws_session_token=all_config_delivery_channels[y]['SessionToken'],
			region_name=all_config_delivery_channels[y]['Region'])
		client_cf_child = session_cf_child.client('config')
		# List Members
		Output = client_cf_child.delete_delivery_channel(
			DeliveryChannelName=all_config_delivery_channels[y]['DeliveryChannel']
		)
		logging.warning(
			f"Delivery Channel {str(all_config_delivery_channels[y]['DeliveryChannel'][0])} has been deleted from child account {str(all_config_delivery_channels[y]['AccountId'])} in region {str(all_config_delivery_channels[y]['Region'])}")


##########################
ERASE_LINE = '\x1b[2K'
if pTiming:
	begin_time = time()

NumObjectsFound = 0
NumAccountsInvestigated = 0
AllCredentials = []
# aws_acct = aws_acct_access(pProfiles)

if pProfiles is None:  # Default use case from the classes
	print("Using the default profile - gathering ")
	aws_acct = aws_acct_access()
	RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
	WorkerThreads = len(aws_acct.ChildAccounts)+4
	if pTiming:
		logging.info(f"{Fore.GREEN}Overhead consumed {time() - begin_time} seconds up till now{Fore.RESET}")
	# This should populate the list "AllCreds" with the credentials for the relevant accounts.
	logging.info(f"Queueing default profile for credentials")
	AllCredentials.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly))
else:
	ProfileList = Inventory_Modules.get_profiles(fprofiles=pProfiles)
	print(f"Capturing info for supplied profiles")
	logging.warning(f"These profiles are being checked {ProfileList}.")
	for profile in ProfileList:
		aws_acct = aws_acct_access(profile)
		WorkerThreads = len(aws_acct.ChildAccounts) + 4
		RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
		if pTiming:
			logging.info(f"{Fore.GREEN}Overhead consumed {time() - begin_time} seconds up till now{Fore.RESET}")
		logging.warning(f"Looking at {profile} account now... ")
		logging.info(f"Queueing {profile} for credentials")
		# This should populate the list "AllCreds" with the credentials for the relevant accounts.
		AllCredentials.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly))
#
# if pAccounts is None:
# 	ChildAccounts = aws_acct.ChildAccounts
# else:
# 	ChildAccounts = []
# 	for item in pAccounts:
# 		ChildAccounts.append({'AccountId': item})

ChildAccounts = Inventory_Modules.RemoveCoreAccounts(AllCredentials, pSkipAccounts)

cf_regions = Inventory_Modules.get_service_regions('config', pRegionList)
all_config_recorders = []
all_config_recorders_and_delivery_channels = []
all_config_delivery_channels = []
print(f"Searching {len(ChildAccounts)} accounts and {len(cf_regions)} regions")

sts_client = aws_acct.session.client('sts')
for account in ChildAccounts:
	NumProfilesInvestigated = 0  # I only care about the last run - so I don't get profiles * regions.
	try:
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, account['AccountId'])
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"Authorization Failure for account {account['AccountId']}")
		continue
	for region in cf_regions:
		NumAccountsInvestigated += 1
		session_aws = boto3.Session(
				aws_access_key_id=account_credentials['AccessKeyId'],
				aws_secret_access_key=account_credentials['SecretAccessKey'],
				aws_session_token=account_credentials['SessionToken'],
				region_name=region)
		client_aws = session_aws.client('config')
		# List Configuration_Recorders
		try:  # Looking for Configuration Recorders
			print(ERASE_LINE, f"Trying account {account['AccountId']} in region {region}", end='\r')
			response = client_aws.describe_configuration_recorders()
			logging.error("Successfully described config recorders")
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"Authorization Failure for account {account['AccountId']}")
			response = {}
		if 'ConfigurationRecorders' in response.keys():
			for i in range(len(response['ConfigurationRecorders'])):
				NumObjectsFound = NumObjectsFound + len(response['ConfigurationRecorders'])
				all_config_recorders.append({
					'AccountId'            : account['AccountId'],
					'ConfigurationRecorder': response['ConfigurationRecorders'][i]['name'],
					'Region'               : region,
					'AccessKeyId'          : account_credentials['AccessKeyId'],
					'SecretAccessKey'      : account_credentials['SecretAccessKey'],
					'SessionToken'         : account_credentials['SessionToken']
					})
				print(
						"Found another config recorder {} in account {} in region {} bringing the total found to {} ".format(
								str(response['ConfigurationRecorders'][i]['name']), account['AccountId'], region,
								str(NumObjectsFound)))
		try:  # Looking for Delivery Channels
			print(ERASE_LINE, f"Trying account {account['AccountId']} in region {region}", end='\r')
			response = client_aws.describe_delivery_channels()
			if len(response['DeliveryChannels']) > 0 and response['DeliveryChannels'][0]['name'][
			                                             -13:] != "DO-NOT-DELETE":
				NumObjectsFound = NumObjectsFound + len(response['DeliveryChannels'])
				all_config_delivery_channels.append({
					'AccountId'      : account['AccountId'],
					'Region'         : region,
					'DeliveryChannel': response['DeliveryChannels'][0]['name'],
					'AccessKeyId'    : account_credentials['AccessKeyId'],
					'SecretAccessKey': account_credentials['SecretAccessKey'],
					'SessionToken'   : account_credentials['SessionToken']
					})
				print(
						"Found another delivery_channel {} in account {} in region {} bringing the total found to {} ".format(
								str(response['DeliveryChannels'][0]['name']), account['AccountId'], region,
								str(NumObjectsFound)))
			# logging.info("Found another detector ("+str(response['DeliveryChannels'][0])+") in account "+account['AccountId']+" in region "+account['AccountId']+" bringing the total found to "+str(NumObjectsFound))
			else:
				print(ERASE_LINE,
				      f"{Fore.RED}No luck in account: {account['AccountId']} in region {region}{Fore.RESET}", end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"Authorization Failure for account {account['AccountId']}")

if args.loglevel < 50:
	print()
	fmt = '%-20s %-15s %-20s'
	print(fmt % ("Account ID", "Region", "Delivery Channel"))
	print(fmt % ("----------", "------", "----------------"))
	for i in range(len(all_config_delivery_channels)):
		print(fmt % (all_config_delivery_channels[i]['AccountId'], all_config_delivery_channels[i]['Region'],
		             all_config_delivery_channels[i]['DeliveryChannel']))

print(ERASE_LINE)
print("We scanned {} accounts and {} regions totalling {} possible areas for resources.".format(len(ChildAccounts),
                                                                                                len(cf_regions),
                                                                                                len(ChildAccounts) * len(
		                                                                                                cf_regions)))
print("Found {} Configuration Recorders across {} accounts across {} regions".format(len(all_config_recorders),
                                                                                     len(ChildAccounts),
                                                                                     len(cf_regions)))
print("Found {} Delivery Channels across {} profiles across {} regions".format(len(all_config_delivery_channels),
                                                                               len(ChildAccounts), len(cf_regions)))
print()

if DeletionRun and not ForceDelete:
	ReallyDelete = (input(
			"Deletion of Config Recorders and Delivery Channels has been requested. Are you still sure? (y/n): ") == 'y')
else:
	ReallyDelete = False

if DeletionRun and (ReallyDelete or ForceDelete):
	MemberList = []
	logging.warning("Deleting all Config Recorders")
	for y in range(len(all_config_recorders)):
		session_cf_child = boto3.Session(
				aws_access_key_id=all_config_recorders[y]['AccessKeyId'],
				aws_secret_access_key=all_config_recorders[y]['SecretAccessKey'],
				aws_session_token=all_config_recorders[y]['SessionToken'],
				region_name=all_config_recorders[y]['Region'])
		client_cf_child = session_cf_child.client('config')
		# Delete ConfigurationRecorders
		try:
			print(ERASE_LINE,
			      f"Deleting recorder from Account {all_config_recorders[y]['AccountId']} in region {all_config_recorders[y]['Region']}",
			      end="\r")
			Output = client_cf_child.delete_configuration_recorder(
					ConfigurationRecorderName=all_config_recorders[y]['ConfigurationRecorder']
					)
		# pprint.pprint(Output)
		except Exception as e:
			# if e.response['Error']['Code'] == 'BadRequestException':
			# 	logging.warning("Caught exception 'BadRequestException', handling the exception...")
			# 	pass
			# else:
			print("Caught unexpected error regarding deleting config recorders. Exiting...")
			pprint.pprint(e)
			sys.exit(9)
	print(f"Removed {len(all_config_recorders)} config recorders")
	for y in range(len(all_config_delivery_channels)):
		logging.info(f"Deleting delivery channel: {all_config_delivery_channels[y]['DeliveryChannel']} from account "
		             f"{all_config_delivery_channels[y]['AccountId']} in region {all_config_delivery_channels[y]['Region']}")
		print(f"Deleting delivery channel in account {all_config_delivery_channels[y]['AccountId']} in "
		      f"region {all_config_delivery_channels[y]['Region']}", end='\r')
		session_cf_child = boto3.Session(
				aws_access_key_id=all_config_delivery_channels[y]['AccessKeyId'],
				aws_secret_access_key=all_config_delivery_channels[y]['SecretAccessKey'],
				aws_session_token=all_config_delivery_channels[y]['SessionToken'],
				region_name=all_config_delivery_channels[y]['Region'])
		client_cf_child = session_cf_child.client('config')
		# List Members
		Output = client_cf_child.delete_delivery_channel(
				DeliveryChannelName=all_config_delivery_channels[y]['DeliveryChannel']
				)
		logging.warning(
				f"Delivery Channel {str(all_config_delivery_channels[y]['DeliveryChannel'][0])} has been deleted from child account {str(all_config_delivery_channels[y]['AccountId'])} in region {str(all_config_delivery_channels[y]['Region'])}")

if pTiming:
	end_time = time()
	duration = end_time - begin_time
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {duration} seconds{Fore.RESET}")
print()
print("Thank you for using this tool")
