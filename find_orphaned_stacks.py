#!/usr/bin/env python3

import logging

from time import time

import simplejson as json
from botocore.exceptions import ClientError
from colorama import Fore, init

import Inventory_Modules
from Inventory_Modules import get_credentials_for_accounts_in_org, find_stacks2, find_stacksets3, find_stack_instances3, display_results
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access

import sys
from os.path import split

"""
This script was created to help solve a testing problem for the "move_stack_instances.py" script.
Originally, that script didn't have built-in recovery, so we needed this script to "recover" those stack-instance ids that might have been lost during the move_stack_instances.py run. However, that script now has built-in recovery, so this script isn't really needed. However, it can still be used to find any stack-instances that have been orphaned from their original stack-set, if that happens. 
"""

init()
__version__ = "2024.03.05"
ERASE_LINE = '\x1b[2K'
begin_time = time()
DefaultMaxWorkerThreads = 25


##################
# Functions
##################

def parse_args(args):
	"""
	Description: Parse the arguments sent to the script
	@param args: namespace of the arguments passed in at the command line
	@return: namespace with all parameters parsed out
	"""
	script_path, script_name = split(sys.argv[0])
	parser = CommonArguments()
	parser.singleregion()
	parser.singleprofile()
	parser.fragment()
	parser.extendedargs()
	parser.rolestouse()
	parser.save_to_file()
	parser.verbosity()
	parser.timing()
	parser.version(__version__)
	local = parser.my_parser.add_argument_group(script_name, 'Parameters specific to this script')
	local.add_argument(
		'-R', "--SearchRegions",
		help="The region(s) you want to search through to find orphaned stacksets.",
		default=['all'],
		nargs="*",
		metavar="region-name",
		dest="pRegionList")

	return (parser.my_parser.parse_args(args))


def print_timings(fTiming: bool = False, fverbose: int = 50, fmessage: str = None):
	"""
	Description: Prints how long it's taken in the script to get to this point...
	@param fTiming: Boolean as to whether we print anything
	@param fverbose: Verbosity to determine whether we print when user didn't specify any verbosity. This allows us to only print when they want more info.
	@param fmessage: The message to print out, when we print the timings.
	@return: None
	"""
	if fTiming and fverbose < 50:
		print(f"{Fore.GREEN}{fmessage}\n"
		      f"This script has taken {time() - begin_time:.6f} seconds so far{Fore.RESET}")


def setup_auth_and_regions(fProfile: str) -> (aws_acct_access, list):
	"""
	Description: This function takes in a profile, and returns the account object and the regions valid for this account / org.
	@param fProfile: A string representing the profile provided by the user. If nothing, then use the default profile or credentials
	@return:
		- an object of the type "aws_acct_access"
		- a list of regions valid for this particular profile/ account.
	"""
	try:
		aws_acct = aws_acct_access(fProfile)
	except ConnectionError as my_Error:
		logging.error(f"Exiting due to error: {my_Error}")
		sys.exit(8)

	AllRegions = Inventory_Modules.get_ec2_regions3(aws_acct)
	RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)

	if pRegion.lower() not in AllRegions:
		print()
		print(f"{Fore.RED}You specified '{pRegion}' as the region, but this script only works with a single region.\n"
		      f"Please run the command again and specify only a single, valid region{Fore.RESET}")
		print()
		sys.exit(9)

	print()
	# if pdelete:
	# 	action = "and delete"
	# elif pAddNew:
	# 	action = "and add to"
	# elif pRefresh:
	# 	action = "and refresh"
	# else:
	# 	action = "but not modify"
	print(f"You asked me to find orphaned stacksets that match the following:")
	print(f"\t\tIn the {aws_acct.AccountType} account {aws_acct.acct_number}")
	print(f"\t\tIn this home Region: {pRegion}")
	print(f"\t\tAcross regions that match this fragment: {pRegionList}") if pRegionList is not None else ''
	print(f"While skipping these accounts:\n{Fore.RED}{pSkipAccounts}{Fore.RESET}") if pSkipAccounts is not None else ''

	if pExact:
		print(f"\t\tFor stacksets that {Fore.RED}exactly match{Fore.RESET}: {pFragments}")
	else:
		print(f"\t\tFor stacksets that contain th{'is fragment' if len(pFragments) == 1 else 'ese fragments'}: {pFragments}")

	if pAccounts is None:
		print(f"\t\tFor stack instances across all accounts")
	else:
		print(f"\t\tSpecifically to find th{'ese' if len(pAccounts) > 1 else 'is'} account number{'s' if len(pAccounts) > 1 else ''}: {pAccounts}")
	# print(f"\t\tSpecifically to find th{'ese' if len(pRegionModifyList) > 1 else 'is'} region{'s' if len(pRegionModifyList) > 1 else ''}: {pRegionModifyList}") if pRegionModifyList is not None else ""
	print()
	return (aws_acct, RegionList)


def find_stacks_within_child_accounts(fall_credentials, fFragmentlist:list=None):
	from queue import Queue
	from threading import Thread

	class FindStacks(Thread):
		def __init__(self, fqueue: Queue):
			Thread.__init__(self)
			self.queue = fqueue

		def run(self):
			while True:
				# Get the next account from the queue
				c_credential, c_fragmentlist = self.queue.get()
				# Find the stacks in this account
				try:
					if c_credential['Success']:
						account_and_region_stacks = find_stacks2(c_credential, c_credential['Region'], c_fragmentlist)
						AllFoundStacks.extend(account_and_region_stacks)
					else:
						logging.info(f"Skipping {c_credential['AccountNumber']} in {c_credential['Region']} as we failed to successfully access")
				except Exception as my_Error:
					# ErrorMessage = my_Error.response['Error']['Message']
					logging.error(f"Error accessing account {c_credential['AccountId']} in region {c_credential['Region']} "
					              f"Skipping this account")
					logging.info(f"Actual Error: {my_Error}")
				finally:
					# Notify the queue that the job is done
					self.queue.task_done()

	# Create a queue to hold the threads
	checkqueue = Queue()
	if fFragmentlist is None:
		fFragmentlist = ['all']
	# This function takes the accounts and "SkipAccounts" that the user provided into account, so we don't have to filter any more than this.

	WorkerThreads = min(len(fall_credentials), DefaultMaxWorkerThreads)

	AllFoundStacks = []
	for x in range(WorkerThreads):
		worker = FindStacks(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	for credential in fall_credentials:
		logging.info(f"Queueing account {credential['AccountId']} and {credential['Region']}")
		try:
			# I don't know why - but double parens are necessary below. If you remove them, only the first parameter is queued.
			checkqueue.put((credential, fFragmentlist))
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']}")
				logging.warning(f"It's possible that the region {credential['Region']} hasn't been opted-into")
				pass
	checkqueue.join()
	return (AllFoundStacks)


def reconcile_between_parent_stacksets_and_children_stacks(f_parent_stack_instances:list, f_child_stacks:list):
	child_comparisons = 0
	parent_comparisons = 0
	i = 0
	for ParentInstance in f_parent_stack_instances:
		parent_comparisons += 1
		for Childinstance in f_child_stacks:
			child_comparisons += 1
			if 'StackId' in ParentInstance.keys() and Childinstance['StackId'] == ParentInstance['StackId']:
				i += 1
				logging.debug(f"**** Match {i}!! **** - {time() - begin_time:.6f}")
				logging.debug(f"Childinstance: {Childinstance['StackId']}")
				logging.debug(f"ParentInstance:  {ParentInstance['StackId']}")
				Childinstance['Matches'] = ParentInstance['StackId']
				ParentInstance['Matches'] = Childinstance['StackId']
			else:
				continue
	print_timings(pTiming, verbose, f"We compared {len(AllChildStackInstances)} child stacks against {len(AllParentStackInstancesInStackSets)} parent stack instances")
	# Filter out any instances that have a 'Match' in the Children
	Parent_Instances_Not_In_Children_Stacks = [x for x in AllParentStackInstancesInStackSets if 'Matches' not in x.keys()]
	# Filter out any instances that have a 'Match' in the Parent, as well as any that are regular account stacks
	Child_Instances_Not_In_Parent_Stacks = [x for x in AllChildStackInstances if 'Matches' not in x.keys() and (x['StackName'].find('StackSet-') > -1)]
	print()
	print(f"We found {len(Parent_Instances_Not_In_Children_Stacks)} parent stack instances that are not in the child stacks")
	print(f"We found {len(Child_Instances_Not_In_Parent_Stacks)} child stacks that are not in the parent stacksets")
	print()
	if verbose < 50:
		parent_display_dict = {'Account'     : {'DisplayOrder': 1, 'Heading': 'Acct Number'},
		                       'Region'      : {'DisplayOrder': 2, 'Heading': 'Region'},
		                       'StackSetId'  : {'DisplayOrder': 3, 'Heading': 'StackSet Id'},
		                       'Status'      : {'DisplayOrder': 4, 'Heading': 'Status'},
		                       'StatusReason': {'DisplayOrder': 5, 'Heading': 'Possible Reason'}}
		print(f"Stack Instances in the Root Account that don't appear in the Children")
		sorted_Parent_Instances_Not_In_Children_Stacks = sorted(Parent_Instances_Not_In_Children_Stacks, key=lambda k: (k['Account'], k['Region'], k['StackSetId']))
		display_results(sorted_Parent_Instances_Not_In_Children_Stacks, parent_display_dict, None, f"{pFilename}-Parent")
		child_display_dict = {'AccountNumber': {'DisplayOrder': 1, 'Heading': 'Acct Number'},
		                      'Region'       : {'DisplayOrder': 2, 'Heading': 'Region'},
		                      'StackName'    : {'DisplayOrder': 3, 'Heading': 'Stack Name'},
		                      'StackStatus'  : {'DisplayOrder': 4, 'Heading': 'Status'}}
		print(f"Stacks in the Children accounts that don't appear in the Root Stacksets")
		sorted_Child_Instances_Not_In_Parent_Stacks = sorted(Child_Instances_Not_In_Parent_Stacks, key=lambda k: (k['AccountNumber'], k['Region'], k['StackName']))
		display_results(sorted_Child_Instances_Not_In_Parent_Stacks, child_display_dict, None, f"{pFilename}-Child")


##################
# Main
##################

if __name__ == '__main__':
	args = parse_args(sys.argv[1:])
	pProfile = args.Profile
	pRegion = args.Region
	pRegionList = args.pRegionList
	pAccounts = args.Accounts
	pSkipAccounts = args.SkipAccounts
	pSkipProfiles = args.SkipProfiles
	pFilename = args.Filename
	pRootOnly = False
	pExact = args.Exact
	pRoles = args.AccessRoles
	verbose = args.loglevel
	pTiming = args.Time
	pFragments = args.Fragments
	logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")

	ERASE_LINE = '\x1b[2K'
	# aws_acct = aws_acct_access(pProfile)
	begin_time = time()
	ChildAccounts = []

	# Setup credentials and regions (filtered by what they wanted to check)
	aws_acct, RegionList = setup_auth_and_regions(pProfile)
	# Determine the accounts we're checking
	print_timings(pTiming, verbose, "Just setup account and region list")
	if pAccounts is None:
		ChildAccounts = aws_acct.ChildAccounts
	else:
		for account in aws_acct.ChildAccounts:
			if account['AccountId'] in pAccounts:
				ChildAccounts.append({'AccountId'    : account['AccountId'],
				                      'AccountEmail' : account['AccountEmail'],
				                      'AccountStatus': account['AccountStatus'],
				                      'MgmtAccount'  : account['MgmtAccount']})
	AccountList = [account['AccountId'] for account in ChildAccounts]
	AllCredentials = get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, AccountList, pProfile, RegionList, pRoles, pTiming)
	print_timings(pTiming, verbose, f"Finished getting {len(AllCredentials)} credentials for all accounts and regions in spec...")
	pRootOnly = False  # It doesn't make any sense to think that this script would be used for only the root account

	# Connect to every account, and in every region specified, to find all stacks
	print(f"Now finding all stacks across {'all' if pAccounts is None else (len(pAccounts) * len(RegionList))} accounts and regions under the {aws_acct.AccountType} account {aws_acct.acct_number}")
	AllChildStackInstances = find_stacks_within_child_accounts(AllCredentials, pFragments)
	print_timings(pTiming, verbose, f"Just finished getting {len(AllChildStackInstances)} children stack instances")
	# and then compare them with the stackset instances managed within the Root account, and find anything that doesn't match

	# This is the list of stacksets in the root account
	AllParentStackSets = find_stacksets3(aws_acct, pRegion, pFragments, pExact)
	print_timings(pTiming, verbose, f"Just finished getting {len(AllParentStackSets['StackSets'])} parent stack sets")
	print(f"Now getting all the stack instances for all {len(AllParentStackSets)} stacksets")
	# This will be the listing of the stack_instances in each of the stacksets in the root account
	AllParentStackInstancesInStackSets = []
	for stackset_name, stackset_attributes in AllParentStackSets['StackSets'].items():
		StackInstancesInStackSets = find_stack_instances3(aws_acct, pRegion, stackset_name, faccountlist=AccountList, fregionlist=RegionList)
		# TODO: Filter out skipped / closed accounts within the stacksets
		AllParentStackInstancesInStackSets.extend(StackInstancesInStackSets)
	print_timings(pTiming, verbose, f"Just finished getting {len(AllParentStackInstancesInStackSets)} parent stack instances")
	# Then compare the stack_instances in the root account with the stack_instances in the child accounts to see if anything is missing
	print(f"We found {len(AllChildStackInstances)} stack instances in the {len(AccountList)} child accounts")
	print(f"We found {len(AllParentStackInstancesInStackSets)} stack instances in the {len(AllParentStackSets['StackSets'])} stacksets in the root account")
	print(f"Now cross-referencing these to find if there are any orphaned stacks...")
	# Find the stacks that are in the root account but not in the child accounts
	# And find any stack instances in the children accounts that are not in the root account
	# And display them to the screen...
	reconcile_between_parent_stacksets_and_children_stacks(AllParentStackInstancesInStackSets, AllChildStackInstances)

	if pTiming:
		print(ERASE_LINE)
		print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")

	print()
	print("Thanks for using this script...")
	print()
