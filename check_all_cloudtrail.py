#!/usr/bin/env python3


# import boto3
import Inventory_Modules
from Inventory_Modules import display_results, get_all_credentials
from ArgumentsClass import CommonArguments
from threading import Thread
from queue import Queue
from colorama import init, Fore
from time import time
from botocore.exceptions import ClientError

import logging

init()
__version__ = "2023.05.31"

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
parser.rootOnly()
parser.save_to_file()
parser.timing()
parser.verbosity()
parser.version(__version__)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pSkipAccounts = args.SkipAccounts
pAccounts = args.Accounts
pSkipProfiles = args.SkipProfiles
pRootOnly = args.RootOnly
pSaveFilename = args.Filename
pTiming = args.Time
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")


##################
def check_account_for_cloudtrail(f_AllCredentials):
	"""
	Note that this function checks the passed in account credentials only
	"""

	class CheckAccountForCloudtrailThreaded(Thread):
		def __init__(self, queue):
			Thread.__init__(self)
			self.queue = queue

		def run(self):
			while True:
				c_account_credentials = self.queue.get()
				try:
					logging.info(f"Checking account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']}")
					Trails = Inventory_Modules.find_account_cloudtrail2(c_account_credentials, c_account_credentials['Region'])
					logging.info(f"Root Account: {c_account_credentials['MgmtAccount']} Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(Trails['trailList'])} trails")
					if 'trailList' in Trails.keys():
						for y in range(len(Trails['trailList'])):
							AllTrails.append({'MgmtAccount'     : c_account_credentials['MgmtAccount'],
							                  'AccountId'       : c_account_credentials['AccountId'],
							                  'Region'          : c_account_credentials['Region'],
							                  'TrailName'       : Trails['trailList'][y]['Name'],
							                  'MultiRegion'     : Trails['trailList'][y]['IsMultiRegionTrail'],
							                  'OrgTrail'        : "OrgTrail" if Trails['trailList'][y]['IsOrganizationTrail'] else "Account Trail",
							                  'Bucket'          : Trails['trailList'][y]['S3BucketName'],
							                  'KMS'             : Trails['trailList'][y]['KmsKeyId'] if 'KmsKeyId' in Trails.keys() else None,
							                  'CloudWatchLogArn': Trails['trailList'][y]['CloudWatchLogsLogGroupArn'] if 'CloudWatchLogsLogGroupArn' in Trails.keys() else None,
							                  'HomeRegion'      : Trails['trailList'][y]['HomeRegion'] if 'HomeRegion' in Trails.keys() else None,
							                  'SNSTopicName'    : Trails['trailList'][y]['SNSTopicName'] if 'SNSTopicName' in Trails.keys() else None,
							                  })
						# AllTrails.append(Trails['trailList'])
				except ClientError as my_Error:
					if str(my_Error).find("AuthFailure") > 0:
						logging.error(f"Authorization Failure accessing account {c_account_credentials['AccountId']} in {c_account_credentials['Region']} region")
						logging.warning(f"It's possible that the region {c_account_credentials['Region']} hasn't been opted-into")
						pass

				finally:
					print(".", end='')
					self.queue.task_done()

	AllTrails = []
	checkqueue = Queue()
	WorkerThreads = min(len(f_AllCredentials), 50)
	for x in range(WorkerThreads):
		worker = CheckAccountForCloudtrailThreaded(checkqueue)
		worker.daemon = True
		worker.start()

	for credential in f_AllCredentials:
		try:
			checkqueue.put((credential)) if credential['Success'] else None
		except ClientError as my_Error:
			logging.error(f"Error: {my_Error}")
			pass

	checkqueue.join()
	return (AllTrails)


##################
ERASE_LINE = '\x1b[2K'

logging.info(f"Profiles: {pProfiles}")
if pTiming:
	begin_time = time()

print()
print(f"Checking for CloudTrails... ")
print()

TrailsFound = []
AllCredentials = []
if pSkipAccounts is None:
	pSkipAccounts = []

AllCredentials = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)


# print(f"{ERASE_LINE}Checking account {credential['AccountId']} in region {credential['Region']}: {account_num} of {len(AllCredentials)}", end='\r')
TrailsFound = check_account_for_cloudtrail(AllCredentials)

AllChildAccountandRegionList = [[item['MgmtAccount'], item['AccountId'], item['Region']] for item in AllCredentials]
ChildAccountsandRegionsWithCloudTrail = [[item['MgmtAccount'], item['AccountId'], item['Region']] for item in TrailsFound]
ProblemAccountsandRegions = [item for item in AllChildAccountandRegionList if item not in ChildAccountsandRegionsWithCloudTrail]
UniqueRegions = list(set([item['Region'] for item in AllCredentials]))

print()

display_dict = {'AccountId'  : {'Format': '15s', 'DisplayOrder': 2, 'Heading': 'Account Number'},
				'MgmtAccount': {'Format': '15s', 'DisplayOrder': 1, 'Heading': 'Parent Acct'},
				'Region'     : {'Format': '15s', 'DisplayOrder': 3, 'Heading': 'Region'},
				'TrailName'  : {'Format': '40s', 'DisplayOrder': 5, 'Heading': 'Trail Name'},
				'OrgTrail'   : {'Format': '15s', 'DisplayOrder': 4, 'Heading': 'Org Trail?'},
				'Bucket'     : {'Format': '20s', 'DisplayOrder': 6, 'Heading': 'S3 Bucket'}}
sorted_Results = sorted(TrailsFound, key=lambda d: (d['MgmtAccount'], d['AccountId'], d['Region'], d['TrailName']))
ProblemAccountsandRegions.sort()
display_results(sorted_Results, display_dict, "None", pSaveFilename)

print(f"These accounts were skipped - as requested: {pSkipAccounts}")
print(f"There were {len(ProblemAccountsandRegions)} accounts and regions that didn't seem to have a CloudTrail associated: \n")
for item in ProblemAccountsandRegions:
	print(item)
print()
print(f"Found {len(TrailsFound)} trails across {len(AllCredentials)} accounts across {len(UniqueRegions)} regions")
print()
if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
print("Thank you for using this script")
print()
