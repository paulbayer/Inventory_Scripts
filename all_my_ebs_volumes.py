#!/usr/bin/env python3

# import boto3
from Inventory_Modules import display_results, get_all_credentials, find_account_volumes2
from ArgumentsClass import CommonArguments
from colorama import init, Fore
from botocore.exceptions import ClientError
from queue import Queue
from threading import Thread
from time import time

import logging

init()
__version__ = "2023.07.18"

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
parser.fragment()
parser.rootOnly()
parser.save_to_file()
parser.timing()
parser.verbosity()
parser.version(__version__)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pAccounts = args.Accounts
pFragments = args.Fragments
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pRootOnly = args.RootOnly
# pText_to_find = args.pText_To_Find
pFilename = args.Filename
pTiming = args.Time
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

##################

ERASE_LINE = '\x1b[2K'

logging.info(f"Profiles: {pProfiles}")

##################


# def check_accounts_for_ebs_volumes(CredentialList, fRegionList=None, ftext_to_find=None):
def check_accounts_for_ebs_volumes(fCredentialList, ffragment_list=None):
	"""
	Note that this function takes a list of Credentials and checks for EBS Volumes in every account it has creds for
	"""

	class FindVolumes(Thread):

		def __init__(self, queue):
			Thread.__init__(self)
			self.queue = queue

		def run(self):
			while True:
				# Get the work from the queue and expand the tuple
				# c_account_credentials, c_region, c_text_to_find, c_PlacesToLook, c_PlaceCount = self.queue.get()
				c_account_credentials, c_region, c_fragment, c_PlacesToLook, c_PlaceCount = self.queue.get()
				logging.info(f"De-queued info for account {c_account_credentials['AccountId']}")
				try:
					logging.info(f"Attempting to connect to {c_account_credentials['AccountId']}")
					# account_volumes = find_account_volumes2(c_account_credentials, c_text_to_find)
					account_volumes = find_account_volumes2(c_account_credentials)
					logging.info(f"Successfully connected to account {c_account_credentials['AccountId']}")
					for _ in range(len(account_volumes)):
						account_volumes[_]['MgmtAccount'] = c_account_credentials['MgmtAccount']
					AllVolumes.extend(account_volumes)
				except KeyError as my_Error:
					logging.error(f"Account Access failed - trying to access {c_account_credentials['AccountId']}")
					logging.info(f"Actual Error: {my_Error}")
					pass
				except AttributeError as my_Error:
					logging.error(f"Error: Likely that one of the supplied profiles {pProfiles} was wrong")
					logging.warning(my_Error)
					continue
				finally:
					print(f"{ERASE_LINE}Finished finding subnets in account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']} - {c_PlaceCount} / {c_PlacesToLook}", end='\r')
					self.queue.task_done()

	checkqueue = Queue()

	if ffragment_list is None:
		ffragment_list = []
	AllVolumes = []
	PlaceCount = 1
	PlacesToLook = len(fCredentialList)
	WorkerThreads = min(len(fCredentialList), 50)

	for x in range(WorkerThreads):
		worker = FindVolumes(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	for credential in fCredentialList:
		logging.info(f"Connecting to account {credential['AccountId']}")
		try:
			# print(f"{ERASE_LINE}Queuing account {credential['AccountId']} in region {region}", end='\r')
			checkqueue.put((credential, credential['Region'], ffragment_list, PlacesToLook, PlaceCount))
			PlaceCount += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {credential['AccountId']} in '{credential['Region']}' region")
				logging.warning(f"It's possible that the region '{credential['Region']}' hasn't been opted-into")
				pass
	checkqueue.join()
	return (AllVolumes)


##################

if pTiming:
	begin_time = time()
print()
print(f"Checking for EBS Volumes... ")
print()

display_dict = {'MgmtAccount': {'DisplayOrder': 1, 'Heading': 'Mgmt Acct'},
                'AccountId'  : {'DisplayOrder': 2, 'Heading': 'Acct Number'},
                'Region'     : {'DisplayOrder': 3, 'Heading': 'Region'},
                'VolumeName' : {'DisplayOrder': 4, 'Heading': 'Volume Name'},
                'State'      : {'DisplayOrder': 5, 'Heading': 'State', 'Condition': ['available', 'creating', 'deleting', 'deleted', 'error']},
                'Size'       : {'DisplayOrder': 6, 'Heading': 'Size (GBs)'},
                # 'KmsKeyId'   : {'DisplayOrder': 9, 'Heading': 'Encryption Key'},
                'Throughput'   : {'DisplayOrder': 8, 'Heading': 'Throughput'},
                'VolumeType' : {'DisplayOrder': 7, 'Heading': 'Type'}}

VolumesFound = []
CredentialList = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)
RegionList = list(set([x['Region'] for x in CredentialList]))
AccountList = list(set([x['AccountId'] for x in CredentialList]))

VolumesFound.extend(check_accounts_for_ebs_volumes(CredentialList, pFragments))
OrphanedVolumes = [x for x in VolumesFound if x['State'] in ['available', 'error']]

sorted_Volumes_Found = sorted(VolumesFound, key=lambda x: (x['MgmtAccount'], x['AccountId'], x['Region'], x['VolumeName'], x['Size']))
display_results(sorted_Volumes_Found, display_dict, 'None', pFilename)

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script completed in {time() - begin_time:.2f} seconds{Fore.RESET}")
print()
print(f"These accounts were skipped - as requested: {pSkipAccounts}") if pSkipAccounts is not None else ""
print(f"These profiles were skipped - as requested: {pSkipProfiles}") if pSkipProfiles is not None else ""
print(f"This output has also been written to a file beginning with '{pFilename}' + the date and time") if pFilename is not None else ""
print()
print(f"Found {len(VolumesFound)} volumes across {len(AccountList)} account{'' if len(AccountList) == 1 else 's'} "
      f"across {len(RegionList)} region{'' if len(RegionList) == 1 else 's'}")
print()
print(f"{Fore.RED}Found {len(OrphanedVolumes)} volume{'' if len(OrphanedVolumes) == 1 else 's'} that aren't attached to anything.\n"
      f"Th{'is' if len(OrphanedVolumes) == 1 else 'ese'} are likely orphaned, and should be considered for deletion to save costs.{Fore.RESET}") if len(OrphanedVolumes) > 0 else ""
print()
print("Thank you for using this script")
print()
