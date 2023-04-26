#!/usr/bin/env python3

import sys
import Inventory_Modules
from Inventory_Modules import display_results, get_all_credentials
from ArgumentsClass import CommonArguments
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
parser.timing()
parser.fragment()
parser.verbosity()
parser.my_parser.add_argument(
	"+delete", "+forreal",
	dest="flagDelete",
	action="store_true",  # If the parameter is supplied, it will be true, otherwise it's false
	help="Whether to delete the configuration recorders and delivery channels it finds.")
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pAccounts = args.Accounts
pFragments = args.Fragments
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pRootOnly = args.RootOnly
pTiming = args.Time
verbose = args.loglevel
DeletionRun = args.flagDelete
ForceDelete = args.Force
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")


##########################
def check_accounts_for_delivery_channels_and_config_recorders(CredentialList, fRegionList=None, fFragments=None, fFixRun=False):
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
				c_account_credentials, c_fixrun, c_fragments, c_PlacesToLook, c_PlaceCount = self.queue.get()
				logging.info(f"De-queued info for account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']}")
				try:
					logging.info(f"Checking for config recorders and delivery channels in account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']}")
					capture_this_delivery_channel = False
					account_dcs = Inventory_Modules.find_delivery_channels2(c_account_credentials, c_account_credentials['Region'])
					if len(account_dcs['DeliveryChannels']) > 0:
						if c_fragments is None or 'all' in c_fragments:
							capture_this_delivery_channel = True
							logging.info(f"No fragment provided. Found {account_dcs['DeliveryChannels'][0]['name']}")
						else:
							for fragment in c_fragments:
								if fragment in account_dcs['DeliveryChannels'][0]['name']:
									capture_this_delivery_channel = True
									logging.info(f"Found {account_dcs['DeliveryChannels'][0]['name']} which contains {fragment}")
									break
								else:
									capture_this_delivery_channel = False
									logging.info(f"Looking for {fragment}. Found {account_dcs['DeliveryChannels'][0]['name']}, so skipping...")
						if capture_this_delivery_channel:
							account_dcs['DeliveryChannels'][0].update({'Type'           : 'Delivery Channel',
							                                           'AccountId'      : c_account_credentials['AccountNumber'],
							                                           'AccessKeyId'    : c_account_credentials['AccessKeyId'],
							                                           'SecretAccessKey': c_account_credentials['SecretAccessKey'],
							                                           'SessionToken'   : c_account_credentials['SessionToken'],
							                                           'Region'         : c_account_credentials['Region'],
							                                           'MgmtAccount'    : c_account_credentials['MgmtAccount'],
							                                           'ParentProfile'  : c_account_credentials['ParentProfile'],
							                                           'Deleted'        : False})
							account_crs_and_dcs.extend(account_dcs['DeliveryChannels'])

					account_crs = Inventory_Modules.find_config_recorders2(c_account_credentials, c_account_credentials['Region'])
					capture_this_config_recorder = False
					if len(account_crs['ConfigurationRecorders']) > 0:
						if c_fragments is None or 'all' in c_fragments:
							capture_this_config_recorder = True
							logging.info(f"No fragment provided. Found {account_crs['ConfigurationRecorders'][0]['name']}")
						else:
							for fragment in c_fragments:
								if fragment in account_crs['ConfigurationRecorders'][0]['name']:
									capture_this_config_recorder = True
									logging.info(f"Found {account_crs['ConfigurationRecorders'][0]['name']} which contains {fragment}")
									break
								else:
									capture_this_config_recorder = False
									logging.info(f"Looking for {fragment}. Found {account_crs['ConfigurationRecorders'][0]['name']}, so skipping...")
						if capture_this_config_recorder:
							account_crs['ConfigurationRecorders'][0].update({'Type'           : 'Config Recorder',
																			 'AccountId'      : c_account_credentials['AccountNumber'],
																			 'AccessKeyId'    : c_account_credentials['AccessKeyId'],
																			 'SecretAccessKey': c_account_credentials['SecretAccessKey'],
																			 'SessionToken'   : c_account_credentials['SessionToken'],
																			 'Region'         : c_account_credentials['Region'],
																			 'MgmtAccount'    : c_account_credentials['MgmtAccount'],
																			 'ParentProfile'  : c_account_credentials['ParentProfile'],
																			 'Deleted'        : False})
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
					# print(".", end='')
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
		print(".", end='')
		try:
			# print(f"{ERASE_LINE}Queuing account {credential['AccountId']} in region {credential['Region']}", end='\r')
			# I don't know why - but double parens are necessary below. If you remove them, only the first parameter is queued.
			checkqueue.put((credential, fFixRun, fFragments, len(CredentialList), PlaceCount))
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

display_dict = {'ParentProfile': {'Format': '24s', 'DisplayOrder': 1, 'Heading': 'Parent Profile'},
				'MgmtAccount'  : {'Format': '15s', 'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
				'AccountId'    : {'Format': '15s', 'DisplayOrder': 3, 'Heading': 'Acct Number'},
				'Region'       : {'Format': '15s', 'DisplayOrder': 4, 'Heading': 'Region'},
				'Type'         : {'Format': '20s', 'DisplayOrder': 5, 'Heading': 'Type'},
				'name'         : {'Format': '30s', 'DisplayOrder': 6, 'Heading': 'Name'}}

NumObjectsFound = 0
NumAccountsInvestigated = 0

AllCredentials = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)
RegionList = list(set([x['Region'] for x in AllCredentials]))
AccountNum = len(set([acct['AccountId'] for acct in AllCredentials]))

cf_regions = Inventory_Modules.get_service_regions('config', RegionList)
print()
print(f"Searching total of {AccountNum} accounts and {len(cf_regions)} regions")
if pTiming:
	print()
	milestone_time1 = time()
	print(f"{Fore.GREEN}\t\tFiguring out what regions are available to your accounts, and capturing credentials for all accounts in those regions took: {(milestone_time1 - begin_time):.3f} seconds{Fore.RESET}")
	print()
print(f"Now running through all accounts and regions identified to find resources...")
all_config_recorders_and_delivery_channels = check_accounts_for_delivery_channels_and_config_recorders(AllCredentials, cf_regions, pFragments, DeletionRun)

if pTiming:
	print()
	milestone_time2 = time()
	print(f"{Fore.GREEN}\t\tChecking {len(AllCredentials)} places took: {(milestone_time2 - milestone_time1):.3f} seconds{Fore.RESET}")
	print()
cr = dc = 0
for item in all_config_recorders_and_delivery_channels:
	if item['Type'] == 'Delivery Channel':
		dc += 1
	elif item['Type'] == 'Config Recorder':
		cr += 1

all_sorted_config_recorders_and_delivery_channels = sorted(all_config_recorders_and_delivery_channels, key=lambda d: (d['ParentProfile'], d['MgmtAccount'], d['AccountId'], d['Region'], d['Type']))
if pTiming:
	print()
	milestone_time3 = time()
	print(f"{Fore.GREEN}\t\tSorting the list of places took: {(milestone_time3 - milestone_time2):.3f} seconds{Fore.RESET}")
	print()
display_results(all_sorted_config_recorders_and_delivery_channels, display_dict)

print(ERASE_LINE)
print(f"We scanned {AccountNum} accounts and {len(RegionList)} regions totalling {len(AllCredentials)} possible areas for resources.")
print(f"We Found {cr} Configuration Recorders and {dc} Delivery Channels")
print()

if DeletionRun and not ForceDelete:
	ReallyDelete = (input(
		"Deletion of Config Recorders and Delivery Channels has been requested. Are you still sure? (y/n): ") == 'y')
else:
	ReallyDelete = False

if DeletionRun and (ReallyDelete or ForceDelete):
	config_recorders_and_delivery_channels_to_delete = sorted(all_config_recorders_and_delivery_channels, key=lambda d: (d['Type'], d['ParentProfile'], d['MgmtAccount'], d['AccountId']))
	logging.warning("Deleting all Config Recorders")
	i = 0
	while i < len(config_recorders_and_delivery_channels_to_delete):
		deletion_item = config_recorders_and_delivery_channels_to_delete[i]
		# Delete ConfigurationRecorders
		try:
			print(ERASE_LINE, f"Deleting {deletion_item['Type']} from Account {deletion_item['AccountId']} in region {deletion_item['Region']}", end="\r")
			Output = Inventory_Modules.del_config_recorder_or_delivery_channel2(deletion_item)
			all_config_recorders_and_delivery_channels[i].update({'Deleted': Output['Success']})

			# Verify Config Recorder is gone first
			i += 1
		except Exception as my_Error:
			print()
			print("Caught unexpected error while deleting. Exiting...")
			logging.error(f"Error: {my_Error}")
			sys.exit(9)

	if pTiming:
		print()
		milestone_time4 = time()
		print(f"{Fore.GREEN}\t\tDeleting {len(all_config_recorders_and_delivery_channels)} places took: {(milestone_time4 - milestone_time3):.3f} seconds{Fore.RESET}")
		print()
	print(f"Removed {len(all_config_recorders_and_delivery_channels)} config recorders and delivery channels")

if pTiming:
	end_time = time()
	duration = end_time - begin_time
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This whole script took {duration:.3f} seconds{Fore.RESET}")
print()
print("Thank you for using this tool")
print()
