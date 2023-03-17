#!/usr/bin/env python3

# import boto3
import Inventory_Modules
from Inventory_Modules import display_results
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

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
parser.rootOnly()
parser.fragment()
parser.verbosity()
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

display_dict = {'MgmtAccount'  : '12s',
				'AccountNumber': '12s',
				'Region'       : '15s',
				'PolicyName'   : '40s',
				'Action'       : '10s'}
PoliciesFound = []
AllChildAccounts = []
# TODO: Will have to be changed to support single region-only accounts, but that's a ways off yet.
pRegionList = RegionList = ['us-east-1']
subnet_list = []
AllCredentials = []

if pProfiles is None:  # Default use case from the classes
	print("Getting Accounts to check: ", end='')
	aws_acct = aws_acct_access()
	profile = 'default'
	# RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
	if pTiming:
		logging.info(f"{Fore.GREEN}Overhead consumed {time() - begin_time} seconds up till now{Fore.RESET}")
	# This should populate the list "AllCreds" with the credentials for the relevant accounts.
	logging.info(f"Queueing default profile for credentials")
	AllCredentials.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList))

else:
	ProfileList = Inventory_Modules.get_profiles(fSkipProfiles=pSkipProfiles, fprofiles=pProfiles)
	logging.warning(f"These profiles are being checked {ProfileList}.")
	print("Getting Accounts to check: ", end='')
	for profile in ProfileList:
		aws_acct = aws_acct_access(profile)
		# RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
		if pTiming:
			logging.info(f"{Fore.GREEN}Overhead consumed {time() - begin_time} seconds up till now{Fore.RESET}")
		logging.warning(f"Looking at {profile} account now across these regions {RegionList}... ")
		logging.info(f"Queueing {profile} for credentials")
		# This should populate the list "AllCreds" with the credentials for the relevant accounts.
		AllCredentials.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList))

PoliciesFound.extend(check_accounts_for_policies(AllCredentials, RegionList, pAction, pFragment))
display_results(PoliciesFound, display_dict, pAction)

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time} seconds{Fore.RESET}")
print(f"These accounts were skipped - as requested: {pSkipAccounts}") if pSkipAccounts is not None else print()
print()
print(f"Found {len(PoliciesFound)} policies across {len(AllCredentials)} accounts across {len(RegionList)} regions\n"
	  f"	that matched the fragment{s if len(pFragment) > 1 else ''} that you specified: {pFragment}")
print()
print("Thank you for using this script")
print()
