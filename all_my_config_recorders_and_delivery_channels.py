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
pSkipProfiles = args.SkipProfiles
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


def check_accounts_for_delivery_channels_and_config_recorders(CredentialList, fRegionList=None, fFixRun=False):
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
				c_account_credentials, c_fixrun, c_PlacesToLook, c_PlaceCount = self.queue.get()
				logging.info(f"De-queued info for account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']}")
				try:
					logging.info(f"Checking for config recorders and delivery channels in account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']}")
					account_dcs = Inventory_Modules.find_delivery_channels2(c_account_credentials, c_account_credentials['Region'])
					if len(account_dcs['DeliveryChannels']) > 0:
						account_dcs['DeliveryChannels'][0].update({'Type'           : 'Delivery Channel',
																   'AccountId'      : c_account_credentials['AccountNumber'],
																   'AccessKeyId'    : c_account_credentials['AccessKeyId'],
																   'SecretAccessKey': c_account_credentials['SecretAccessKey'],
																   'SessionToken'   : c_account_credentials['SessionToken'],
																   'Region'         : c_account_credentials['Region'],
																   'MgmtAccount'    : c_account_credentials['MgmtAccount'],
																   'ParentProfile'  : c_account_credentials['ParentProfile']})
						account_crs_and_dcs.extend(account_dcs['DeliveryChannels'])
					account_crs = Inventory_Modules.find_config_recorders2(c_account_credentials, c_account_credentials['Region'])
					if len(account_crs['ConfigurationRecorders']) > 0:
						account_crs['ConfigurationRecorders'][0].update({'Type'           : 'Config Recorder',
																		 'AccountId'      : c_account_credentials['AccountNumber'],
																		 'AccessKeyId'    : c_account_credentials['AccessKeyId'],
																		 'SecretAccessKey': c_account_credentials['SecretAccessKey'],
																		 'SessionToken'   : c_account_credentials['SessionToken'],
																		 'Region'         : c_account_credentials['Region'],
																		 'MgmtAccount'    : c_account_credentials['MgmtAccount'],
																		 'ParentProfile'  : c_account_credentials['ParentProfile']})
						account_crs_and_dcs.extend(account_crs['ConfigurationRecorders'])
					logging.info(f"Successfully connected to account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']}")
				except KeyError as my_Error:
					logging.error(f"Account Access failed - trying to access {c_account_credentials['AccountId']} in region {c_account_credentials['Region']}")
					logging.info(f"Actual Error: {my_Error}")
					pass
				except AttributeError as my_Error:
					logging.error(f"Error: Likely that one of the supplied profiles {pProfiles} was wrong")
					logging.warning(my_Error)
					continue
				finally:
					logging.info(f"{ERASE_LINE}Finished finding items in account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']} - {c_PlaceCount} / {c_PlacesToLook}")
					print(".", end='')
					self.queue.task_done()

	account_crs_and_dcs = []
	PlaceCount = 1
	WorkerThreads = min(len(CredentialList), 50)

	if fRegionList is None:
		fRegionList = ['us-east-1']
	checkqueue = Queue()

	for x in range(WorkerThreads):
		worker = Find_Config_Recorders_and_Delivery_Channels(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	# Since the list of credentials (in CredentialList) already includes the regions, I only have to go through this list, and not *per* region.
	for credential in CredentialList:
		logging.info(f"Connecting to account {credential['AccountId']} in region {credential['Region']}")
		try:
			# print(f"{ERASE_LINE}Queuing account {credential['AccountId']} in region {credential['Region']}", end='\r')
			# I don't know why - but double parens are necessary below. If you remove them, only the first parameter is queued.
			checkqueue.put((credential, fFixRun, len(CredentialList), PlaceCount))
			PlaceCount += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
				logging.warning(f"It's possible that the region {credential['Region']} hasn't been opted-into")
				pass
	checkqueue.join()
	return (account_crs_and_dcs)


##########################
ERASE_LINE = '\x1b[2K'
if pTiming:
	begin_time = time()

NumObjectsFound = 0
NumAccountsInvestigated = 0
AllCredentials = []
RegionList = ['us-east-1']

if pProfiles is None:  # Default use case from the classes
	print("Using the default profile - gathering info")
	aws_acct = aws_acct_access()
	RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
	# This should populate the list "AllCreds" with the credentials for the relevant accounts.
	logging.info(f"Queueing default profile for credentials")
	profile = 'default'
	AllCredentials.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, profile, RegionList))
else:
	ProfileList = Inventory_Modules.get_profiles(fSkipProfiles=pSkipProfiles, fprofiles=pProfiles)
	print(f"Capturing info for {len(ProfileList)} requested profiles {ProfileList}")
	for profile in ProfileList:
		aws_acct = aws_acct_access(profile)
		# WorkerThreads = len(aws_acct.ChildAccounts) + 4
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

# ChildAccounts = Inventory_Modules.RemoveCoreAccounts(ChildAccounts, pSkipAccounts)

cf_regions = Inventory_Modules.get_service_regions('config', RegionList)
all_config_recorders = []
all_config_delivery_channels = []
print(f"Searching {len(AllCredentials)} accounts and {len(cf_regions)} regions")
all_config_recorders_and_delivery_channels = check_accounts_for_delivery_channels_and_config_recorders(AllCredentials, cf_regions, DeletionRun)

# sts_client = aws_acct.session.client('sts')
# for account in ChildAccounts:
# 	NumProfilesInvestigated = 0  # I only care about the last run - so I don't get profiles * regions.
# 	try:
# 		account_credentials = Inventory_Modules.get_child_access3(aws_acct, account['AccountId'])
# 	except ClientError as my_Error:
# 		if str(my_Error).find("AuthFailure") > 0:
# 			print(f"Authorization Failure for account {account['AccountId']}")
# 		continue
# 	for region in cf_regions:
# 		NumAccountsInvestigated += 1
# 		session_aws = boto3.Session(
# 				aws_access_key_id=account_credentials['AccessKeyId'],
# 				aws_secret_access_key=account_credentials['SecretAccessKey'],
# 				aws_session_token=account_credentials['SessionToken'],
# 				region_name=region)
# 		client_aws = session_aws.client('config')
# 		# List Configuration_Recorders
# 		try:  # Looking for Configuration Recorders
# 			print(ERASE_LINE, f"Trying account {account['AccountId']} in region {region}", end='\r')
# 			response = client_aws.describe_configuration_recorders()
# 			logging.error("Successfully described config recorders")
# 		except ClientError as my_Error:
# 			if str(my_Error).find("AuthFailure") > 0:
# 				print(f"Authorization Failure for account {account['AccountId']}")
# 			response = {}
# 		if 'ConfigurationRecorders' in response.keys():
# 			for i in range(len(response['ConfigurationRecorders'])):
# 				NumObjectsFound = NumObjectsFound + len(response['ConfigurationRecorders'])
# 				all_config_recorders.append({
# 					'AccountId'            : account['AccountId'],
# 					'ConfigurationRecorder': response['ConfigurationRecorders'][i]['name'],
# 					'Region'               : region,
# 					'AccessKeyId'          : account_credentials['AccessKeyId'],
# 					'SecretAccessKey'      : account_credentials['SecretAccessKey'],
# 					'SessionToken'         : account_credentials['SessionToken']
# 					})
# 				print(
# 						f"Found another config recorder {str(response['ConfigurationRecorders'][i]['name'])} in account {account['AccountId']} in region {region} bringing the total found to {str(NumObjectsFound)} ")
# 		try:  # Looking for Delivery Channels
# 			print(ERASE_LINE, f"Trying account {account['AccountId']} in region {region}", end='\r')
# 			response = client_aws.describe_delivery_channels()
# 			if len(response['DeliveryChannels']) > 0 and response['DeliveryChannels'][0]['name'][
# 			                                             -13:] != "DO-NOT-DELETE":
# 				NumObjectsFound = NumObjectsFound + len(response['DeliveryChannels'])
# 				all_config_delivery_channels.append({
# 					'AccountId'      : account['AccountId'],
# 					'Region'         : region,
# 					'DeliveryChannel': response['DeliveryChannels'][0]['name'],
# 					'AccessKeyId'    : account_credentials['AccessKeyId'],
# 					'SecretAccessKey': account_credentials['SecretAccessKey'],
# 					'SessionToken'   : account_credentials['SessionToken']
# 					})
# 				print(
# 						f"Found another delivery_channel {str(response['DeliveryChannels'][0]['name'])} in account {account['AccountId']} in region {region} bringing the total found to {str(NumObjectsFound)} ")
# 			# logging.info("Found another detector ("+str(response['DeliveryChannels'][0])+") in account "+account['AccountId']+" in region "+account['AccountId']+" bringing the total found to "+str(NumObjectsFound))
# 			else:
# 				print(ERASE_LINE,
# 				      f"{Fore.RED}No luck in account: {account['AccountId']} in region {region}{Fore.RESET}", end='\r')
# 		except ClientError as my_Error:
# 			if str(my_Error).find("AuthFailure") > 0:
# 				print(f"Authorization Failure for account {account['AccountId']}")

if args.loglevel < 50:
	print()
	fmt = '%-24s %-15s %-15s %-15s %-20s %-30s'
	print(fmt % ("Parent Profile", "Mgmt Account", "Account ID", "Region", "Type", "Name"))
	print(fmt % ("--------------", "------------", "----------", "------", "----", "----"))
	all_sorted_config_recorders_and_delivery_channels = sorted(all_config_recorders_and_delivery_channels, key=lambda d: (d['ParentProfile'], d['MgmtAccount'], d['AccountId']))
	for item in all_sorted_config_recorders_and_delivery_channels:
		print(fmt % (item['ParentProfile'],
					 item['MgmtAccount'],
					 item['AccountId'],
					 item['Region'],
					 item['Type'],
					 item['name']))

print(ERASE_LINE)
print(f"We scanned {len(AllCredentials)} accounts and {len(cf_regions)} regions totalling {len(AllCredentials) * len(cf_regions)} possible areas for resources.")
print(f"Found {len(all_config_recorders)} Configuration Recorders across {len(AllCredentials)} accounts across {len(cf_regions)} regions")
print(f"Found {len(all_config_delivery_channels)} Delivery Channels across {len(AllCredentials)} profiles across {len(cf_regions)} regions")
print()

if DeletionRun and not ForceDelete:
	ReallyDelete = (input(
		"Deletion of Config Recorders and Delivery Channels has been requested. Are you still sure? (y/n): ") == 'y')
else:
	ReallyDelete = False

if DeletionRun and (ReallyDelete or ForceDelete):
	MemberList = []
	logging.warning("Deleting all Config Recorders")
	for deletion_item in all_config_recorders_and_delivery_channels:
		session_cf_child = boto3.Session(
			aws_access_key_id=deletion_item['AccessKeyId'],
			aws_secret_access_key=deletion_item['SecretAccessKey'],
			aws_session_token=deletion_item['SessionToken'],
			region_name=deletion_item['Region'])
		client_cf_child = session_cf_child.client('config')
		# Delete ConfigurationRecorders
		try:
			print(ERASE_LINE,
				  f"Deleting recorder from Account {deletion_item['AccountId']} in region {deletion_item['Region']}",
				  end="\r")
			if deletion_item['Type'] == 'Config Recorder':
				Output = client_cf_child.delete_configuration_recorder(
					ConfigurationRecorderName=deletion_item['name']
				)
			elif deletion_item['Type'] == 'Delivery Channel':
				Output = client_cf_child.delete_delivery_channel(
					DeliveryChannelName=deletion_item['name']
				)
		except Exception as my_Error:
			print("Caught unexpected error while deleting. Exiting...")
			logging.error(f"Error: {my_Error}")
			sys.exit(9)
	if pTiming:
		print()
		milestone_time3 = time()
		print(f"{Fore.GREEN}\t\tDeleting {len(AllCredentials)} places took: {milestone_time3 - milestone_time2} seconds{Fore.RESET}")
		print()
	print(f"Removed {len(all_config_recorders_and_delivery_channels)} config recorders and delivery channels")

if pTiming:
	end_time = time()
	duration = end_time - begin_time
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This whole script took {duration} seconds{Fore.RESET}")
print()
print("Thank you for using this tool")
print()
