#!/usr/bin/env python3

import Inventory_Modules
from Inventory_Modules import get_credentials_for_accounts_in_org
from colorama import init, Fore
from botocore.exceptions import ClientError
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from queue import Queue
from threading import Thread
from time import time

from prettytable import PrettyTable

import logging

init()
__version__ = "2023.05.04"

parser = CommonArguments()
parser.multiprofile()  # Allows for a single profile to be specified
parser.multiregion()  # Allows for multiple regions to be specified at the command line
parser.fragment()   # Allows for soecifying a string fragment to be looked for
parser.extendedargs()
parser.rootOnly()
parser.timing()
parser.verbosity()  # Allows for the verbosity to be handled.
parser.version(__version__)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pFragments = args.Fragments
pAccounts = args.Accounts
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pRootOnly = args.RootOnly
pTiming = args.Time
verbose = args.loglevel

logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

SkipProfiles = ["default"]


def left(s, amount):
	return s[:amount]


def right(s, amount):
	return s[-amount:]


def mid(s, offset, amount):
	return s[offset - 1:offset + amount - 1]


def check_accounts_for_functions(CredentialList, fFragments=None):
	"""
	Note that this function takes a list of Credentials and checks for functions in every account it has creds for
	"""

	class FindFunctions(Thread):

		def __init__(self, queue):
			Thread.__init__(self)
			self.queue = queue

		def run(self):
			while True:
				# Get the work from the queue and expand the tuple
				c_account_credentials, c_fragment_list, c_PlacesToLook, c_PlaceCount = self.queue.get()
				logging.info(f"De-queued info for account {c_account_credentials['AccountId']}")
				try:
					logging.info(f"Attempting to connect to {c_account_credentials['AccountId']}")
					Functions = Inventory_Modules.find_lambda_functions2(c_account_credentials, c_account_credentials['Region'], c_fragment_list)
					# FunctionNum = len(Functions['Functions'])
					# logging.info(f"{ERASE_LINE}Account: {acct['AccountId']} Region: {region} Found {FunctionNum} functions", end='\r')
				except TypeError as my_Error:
					logging.info(f"Error: {my_Error}")
					continue
				except ClientError as my_Error:
					if str(my_Error).find("AuthFailure") > 0:
						logging.error(f"Account {c_account_credentials['AccountId']}: Authorization Failure")
					continue
				except KeyError as my_Error:
					logging.error(f"Account Access failed - trying to access {c_account_credentials['AccountId']}")
					logging.info(f"Actual Error: {my_Error}")
					continue
				finally:
					if len(Functions) > 0:
						for _ in range(len(Functions)):
							Functions[_]['MgmtAccount'] = c_account_credentials['MgmtAccount']
							Functions[_]['AccountId'] = c_account_credentials['AccountId']
							Functions[_]['Region'] = c_account_credentials['Region']
							# Functions[_]['FunctionName'] = Functions[_]['FunctionName']
							# Functions[_]['FunctionName'] = Functions[_]['RunTime']
							Rolet = Functions[_]['Role']
							Functions[_]['Role'] = mid(Rolet, Rolet.find("/") + 2, len(Rolet))
						AllFuncs.extend(Functions)
					self.queue.task_done()

	AllFuncs = []
	PlaceCount = 0
	PlacesToLook = len(CredentialList)
	WorkerThreads = min(len(CredentialList), 25)

	checkqueue = Queue()

	for x in range(WorkerThreads):
		worker = FindFunctions(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	for credential in CredentialList:
		logging.info(f"Connecting to account {credential['AccountId']}")
		try:
			print(f"{ERASE_LINE}Queuing account {credential['AccountId']} in region {credential['Region']}", end='\r')
			checkqueue.put((credential, fFragments, PlacesToLook, PlaceCount))
			PlaceCount += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
				logging.error(f"It's possible that the region {credential['Region']} hasn't been opted-into")
				pass
	checkqueue.join()
	return (AllFuncs)


##########################

if pTiming:
	begin_time = time()

ERASE_LINE = '\x1b[2K'
NumInstancesFound = 0
NumOfRootProfiles = 0
AllChildAccounts = []
RegionList = []
CredentialList = []

if pProfiles is None:
	aws_acct = aws_acct_access()
	RegionList.extend(Inventory_Modules.get_ec2_regions3(aws_acct, pRegionList))
	profile = "None"
	CredentialList = get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList)
	# AllChildAccounts.extend(aws_acct.ChildAccounts)
	# if aws_acct.AccountType.lower() == 'root':
	# 	NumOfRootProfiles += 1
else:
	ProfileList = Inventory_Modules.get_profiles(SkipProfiles, pProfiles)
	for profile in ProfileList:
		try:
			aws_acct = aws_acct_access(profile)
			RegionList = Inventory_Modules.get_ec2_regions3(aws_acct, pRegionList)
			CredentialList.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList))
			# print(f"{ERASE_LINE}Looking at account {aws_acct.acct_number} within profile: {profile}", end='\r')
			# credentials = Inventory_Modules.get_child_access3(aws_acct, aws_acct.acct_number)
			# credential_list.append(credentials)
		except AttributeError as myError:
			print(f"Failed on profile: {profile}, but continuing on...")
			continue
		# AllChildAccounts.extend(aws_acct.ChildAccounts)
		# print(ERASE_LINE, f"Gathering all account data from account # {aws_acct.acct_number}", end="\r")
		# if aws_acct.AccountType.lower() == 'root':
		# 	NumOfRootProfiles += 1

RegionList = list(set(RegionList))
if pTiming:
	logging.critical(f"{Fore.GREEN}Time so far is {time()-begin_time}{Fore.RESET}")

AccountNum = len(set([acct['AccountId'] for acct in CredentialList]))
print()
print(f"Looking through {AccountNum} accounts and {len(RegionList)} regions ")
print()

AllFunctions = check_accounts_for_functions(CredentialList, pFragments)

print(f"This table represents the summary of functions within the Org:")
x = PrettyTable()
x.field_names = ['Root Account', 'Account', 'Region', 'Function Name', 'Runtime', 'Role']
x.align["Function Name"] = "l"
x.align["Role"] = "l"
x.align["Runtime"] = "l"

for item in AllFunctions:
	x.add_row([item['MgmtAccount'], item['AccountId'], item['Region'], item['FunctionName'], item['Runtime'], item['Role']])
print()
print(x)
print()

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time()-begin_time} seconds{Fore.RESET}")
print(ERASE_LINE)
print(f"Found {len(AllFunctions)} functions across {AccountNum} accounts, across {len(RegionList)} regions")
print()
print("Thank you for using this script")
print()
