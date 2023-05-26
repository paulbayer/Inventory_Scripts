#!/usr/bin/env python3

# import boto3
import Inventory_Modules
from Inventory_Modules import display_results, get_all_credentials
from ArgumentsClass import CommonArguments
# from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError
from queue import Queue
from threading import Thread
from time import time

import logging

init()
__version__ = "2023.05.04"

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
parser.rootOnly()
parser.fragment()
parser.timing()
parser.verbosity()
parser.version(__version__)
parser.my_parser.add_argument(
	"--action",
	dest="paction",
	nargs="*",
	metavar="AWS Action",
	default=None,
	help="An action you're looking for within the policies")
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pAccounts = args.Accounts
pFragment = args.Fragments
pRootOnly = args.RootOnly
pAction = args.paction
pExact = args.Exact
pTiming = args.Time
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

##################

ERASE_LINE = '\x1b[2K'

logging.info(f"Profiles: {pProfiles}")

##################


def check_accounts_for_policies(CredentialList, fRegionList=None, fAction=None, fFragment=None):
	"""
	Note that this function takes a list of Credentials and checks for subnets in every account it has creds for
	"""

	class FindActions(Thread):

		def __init__(self, queue):
			Thread.__init__(self)
			self.queue = queue

		def run(self):
			while True:
				# Get the work from the queue and expand the tuple
				c_account_credentials, c_policy, c_action, c_PlacesToLook, c_PlaceCount = self.queue.get()
				logging.info(f"De-queued info for account {c_account_credentials['AccountId']}")
				try:
					logging.info(f"Attempting to connect to {c_account_credentials['AccountId']}")
					policy_actions = Inventory_Modules.find_policy_action(c_account_credentials, c_policy, c_action)
					logging.info(f"Successfully connected to account {c_account_credentials['AccountId']}")
					if policy_actions:
						AllPolicies.append(policy_actions)
				except KeyError as my_Error:
					logging.error(f"Account Access failed - trying to access {c_account_credentials['AccountId']}")
					logging.info(f"Actual Error: {my_Error}")
					pass
				except AttributeError as my_Error:
					logging.error(f"Error: Likely that one of the supplied profiles {pProfiles} was wrong")
					logging.warning(my_Error)
					continue
				finally:
					print(f"{ERASE_LINE}Finished finding policy actions in account {c_account_credentials['AccountId']} - {c_PlaceCount} / {c_PlacesToLook}", end='\r')
					self.queue.task_done()

	if fRegionList is None:
		fRegionList = ['us-east-1']
	if fFragment is None:
		fFragment = []
	checkqueue = Queue()

	AllPolicies = []
	AccountCount = 0
	Policies = []

	print()
	for credential in CredentialList:
		logging.info(f"Connecting to account {credential['AccountId']}")
		try:
			Policies = Inventory_Modules.find_account_policies2(credential, fRegionList[0], fFragment, pExact)
			AccountCount += 1
			PlacesToLook = len(Policies)
			print(f"{ERASE_LINE}Found {PlacesToLook} matching policies in account {credential['AccountId']} ({AccountCount}/{len(CredentialList)})", end='\r')
			# print(f"{ERASE_LINE}Queuing account {credential['AccountId']} in region {region}", end='\r')
			if fAction is None:
				AllPolicies.extend(Policies)
			else:
				for policy in Policies:
					checkqueue.put((credential, policy, fAction, PlacesToLook, AccountCount))
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {credential['AccountId']}")
				pass

	# WorkerThreads = min(len(Policies) * len(fAction), 250)
	WorkerThreads = min(AccountCount, 12)

	for x in range(WorkerThreads):
		worker = FindActions(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	checkqueue.join()
	return (AllPolicies)


##################

begin_time = time()
print()
print(f"Checking for matching Policies... ")
print()

display_dict = {'MgmtAccount'  : {'Format': '12s', 'DisplayOrder': 1, 'Heading': 'Mgmt Acct'},
				'AccountNumber': {'Format': '12s', 'DisplayOrder': 2, 'Heading': 'Acct Number'},
				'Region'       : {'Format': '15s', 'DisplayOrder': 3, 'Heading': 'Region'},
				'PolicyName'   : {'Format': '40s', 'DisplayOrder': 4, 'Heading': 'Policy Name'},
				'Action'       : {'Format': '10s', 'DisplayOrder': 5, 'Heading': 'Action'}}

PoliciesFound = []
AllChildAccounts = []
# TODO: Will have to be changed to support single region-only accounts, but that's a ways off yet.
pRegionList = RegionList = ['us-east-1']

AllCredentials = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)

if pTiming:
	logging.info(f"{Fore.GREEN}Overhead consumed {time() - begin_time:.2f} seconds up till now{Fore.RESET}")

PoliciesFound.extend(check_accounts_for_policies(AllCredentials, RegionList, pAction, pFragment))
sorted_policies = sorted(PoliciesFound, key=lambda x: (x['MgmtAccount'], x['AccountNumber'], x['Region'], x['PolicyName']))
display_results(sorted_policies, display_dict, pAction)

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
print(f"These accounts were skipped - as requested: {pSkipAccounts}") if pSkipAccounts is not None else print()
print()
print(f"Found {len(PoliciesFound)} policies across {len(AllCredentials)} accounts across {len(RegionList)} regions\n"
	  f"	that matched the fragment{'s' if len(pFragment) > 1 else ''} that you specified: {pFragment}")
print()
print("Thank you for using this script")
print()
