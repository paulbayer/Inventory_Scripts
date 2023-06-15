#!/usr/bin/env python3


import Inventory_Modules
from Inventory_Modules import display_results, get_all_credentials
from ArgumentsClass import CommonArguments
from colorama import init, Fore
from time import time
from threading import Thread
from queue import Queue
from botocore.exceptions import ClientError

import logging

init()
__version__ = "2023.05.31"

parser = CommonArguments()
parser.multiregion()
parser.multiprofile()
parser.extendedargs()
parser.rootOnly()
parser.verbosity()
parser.timing()
parser.version(__version__)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pSkipProfiles = args.SkipProfiles
pSkipAccounts = args.SkipAccounts
pRootOnly = args.RootOnly
pAccounts = args.Accounts
pTiming = args.Time
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")


########################
def find_all_hosted_zones(fAllCredentials):
	"""
	Note that this function takes a list of stack set names and finds the hosted zones within them

	"""

	# This function is called
	class FindZones(Thread):

		def __init__(self, queue):
			Thread.__init__(self)
			self.queue = queue

		def run(self):
			while True:
				# Get the work from the queue and expand the tuple
				c_account_credentials, c_PlaceCount = self.queue.get()
				logging.info(f"De-queued info for account number {c_account_credentials['AccountId']}")
				try:
					# Now go through those stacksets and determine the instances, made up of accounts and regions
					# Most time spent in this loop
					# TODO: Need paging here
					HostedZones = Inventory_Modules.find_private_hosted_zones2(c_account_credentials, c_account_credentials['Region'])
					# Instances = Inventory_Modules.find_account_instances2(c_account_credentials, c_account_credentials['Region'])
					logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(HostedZones['HostedZones'])} zones")

					if len(HostedZones['HostedZones']) > 0:
						for zone in HostedZones['HostedZones']:
							ThreadedHostedZones.append({'ParentProfile': c_account_credentials['ParentProfile'],
							                       'MgmtAccount'  : c_account_credentials['MgmtAccount'],
							                       'AccountId'    : c_account_credentials['AccountId'],
							                       'Region'       : c_account_credentials['Region'],
							                       'PHZName'      : zone['Name'],
							                       'Records'      : zone['ResourceRecordSetCount'],
							                       'PHZId'        : zone['Id']})
				except KeyError as my_Error:
					logging.error(f"Account Access failed - trying to access {c_account_credentials['AccountId']}")
					logging.info(f"Actual Error: {my_Error}")
					pass
				except AttributeError as my_Error:
					logging.error(f"Error: Likely that one of the supplied profiles was wrong")
					logging.warning(my_Error)
					continue
				except ClientError as my_Error:
					if str(my_Error).find("AuthFailure") > 0:
						logging.error(f"Authorization Failure accessing account {c_account_credentials['AccountId']} in {c_account_credentials['Region']} region")
						logging.warning(f"It's possible that the region {c_account_credentials['Region']} hasn't been opted-into")
						continue
					else:
						logging.error(f"Error: Likely throttling errors from too much activity")
						logging.warning(my_Error)
						continue
				finally:
					# print(f"{ERASE_LINE}Finished finding instances in account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']} - {c_PlaceCount} / {len(AllCredentials)}", end='\r')
					print(".", end='')
					self.queue.task_done()

	###########

	checkqueue = Queue()

	ThreadedHostedZones = []
	PlaceCount = 0
	WorkerThreads = min(len(fAllCredentials), 25)

	for x in range(WorkerThreads):
		worker = FindZones(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	for credential in fAllCredentials:
		logging.info(f"Beginning to queue data - starting with {credential['AccountId']}")
		# for region in fRegionList:
		try:
			# I don't know why - but double parens are necessary below. If you remove them, only the first parameter is queued.
			checkqueue.put((credential, PlaceCount))
			PlaceCount += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
				logging.warning(f"It's possible that the region {credential['Region']} hasn't been opted-into")
				pass
	checkqueue.join()
	return (ThreadedHostedZones)


########################
ERASE_LINE = '\x1b[2K'

if pTiming:
	begin_time = time()

AllCredentials = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)
AllAccountList = list(set([x['AccountId'] for x in AllCredentials]))
AllRegionList = list(set([x['Region'] for x in AllCredentials]))
AllHostedZones = find_all_hosted_zones(AllCredentials)

print()

display_dict = {'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
                'MgmtAccount'  : {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
                'AccountId'    : {'DisplayOrder': 3, 'Heading': 'Acct Number'},
                'Region'       : {'DisplayOrder': 4, 'Heading': 'Region'},
                'PHZName'      : {'DisplayOrder': 5, 'Heading': 'Zone Name'},
                'Records'      : {'DisplayOrder': 6, 'Heading': '# of Records'},
                'PHZId'        : {'DisplayOrder': 7, 'Heading': 'Zone ID'}}

sort_Hosted_Zones = sorted(AllHostedZones, key=lambda x: (x['ParentProfile'], x['MgmtAccount'], x['AccountId'], x['PHZName'], x['Region']))
display_results(sort_Hosted_Zones, display_dict)

print(ERASE_LINE)
print(f"{Fore.RED}Found {len(AllHostedZones)} Hosted Zones across {len(AllAccountList)} accounts across {len(AllRegionList)} regions{Fore.RESET}")
print()
if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
	print(ERASE_LINE)
print("Thanks for using this script...")
print()
