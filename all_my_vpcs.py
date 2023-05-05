#!/usr/bin/env python3


import Inventory_Modules
from Inventory_Modules import get_all_credentials, display_results
from ArgumentsClass import CommonArguments
from time import time
from threading import Thread
from queue import Queue
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()
__version__ = "2023.05.04"

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
parser.rootOnly()
parser.timing()
parser.verbosity()
parser.version(__version__)
parser.my_parser.add_argument(
	"--default",
	dest="pDefault",
	metavar="Looking for default VPCs only",
	action="store_const",
	default=False,
	const=True,
	help="Flag to determine whether we're looking for default VPCs only.")
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pAccounts = args.Accounts
pSkipProfiles = args.SkipProfiles
pSkipAccounts = args.SkipAccounts
pRootOnly = args.RootOnly
pTiming = args.Time
pDefault = args.pDefault
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")


##########################

def find_all_vpcs(fAllCredentials, fDefaultOnly=False):
	"""
	Note that this function takes a list of stack set names and finds the stack instances within them
	"""

	# This function is called
	class FindVPCs(Thread):

		def __init__(self, queue):
			Thread.__init__(self)
			self.queue = queue

		def run(self):
			while True:
				# Get the work from the queue and expand the tuple
				c_account_credentials, c_default, c_PlaceCount = self.queue.get()
				logging.info(f"De-queued info for account number {c_account_credentials['AccountId']}")
				try:
					# Now go through those stacksets and determine the instances, made up of accounts and regions
					Vpcs = Inventory_Modules.find_account_vpcs2(c_account_credentials, c_default)
					logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(Vpcs['Vpcs'])} VPCs")
					if 'Vpcs' in Vpcs.keys() and len(Vpcs['Vpcs']) > 0:
						for y in range(len(Vpcs['Vpcs'])):
							VpcId = Vpcs['Vpcs'][y]['VpcId']
							IsDefault = Vpcs['Vpcs'][y]['IsDefault']
							CIDR = Vpcs['Vpcs'][y]['CidrBlock']
							if 'Tags' in Vpcs['Vpcs'][y]:
								for z in range(len(Vpcs['Vpcs'][y]['Tags'])):
									if Vpcs['Vpcs'][y]['Tags'][z]['Key'] == "Name":
										VpcName = Vpcs['Vpcs'][y]['Tags'][z]['Value']
							else:
								VpcName = "No name defined"
							AllVPCs.append({'MgmtAccount': c_account_credentials['MgmtAccount'],
							                'AccountId'  : c_account_credentials['AccountId'],
							                'Region'     : c_account_credentials['Region'],
							                'CIDR'       : CIDR,
							                'VpcId'      : VpcId,
							                'IsDefault'  : IsDefault,
							                'VpcName'    : VpcName})
					else:
						continue

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
					print(".", end='')
					self.queue.task_done()

	###########

	checkqueue = Queue()

	AllVPCs = []
	PlaceCount = 0
	WorkerThreads = min(len(fAllCredentials), 25)

	for x in range(WorkerThreads):
		worker = FindVPCs(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	for credential in fAllCredentials:
		logging.info(f"Beginning to queue data - starting with {credential['AccountId']}")
		# for region in fRegionList:
		try:
			# I don't know why - but double parens are necessary below. If you remove them, only the first parameter is queued.
			checkqueue.put((credential, fDefaultOnly, PlaceCount))
			logging.info(f"Put credential: {credential}, Default: {fDefaultOnly}")
			PlaceCount += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
				logging.warning(f"It's possible that the region {credential['Region']} hasn't been opted-into")
				pass
	checkqueue.join()
	return (AllVPCs)


##########################
ERASE_LINE = '\x1b[2K'

if pTiming:
	begin_time = time()

NumVpcsFound = 0
NumRegions = 0
print()

NumOfRootProfiles = 0

AllCredentials = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)
AllRegionsList = list(set([x['Region'] for x in AllCredentials]))
AllAccountList = list(set([x['AccountId'] for x in AllCredentials]))
display_dict = {'MgmtAccount': {'Format': '12s', 'DisplayOrder': 1, 'Heading': 'Mgmt Acct'},
                'AccountId'  : {'Format': '12s', 'DisplayOrder': 2, 'Heading': 'Acct Number'},
                'Region'     : {'Format': '15s', 'DisplayOrder': 3, 'Heading': 'Region'},
                'VpcName'    : {'Format': '20s', 'DisplayOrder': 4, 'Heading': 'VPC Name'},
                'CIDR'       : {'Format': '18s', 'DisplayOrder': 5, 'Heading': 'CIDR Block'},
                'VpcId'      : {'Format': '15s', 'DisplayOrder': 6, 'Heading': 'VPC Id'}}

logging.info(f"# of Regions: {len(pRegionList)}")
logging.info(f"# of Management Accounts: {NumOfRootProfiles}")
logging.info(f"# of Child Accounts: {len(AllCredentials)}")

All_VPCs_Found = find_all_vpcs(AllCredentials, pDefault)
sorted_AllVPCs = sorted(All_VPCs_Found, key=lambda d: (d['MgmtAccount'], d['AccountId'], d['Region'], d['VpcName'], d['CIDR']))
print()
display_results(sorted_AllVPCs, display_dict, None)

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time} seconds{Fore.RESET}")
print(ERASE_LINE)
print(f"Found {len(All_VPCs_Found)}{' default' if pDefault else ''} Vpcs across {len(AllAccountList)} accounts across {len(AllRegionsList)} regions")
print()
print("Thank you for using this script.")
print()
