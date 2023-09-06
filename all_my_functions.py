#!/usr/bin/env python3
import boto3

import Inventory_Modules
from Inventory_Modules import get_credentials_for_accounts_in_org, display_results
from colorama import init, Fore
from botocore.exceptions import ClientError
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from queue import Queue
from threading import Thread
from time import time
import sys

import logging

init()
__version__ = "2023.09.06"

parser = CommonArguments()
parser.multiprofile()  # Allows for a single profile to be specified
parser.multiregion()  # Allows for multiple regions to be specified at the command line
parser.fragment()  # Allows for soecifying a string fragment to be looked for
parser.extendedargs()
parser.rootOnly()
parser.save_to_file()
parser.timing()
parser.fix()
parser.deletion()
parser.verbosity()  # Allows for the verbosity to be handled.
parser.version(__version__)
parser.my_parser.add_argument(
	"--runtime", "--run", "--rt",
	dest="Runtime",
	nargs="*",
	metavar="language and version",
	default=None,
	help="Language runtime(s) you're looking for within your accounts")
parser.my_parser.add_argument(
	"--new_runtime", "--new",
	dest="NewRuntime",
	metavar="language and version",
	default=None,
	help="Language runtime(s) you will replace what you've found with... ")
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pFragments = args.Fragments
pAccounts = args.Accounts
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pRootOnly = args.RootOnly
pTiming = args.Time
pFix = args.Fix
pForceDelete = args.Force
pSaveFilename = args.Filename
pRuntime = args.Runtime
pNewRuntime = args.NewRuntime
verbose = args.loglevel

logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

SkipProfiles = ["default"]


def left(s, amount):
	return s[:amount]


def right(s, amount):
	return s[-amount:]


def mid(s, offset, amount):
	return s[offset - 1:offset + amount - 1]

def fix_runtime(CredentialList, new_runtime):
	from time import sleep
	class UpdateRuntime(Thread):
		def __init__(self, queue):
			Thread.__init__(self)
			self.queue = queue

		def run(self):
			while True:
				c_account_credentials, c_function_name, c_new_runtime = self.queue.get()
				logging.info(f"De-queued info for account {c_account_credentials['AccountId']}")
				try:
					logging.info(f"Attempting to update {c_function_name} to {c_new_runtime}")
					Success = False
					session = boto3.Session(aws_access_key_id=c_account_credentials['AccessKeyId'],
					                        aws_secret_access_key=c_account_credentials['SecretAccessKey'],
					                        aws_session_token=c_account_credentials['SessionToken'],
					                        region_name=c_account_credentials['Region'])
					client = session.client('lambda')
					logging.info(f"Updating function {c_function_name} to runtime {c_new_runtime}")
					Updated_Function = client.update_function_configuration(FunctionName=c_function_name,
					                                                        Runtime=c_new_runtime)
					sleep(3)
					Success = client.get_function_configuration(FunctionName=c_function_name)['LastUpdateStatus'] == 'Successful'
					while not Success:
						Status = client.get_function_configuration(FunctionName=c_function_name)['LastUpdateStatus']
						Success = True if Status == 'Successful' else 'False'
						if Status == 'InProgress':
							sleep(3)
							logging.info(f"Sleeping to allow {c_function_name} to update to runtime {c_new_runtime}")
						elif Status == 'Failed':
							raise Exception(f'Runtime update for {c_function_name} to {c_new_runtime} failed')
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
					if Success:
						Updated_Function['MgmtAccount'] = c_account_credentials['MgmtAccount']
						Updated_Function['AccountId'] = c_account_credentials['AccountId']
						Updated_Function['Region'] = c_account_credentials['Region']
						Rolet = Updated_Function['Role']
						Updated_Function['Role'] = mid(Rolet, Rolet.find("/") + 2, len(Rolet))
						FixedFuncs.extend(Updated_Function)
					self.queue.task_done()

	FixedFuncs = []
	PlaceCount = 0
	PlacesToLook = len(CredentialList)
	WorkerThreads = min(len(CredentialList), 25)

	checkqueue = Queue()

	for x in range(WorkerThreads):
		worker = UpdateRuntime(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	for credential in CredentialList:
		logging.info(f"Connecting to account {credential['AccountId']}")
		try:
			print(f"{ERASE_LINE}Queuing function {credential['FunctionName']} in account {credential['AccountId']} in region {credential['Region']}", end='\r')
			checkqueue.put((credential, credential['FunctionName'], new_runtime))
			PlaceCount += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
				logging.error(f"It's possible that the region {credential['Region']} hasn't been opted-into")
				pass
	checkqueue.join()
	return (FixedFuncs)


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
							Functions[_]['AccessKeyId'] = c_account_credentials['AccessKeyId']
							Functions[_]['SecretAccessKey'] = c_account_credentials['SecretAccessKey']
							Functions[_]['SessionToken'] = c_account_credentials['SessionToken']
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

print(f"Collecting credentials... ")

if pProfiles is None:
	aws_acct = aws_acct_access()
	RegionList.extend(Inventory_Modules.get_ec2_regions3(aws_acct, pRegionList))
	profile = "None"
	CredentialList = get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList)
else:
	ProfileList = Inventory_Modules.get_profiles(SkipProfiles, pProfiles)
	for profile in ProfileList:
		try:
			aws_acct = aws_acct_access(profile)
			RegionList = Inventory_Modules.get_ec2_regions3(aws_acct, pRegionList)
			CredentialList.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList))
		except AttributeError as myError:
			print(f"Failed on profile: {profile}, but continuing on...")
			continue

RegionList = list(set(RegionList))
if pTiming:
	print(f"{Fore.GREEN}Took {time() - begin_time:.3f} seconds to find all credentials{Fore.RESET}")

AccountNum = len(set([acct['AccountId'] for acct in CredentialList]))
print()
print(f"Looking through {AccountNum} accounts and {len(RegionList)} regions ")
print()

AllFunctions = check_accounts_for_functions(CredentialList, pFragments)

display_dict = {'MgmtAccount' : {'DisplayOrder': 1, 'Heading': 'Mgmt Acct'},
                'AccountId'   : {'DisplayOrder': 2, 'Heading': 'Acct Number'},
                'Region'      : {'DisplayOrder': 3, 'Heading': 'Region'},
                'FunctionName': {'DisplayOrder': 4, 'Heading': 'Function Name'},
                'Runtime'     : {'DisplayOrder': 5, 'Heading': 'Runtime'},
                'Role'        : {'DisplayOrder': 6, 'Heading': 'Role'}}
sorted_results = sorted(AllFunctions, key=lambda k: (k['MgmtAccount'], k['AccountId'], k['Region'], k['FunctionName']))

display_results(sorted_results, display_dict, None, pSaveFilename)

if pTiming and pFix:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}Finding all functions took {time() - begin_time:.3f} seconds{Fore.RESET}")
	begin_fix_time = time()

pFix = pFix and len(AllFunctions) > 0

if pFix and pNewRuntime is None:
	print(f"You provided the parameter at the command line to *fix* errors found, but didn't supply a new runtime to use, so exiting now... ")
	sys.exit(8)
elif pFix and not pForceDelete:
	print(f"You provided the parameter at the command line to *fix* errors found")
	ReallyDelete = (input("Having seen what will change, are you still sure? (y/n): ") in ['y', 'Y', 'Yes', 'yes'])
elif pFix and pForceDelete:
	print(f"You provided the parameter at the command line to *fix* errors found, as well as FORCING this change to happen... ")
	ReallyDelete = True
else:
	ReallyDelete = False

if ReallyDelete:
	print(f"Updating Runtime for all functions found to {pNewRuntime}")
	FixedFunctions = fix_runtime(AllFunctions, pNewRuntime)

	print()
	print(f"New results:")
	display_results(FixedFunctions, display_dict, None, pSaveFilename) if len(FixedFunctions) > 0 else None
	if pTiming:
		print(ERASE_LINE)
		print(f"{Fore.GREEN}Fixing {len(FixedFunctions)} functions took {time() - begin_fix_time:.3f} seconds{Fore.RESET}")

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time:.3f} seconds{Fore.RESET}")
print(ERASE_LINE)
print(f"Found {len(AllFunctions)} functions across {AccountNum} accounts, across {len(RegionList)} regions")
print()
print("Thank you for using this script")
print()
