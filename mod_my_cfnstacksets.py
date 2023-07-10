#!/usr/bin/env python3

import logging
import sys
import Inventory_Modules
from Inventory_Modules import display_results
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore, Style
from queue import Queue
from threading import Thread
from time import sleep, time
from botocore.exceptions import ClientError

'''
	- There are four possible use-cases when trying to modify or remove a stack instance from a stack set:
		- The stack exists as an association within the stackset AND it exists within the child account (typical)
			- We should remove the stackset-association with "--RetainStacks=False" and that will remove the child stack in the child account.
		- The stack exists as an association within the stackset, but has been manually deleted within the child account
			- If we remove the stackset-association with "--RetainStacks=False", it won't error, even when the stack doesn't exist within the child.
			- There is a special use case here where the child account has been deleted or suspended. This is a difficult use-case to test12.
		- The stack doesn't exist within the stackset association, but DOES exist within the child account (because its association was removed from the stackset)
			- The only way to remove this is to remove the stack from the child account. This would have to be done after having found the stack within the child account. This will be a ToDo for later...
		- The stack doesn't exist within the child account, nor within the stack-set
			- Nothing to do here
			
TODO:
	- Pythonize the whole thing
	- More Commenting throughout script
	- Make deleting multiple closed accounts easier - needs a parameter that comprises "+delete +force -A -check" all in one - to remove all closed accounts at one time... 
	- Add a stackset status, instead of just the status for the instances
	- Add a "tail" option, so it runs over and over until the stackset is finished
	- Make sure that the part where it removes stack instances and WAITS till they're done it working... 
'''

init()

__version__ = "2023.06.15"

parser = CommonArguments()
parser.singleprofile()
parser.singleregion()
# This next parameter includes picking a specific account, ignoring specific accounts or profiles
parser.extendedargs()
parser.fragment()
# This next parameter includes *forcing* an operation
parser.deletion()
parser.roletouse()
# parser.save_to_file()
parser.timing()
parser.verbosity()
parser.version(__version__)
group = parser.my_parser.add_mutually_exclusive_group()
group.add_argument(
	'-R', "--RemoveRegion",
	help="The region(s) you want to remove from all the stacksets.",
	default=None,
	nargs="*",
	metavar="region-name",
	dest="pRegionRemove")
group.add_argument(
	"+refresh",
	help="Use this parameter is you want to re-run the same stackset, over again",
	action="store_true",
	dest="Refresh")
parser.my_parser.add_argument(
	'-check',
	help="Do a comparison of the accounts found in the stacksets to the accounts found in the Organization and list out any that have been closed or suspended, but never removed from the stacksets.",
	action="store_true",
	dest="AccountCheck")
parser.my_parser.add_argument(
	'+delete',
	help="[Default] Do a Dry-run; if this parameter is specified, we'll delete stacksets we find, with no additional confirmation.",
	action="store_true",
	dest="DryRun")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Region
pStackfrag = args.Fragments
pExact = args.Exact
pTiming = args.Time
pAccountRemoveList = args.Accounts
verbose = args.loglevel
pCheckAccount = args.AccountCheck
pRole = args.AccessRole
pdelete = args.DryRun
pRegionRemove = args.pRegionRemove
pRefresh = args.Refresh
pForce = args.Force
# pSaveFilename = args.Filename
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

# Seems low, but this fits under the API threshold. Make it too high and it will not.
DefaultMaxWorkerThreads = 5


###################

def find_stack_set_instances(fStackSetNames, fRegion):
	"""
	Note that this function takes a list of stack set names and finds the stack instances within them
	"""

	class FindStackSets(Thread):

		def __init__(self, queue):
			Thread.__init__(self)
			self.queue = queue

		def run(self):
			while True:
				# Get the work from the queue and expand the tuple
				c_stacksetname, c_region, c_stackset_info, c_PlaceCount = self.queue.get()
				logging.info(f"De-queued info for stack set name {c_stacksetname}")
				try:
					# Now go through those stacksets and determine the instances, made up of accounts and regions
					# Most time spent in this loop
					# for i in range(len(fStackSetNames['StackSets'])):
					print(f"{ERASE_LINE}Looking through {c_PlaceCount} of {len(fStackSetNames)} stacksets found with {pStackfrag} string in them", end='\r')
					# TODO: Creating the list to delete this way prohibits this script from including stacksets that are already empty. This should be fixed.
					StackInstances = Inventory_Modules.find_stack_instances3(aws_acct, c_region, c_stacksetname)
					logging.warning(f"Found {len(StackInstances)} Stack Instances within the StackSet {c_stacksetname}")
					if len(StackInstances) == 0 and pdelete and pAccountRemoveList is None and pRegionRemove is None:
						# logging.warning(f"While we didn't find any stack instances within {fStackSetNames['StackSets'][i]['StackSetName']}, we assume you want to delete it, even when it's empty")
						logging.warning(f"While we didn't find any stack instances within {c_stacksetname}, we assume you want to delete it, even when it's empty")
						f_combined_stack_set_instances.append({
							'ParentAccountNumber': aws_acct.acct_number,
							'ChildAccount'       : None,
							'ChildRegion'        : None,
							'PermissionModel'    : c_stackset_info['PermissionModel'] if 'PermissionModel' in c_stackset_info else None,
							'StackStatus'        : None,
							'StackSetName'       : c_stacksetname
						})
					for StackInstance in StackInstances:
						if 'StackId' not in StackInstance.keys():
							logging.info(f"The stack instance found {StackInstance} doesn't have a stackid associated. Which means it's never been deployed and probably OUTDATED")
							pass
						if pAccountRemoveList is None or StackInstance['Account'] in pAccountRemoveList:
							# This stack instance will be reported if it matches the account they provided,
							# or reported on if they didn't provide an account list at all.
							# OR - it will be removed if they also provided the "+delete" parameter...
							logging.debug(f"This is Instance #: {str(StackInstance)}")
							logging.debug(f"This is instance status: {str(StackInstance['Status'])}")
							logging.debug(f"This is ChildAccount: {StackInstance['Account']}")
							logging.debug(f"This is ChildRegion: {StackInstance['Region']}")
							# logging.debug("This is StackId: %s", str(StackInstance['StackId']))

							if pRegionRemove is None or (StackInstance['Region'] in RegionList):
								f_combined_stack_set_instances.append({
									'ParentAccountNumber' : aws_acct.acct_number,
									'ChildAccount'        : StackInstance['Account'],
									'ChildRegion'         : StackInstance['Region'],
									'StackStatus'         : StackInstance['Status'],
									'DetailedStatus'      : StackInstance['StackInstanceStatus']['DetailedStatus'],
									'OrganizationalUnitId': StackInstance['OrganizationalUnitId'] if 'OrganizationalUnitId' in StackInstance else None,
									'PermissionModel'     : c_stackset_info['PermissionModel'] if 'PermissionModel' in c_stackset_info else 'SELF_MANAGED',
									'StackSetName'        : c_stacksetname
								})
						elif not (StackInstance['Account'] in pAccountRemoveList):
							# If the user only wants to remove the stack instances associated with specific accounts,
							# then we only want to capture those stack instances where the account number shows up.
							# The following code captures this scenario
							logging.debug(f"Found a stack instance, but the account didn't match {pAccountRemoveList}... exiting")
							continue
				except KeyError as my_Error:
					logging.error(f"Account Access failed - trying to access {c_stacksetname}")
					logging.info(f"Actual Error: {my_Error}")
					pass
				except AttributeError as my_Error:
					logging.error(f"Error: Likely that one of the supplied profiles was wrong")
					logging.info(f"Actual Error: {my_Error}")
					continue
				except ClientError as my_Error:
					logging.error(f"Error: Likely throttling errors from too much activity")
					logging.info(f"Actual Error: {my_Error}")
					continue
				finally:
					print(f"{ERASE_LINE}Finished finding stack instances in stackset {c_stacksetname} in region {c_region} - {c_PlaceCount} / {len(fStackSetNames)}", end='\r')
					self.queue.task_done()

	###########

	if fRegion is None:
		fRegion = 'us-east-1'
	checkqueue = Queue()

	f_combined_stack_set_instances = []
	PlaceCount = 0
	WorkerThreads = min(len(fStackSetNames), DefaultMaxWorkerThreads)

	for x in range(WorkerThreads):
		worker = FindStackSets(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	for stacksetname in fStackSetNames:
		logging.debug(f"Beginning to queue data - starting with {stacksetname['StackSetName']}")
		try:
			# I don't know why - but double parens are necessary below. If you remove them, only the first parameter is queued.
			PlaceCount += 1
			checkqueue.put((stacksetname['StackSetName'], fRegion, stacksetname, PlaceCount))
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing stack set {stacksetname['StackSetName']} in {fRegion} region")
				logging.warning(f"It's possible that the region {fRegion} hasn't been opted-into")
				pass
	checkqueue.join()
	return (f_combined_stack_set_instances)


def random_string(stringLength=10):
	import random
	import string
	# Generate a random string of fixed length
	letters = string.ascii_lowercase
	randomstring = (''.join(random.choice(letters) for _ in range(stringLength)))
	return (randomstring)


def _delete_stack_instances(faws_acct, fRegion, fStackSetName, fForce, fAccountList=None, fRegionList=None, fPermissionModel='SELF_MANAGED', fDeploymentTargets=None):
	"""
	Required Parameters:
	faws_acct - the object containing the account credentials and such
	fRegion - the region we're looking to make changes in
	fAccountList - this is the listing of accounts that were FOUND to be within stack instances
	fRegionList - The list of regions within the stackset to remove as well
	fStackSetName - the stackset we're removing stack instances from
	fForce - By passing a "True" here, the API will pass on "RetainStacks" to the child stack - which will allow the stackset to be deleted more easily,
	 	but also leaves a remnant in the child account to clean up later..
	fPermissionModel - Whether the StackSet is using SELF_MANAGED or SERVICE_MANAGED permission model (associating the stack with individual accounts, or with an OU itself)
	fDeploymentTargets - When fPermissionModel is 'SELF_MANAGED', this should be None.
						When fPermissionModel is 'SERVICE_MANAGED', this is a dictionary specifying which OUs, or accounts should be impacted"
	"""
	logging.info(f"Removing instances from {fStackSetName} StackSet")
	StackSetOpId = f"DeleteInstances-{random_string(5)}"
	if ((fAccountList is None or fAccountList == []) and fPermissionModel.upper() == 'SELF_MANAGED') or (fRegionList is None or fRegionList == []):
		logging.error(f"AccountList and RegionList cannot be null")
		logging.warning(f"AccountList: {fAccountList}")
		logging.warning(f"RegionList: {fRegionList}")
		# Note: The "Success" is True below to show that the calling function can move forward, even though the Account / Regions are null
		return_response = {'Success': True, 'ErrorMessage': "Failed - Account List or Region List was null"}
		return (return_response)
	elif fPermissionModel == 'SERVICE_MANAGED' and fDeploymentTargets is None:
		logging.error(f"You can't provide a stackset that is self-managed, and not supply the deployment targets it's supposed to delete")
		# Note: The "Success" is True below to show that the calling function can move forward, even though the Account / Regions are null
		return_response = {'Success': False, 'ErrorMessage': "Failed - StackSet is 'Service_Managed' but no deployment target was provided"}
		return (return_response)
	# if fPermissionModel == 'SELF_MANAGED':
	try:
		# def delete_stack_instances3(faws_acct, fRegion, lRegions, fStackSetName, fRetainStacks=False,
		# 							fOperationName=None, lAccounts=None, fPermissionModel='SELF', fDeploymentTarget=None)
		delete_stack_instance_response = Inventory_Modules.delete_stack_instances3(faws_acct, fRegion, fRegionList, fStackSetName, fForce, StackSetOpId,
		                                                                           fAccountList, fPermissionModel, fDeploymentTargets)
		if delete_stack_instance_response['Success']:
			return_response = {'Success': True, 'OperationId': delete_stack_instance_response['OperationId']}
		else:
			return_response = {'Success': False, 'ErrorMessage': delete_stack_instance_response['ErrorMessage']}
		return (return_response)
	except Exception as my_Error:
		print(my_Error)
		if my_Error.response['Error']['Code'] == 'StackSetNotFoundException':
			logging.info("Caught exception 'StackSetNotFoundException', ignoring the exception...")
			return_response = {'Success': False, 'ErrorMessage': "Failed - StackSet not found"}
			return (return_response)
		# except  as my_Error:
		# 	print(my_Error)
		# 	if my_Error.response['Error']['Code'] == 'StackSetNotFoundException':
		# 		logging.info("Caught exception 'StackSetNotFoundException', ignoring the exception...")
		# 		return_response = {'Success': False, 'ErrorMessage': "Failed - StackSet not found"}
		# 		return (return_response)
		else:
			print("Failure to run: ", my_Error)
			return_response = {'Success': False, 'ErrorMessage': "Failed-Other"}
			return (return_response)


def display_stack_set_health(fcombined_stack_set_instances, fAccountList):
	summary = {}
	stack_set_permission_models = dict()
	for record in fcombined_stack_set_instances:
		if fAccountList is not None and record['ChildAccount'] in fAccountList:
			continue
		stack_set_name = record['StackSetName']
		stack_status = record['StackStatus']
		detailed_status = record['DetailedStatus']
		stack_region = record['ChildRegion']
		ou = record['OrganizationalUnitId']
		stack_set_permission_models.update({stack_set_name: record['PermissionModel']})
		if stack_set_name not in summary:
			summary[stack_set_name] = {}
		if stack_status not in summary[stack_set_name]:
			summary[stack_set_name][stack_status] = []
		summary[stack_set_name][stack_status].append({'Account': record['ChildAccount'], 'Region': stack_region, 'DetailedStatus': detailed_status})
	# print(fmt % (stack_set_name, record['ChildAccount'], stack_region, stack_status, detailed_status))

	# Print the summary
	print()
	for stack_set_name, status_counts in summary.items():
		print(f"{stack_set_name} ({stack_set_permission_models[stack_set_name]}):")
		for stack_status, instances in status_counts.items():
			print(f"\t{Fore.RED if stack_status != 'CURRENT' else ''}{stack_status}: {len(instances)} instances {Fore.RESET}")
			if verbose < 50:
				stack_instances = {}
				for stack_instance in instances:
					if stack_instance['Account'] not in stack_instances.keys():
						stack_instances[stack_instance['Account']] = []
					stack_instances[stack_instance['Account']].append(stack_instance['Region'])
				for k, v in stack_instances.items():
					if k in RemovedAccounts:
						print(f"{Style.BRIGHT}{Fore.MAGENTA}\t\t{k}: {v}{Style.RESET_ALL}\t <----- Look here for orphaned accounts! ")
					else:
						print(f"\t\t{k}: {v}")


def get_stack_set_deployment_target_info(faws_acct, fRegion, fStackSetName, fAccountRemovalList=None):
	"""
	Required Parameters:
	faws_acct - the object containing the account credentials and such
	fRegion - the region we're looking to make changes in
	fStackSetName - the stackset we're removing stack instances from
	fAccountRemvalList - The list of accounts they may have provided to limit the deletion to
	"""
	return_result = {'Success': False, 'ErrorMessage': None, 'Results': None}
	if fAccountRemovalList is None:
		deployment_results = Inventory_Modules.find_stack_instances3(faws_acct, fRegion, fStackSetName)
		identified_ous = list(set([x['OrganizationalUnitId'] for x in deployment_results]))
		DeploymentTargets = {
			# 'Accounts'             : [
			# 	'string',
			# ],
			# 'AccountsUrl'          : 'string',
			'OrganizationalUnitIds': identified_ous
			# 'AccountFilterType'    : 'NONE' | 'INTERSECTION' | 'DIFFERENCE' | 'UNION'
		}
	else:
		DeploymentTargets = {
			'Accounts': fAccountRemovalList,
			# 'AccountsUrl'          : 'string',
			# 'OrganizationalUnitIds': identified_ous
			# 'AccountFilterType'    : 'NONE' | 'INTERSECTION' | 'DIFFERENCE' | 'UNION'
		}
	return_result.update({'Success': True, 'ErrorMessage': None, 'Results': DeploymentTargets})
	return (return_result)


##########################


if pTiming:
	begin_time = time()

ERASE_LINE = '\x1b[2K'
sleep_interval = 5

try:
	aws_acct = aws_acct_access(pProfile)
except ConnectionError as my_Error:
	logging.error(f"Exiting due to error: {my_Error}")
	sys.exit(8)

AllRegions = Inventory_Modules.get_ec2_regions()

if pRegion.lower() not in AllRegions:
	print()
	print(f"{Fore.RED}You specified '{pRegion}' as the region, but this script only works with a single region.\n"
	      f"Please run the command again and specify only a single, valid region{Fore.RESET}")
	print()
	sys.exit(9)

print()
print(f"You asked me to find {'(and delete)' if pdelete else '(but not delete)'} stacksets that match the following:")
print(f"\t\tIn the {aws_acct.AccountType} account {aws_acct.acct_number}")
print(f"\t\tIn this Region: {pRegion}")

RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionRemove)

if pRegionRemove is None:
	print(f"\t\tFor stack instances across all enabled Regions")
else:
	print(f"\t\tLimiting instance targets to Region{'s' if len(RegionList) > 1 else ''}: {RegionList}")

if pExact:
	print(f"\t\tFor stacksets that {Fore.RED}exactly match{Fore.RESET} these fragments: {pStackfrag}")
else:
	print(f"\t\tFor stacksets that contains these fragments: {pStackfrag}")
# print(f"\t\tFor stack instances that match this status: {}".format(pstatus))

print(f"\t\tSpecifically to find th{'ese' if len(pAccountRemoveList) > 1 else 'is'} account number{'s' if len(pAccountRemoveList) > 1 else ''}: {pAccountRemoveList}") if pAccountRemoveList is not None else ""
print(f"\t\tWe'll also display those accounts in the stacksets that are no longer part of the organization") if pCheckAccount else ""
print(f"\t\tWe'll refresh the stackset with fragments {pStackfrag}") if pRefresh else ""
print()

# Get the StackSet names from the Management Account
StackSetNames = Inventory_Modules.find_stacksets3(aws_acct, pRegion, pStackfrag, pExact)
if not StackSetNames['Success']:
	logging.error("Something went wrong with the AWS connection. Please check the parameters supplied and try again.")
	sys.exit(StackSetNames)
logging.info(f"Found {len(StackSetNames['StackSets'])} StackSetNames that matched your fragment")

combined_stack_set_instances = find_stack_set_instances(StackSetNames['StackSets'], pRegion)

print(ERASE_LINE)
logging.info(f"Found {len(combined_stack_set_instances)} stack instances.")

AccountList = []
ApplicableStackSetsList = []
FoundRegionList = []

for _ in range(len(combined_stack_set_instances)):
	if pAccountRemoveList is None:  # Means we want to not remove anything
		ApplicableStackSetsList.append(combined_stack_set_instances[_]['StackSetName'])
		AccountList.append(combined_stack_set_instances[_]['ChildAccount'])
		FoundRegionList.append(combined_stack_set_instances[_]['ChildRegion'])
	elif pAccountRemoveList is not None:
		if combined_stack_set_instances[_]['ChildAccount'] in pAccountRemoveList:
			ApplicableStackSetsList.append(combined_stack_set_instances[_]['StackSetName'])
			AccountList.append(combined_stack_set_instances[_]['ChildAccount'])
			FoundRegionList.append(combined_stack_set_instances[_]['ChildRegion'])

# I had to add this list comprehension to filter out the "None" types that happen when there are no stack-instances within a stack-set
AccountList = sorted(list(set([item for item in AccountList if item is not None])))
# RegionList isn't specific per account, as the deletion API doesn't need it to be, and it's easier to keep a single list of all regions, instead of per StackSet
# TODO: Since we allow this now, should we revisit this?
# If we update this script to allow the removal of individual regions as well as individual accounts, then we'll do that.
FoundRegionList = sorted(list(set([item for item in FoundRegionList if item is not None])))

ApplicableStackSetsList = sorted(list(set(ApplicableStackSetsList)))
RemovedAccounts = []

if pCheckAccount:
	OrgAccountList = [i['AccountId'] for i in aws_acct.ChildAccounts]
	print("Displaying accounts within the stacksets that aren't a part of the Organization")
	logging.info(f"There are {len(OrgAccountList)} accounts in the Org, and {len(AccountList)} unique accounts in all stacksets found")
	RemovedAccounts = list(set(AccountList) - set(OrgAccountList))
	InaccessibleAccounts = []
	for accountnum in AccountList:
		if verbose < 50:
			print(f"{ERASE_LINE}Trying to gain access to account number {accountnum}", end='\r')
		my_creds = Inventory_Modules.get_child_access3(aws_acct, accountnum)
		if my_creds['AccessError']:
			InaccessibleAccounts.append({'AccountId' : accountnum,
			                             'Success'   : my_creds['Success'],
			                             'RolesTried': my_creds['RolesTried']})
	print()
	logging.info(f"Found {len(InaccessibleAccounts) + len(RemovedAccounts)} accounts that don't belong")
	print(f"There were {len(RemovedAccounts)} accounts found in the {len(StackSetNames['StackSets'])} Stacksets we looked through, that are not a part of the Organization")
	print(f"There are {len(InaccessibleAccounts)} accounts that appear inaccessible, using typical role names")
	for item in RemovedAccounts:
		print(f"Account {item} is not in the Organization")
	for item in InaccessibleAccounts:
		print(f"Account {item['AccountId']} is unreachable using these roles:\n"
		      f"\t\t{item['RolesTried']}")
	print()

'''
The next section is broken up into a few pieces. I should try to re-write this to make it easier to read, but I decided to comment here instead.

* if pdryrun and pAccountRemoveList==None
 - This handles the scenario where we're doing a read-only run, and we didn't provide a specific Account that we're interested in.
 - This should be the normal case - where we're just doing a generic read of all stacksets in an account.
 - By default, it will print out the last line - summarizing everything found.
 - If you have additional verbosity set, it will print out a list of stacksets found, and a list of the accounts with the regions enabled by the stacksets,
* if pdryrun (which means you DID specify a specific account you're looking for)
 - It will print that it found that account associated with X number of stacksets.
 - If you have additional verbosity set, it will print out which stacksets that account is associated with, and which regions.
* If this is NOT a dry-run (meaning you want to take action on the stacksets) and it's not a REFRESH
 - We assume you're looking to remove accounts from a specific stackset
 - We ask whether you're sure if you want to remove the account, unless you've also supplied the "+force" parameter, which bypasses the extra check
	* If you didn't supply the Account Number
	 - then we assume you wanted to remove the stack instances from the stackset(s)
	 - except we previously allowed certain accounts to be "skipped", so we need to make sure we're skipping those accounts when we remove stack instances from these stacksets.
* If this is NOT a dry-run (meaning you want to take action) but it IS a REFRESH
 - We're going to go through all stacksets you selected, 
 - Find out the existing information on them, and hold that 
 - Then try to UPDATE that stackset, supplying the same information back to the stackset as the original, to ensure as little change as possible. 
'''

# TODO: Update this to make it more readable
if not pdelete and pAccountRemoveList is None:
	print(f"Found {len(StackSetNames['StackSets'])} StackSets that matched, with {len(combined_stack_set_instances)} total instances across {len(AccountList)} accounts, across {len(FoundRegionList)} regions")
	print(f"We found the following StackSets with the fragment you provided {pStackfrag}:")
	display_stack_set_health(combined_stack_set_instances, pAccountRemoveList)
elif not pdelete:
	display_dict = {'StackSetName'  : {'DisplayOrder': 1, 'Heading': 'Stack Set Name'},
	                'ChildAccount'  : {'DisplayOrder': 2, 'Heading': 'Acct Number'},
	                'ChildRegion'   : {'DisplayOrder': 3, 'Heading': 'Region'},
	                'DetailedStatus': {'DisplayOrder': 4, 'Heading': 'Instance Status', 'Condition': ['FAILED', 'INOPERABLE', 'SKIPPED_SUSPENDED_ACCOUNT', 'CANCELLED']}}
	print()
	print(f"We found that stacks that match these accounts {pAccountRemoveList} show up in these regions:")
	display_results(combined_stack_set_instances, display_dict, 'None')
	# for i in range(len(combined_stack_set_instances)):
	# 	if combined_stack_set_instances[i]['ChildAccount'] in pAccountRemoveList:
	# 		print(f"\t{combined_stack_set_instances[i]['StackSetName']} \t {combined_stack_set_instances[i]['ChildRegion']} \t {combined_stack_set_instances[i]['ChildAccount']} \t {combined_stack_set_instances[i]['DetailedStatus']}")

if pdelete and not pRefresh:
	print()
	print(f"Removing {len(combined_stack_set_instances)} stack instances from the {len(StackSetNames['StackSets'])} StackSets found")
	StackInstanceItem = 0
	for StackSet in StackSetNames['StackSets']:
		StackSetName = StackSet['StackSetName']
		StackInstanceItem += 1
		print(f"Now deleting stackset instances in {StackSetName}. {StackInstanceItem} of {len(ApplicableStackSetsList)} done")
		# TODO: This needs to be wrapped in a try...except
		# Determine what kind of stackset this is - Self-Managed, or Service-Managed.
		# We need to check to see if the 'PermissionModel' key in in the dictionary, since it's only in the dictionary if the permission is 'service_managed',
		# but I'm not willing to be it stats that way...
		if 'PermissionModel' in StackSet.keys() and StackSet['PermissionModel'] == 'SERVICE_MANAGED':
			"""
			If the StackSet is SERVICE-MANAGED, we need to find more information about the stackset than is returned in the "list-stack-set" call from above
			"""
			if pAccountRemoveList is None:
				DeploymentTargets = get_stack_set_deployment_target_info(aws_acct, pRegion, StackSetName)
			else:
				DeploymentTargets = get_stack_set_deployment_target_info(aws_acct, pRegion, StackSetName, pAccountRemoveList)
			if FoundRegionList is None:
				print(f"There appear to be no stack instances for this stack-set")
				continue
			# TODO:
			#  Have to rethink this part - since we have to be careful how we remove specific accounts or OUs in Service-Managed Stacks
			if pAccountRemoveList is None:  # Remove all instances from the stackset
				if pRegionRemove is not None:
					print(f"About to update stackset {StackSetName} to remove all accounts within {str(FoundRegionList)}")
					RemoveStackSet = False
				else:
					print(f"About to update stackset {StackSetName} to remove ALL accounts from all regions")
					RemoveStackSet = True
			# RemoveStackInstanceResult = _delete_stack_instances(aws_acct, pRegion, AccountList, FoundRegionList, StackSetName, pForce)
			else:
				print(f"About to remove account {pAccountRemoveList} from stackset {StackSetName} in regions {str(FoundRegionList)}")
				RemoveStackSet = False
			RemoveStackInstanceResult = _delete_stack_instances(aws_acct, pRegion, StackSetName, pForce, AccountList,
			                                                    FoundRegionList, StackSet['PermissionModel'], DeploymentTargets['Results'])
		else:
			if FoundRegionList is None:
				print(f"There appear to be no stack instances for this stack-set")
				continue
			if pAccountRemoveList is None:  # Remove all instances from the stackset
				if pRegionRemove is not None:
					logging.error(f"About to update stackset {StackSetName} to remove all accounts within {str(FoundRegionList)}")
					RemoveStackSet = False
				else:
					logging.info(f"About to update stackset {StackSetName} to remove ALL accounts from all regions")
					RemoveStackSet = True
			# RemoveStackInstanceResult = _delete_stack_instances(aws_acct, pRegion, AccountList, FoundRegionList, StackSetName, pForce)
			else:
				logging.info(f"About to remove account {pAccountRemoveList} from stackset {StackSetName} in regions {str(FoundRegionList)}")
				RemoveStackSet = False
			RemoveStackInstanceResult = _delete_stack_instances(aws_acct, pRegion, StackSetName, pForce, AccountList, FoundRegionList)
		if RemoveStackInstanceResult['Success']:
			Instances = [item for item in combined_stack_set_instances if item['StackSetName'] == StackSetName]
			print(f"{ERASE_LINE}Successfully initiated removal of {len(Instances)} instances from StackSet {StackSetName}")
		elif RemoveStackInstanceResult['ErrorMessage'] == 'Failed-ForceIt' and pForce:
			print("We tried to force the deletion, but some other problem happened.")
		elif RemoveStackInstanceResult['ErrorMessage'] == 'Failed-ForceIt' and not pForce:
			Decision = (input("Deletion of Stack Instances failed, but might work if we force it. Shall we force it? (y/n): ") in ['y', 'Y'])
			if Decision:
				RemoveStackInstanceResult = _delete_stack_instances(aws_acct, pRegion, StackSetName, True, AccountList, FoundRegionList)  # Try it again, forcing it this time
				if RemoveStackInstanceResult['Success']:
					print(f"{ERASE_LINE}Successfully retried StackSet {StackSetName}")
				elif pForce is True and RemoveStackInstanceResult['ErrorMessage'] == 'Failed-ForceIt':
					print(f"{ERASE_LINE}Some other problem happened on the retry.")
				elif RemoveStackInstanceResult['ErrorMessage'] == 'Failed-Other':
					print(f"{ERASE_LINE}Something else failed on the retry... Please report the error received.")
		elif str(RemoveStackInstanceResult['ErrorMessage']).find('OperationInProgressException') > 0:
			print(f"{Fore.RED}Another operation is running on this StackSet... Please wait for that operation to end and re-run this script{Fore.RESET}")
			sys.exit(RemoveStackInstanceResult['ErrorMessage'])
		else:
			# elif RemoveStackInstanceResult['ErrorMessage'] == 'Failed-Other':
			print(f"{Fore.RED}Something else failed... Please report the error below{Fore.RESET}")
			logging.critical(f"{RemoveStackInstanceResult['ErrorMessage']}")
			sys.exit(RemoveStackInstanceResult['ErrorMessage'])
		if RemoveStackSet:
			logging.info(f"Instances have received the deletion command, continuing to remove the stackset too")
			# If there were no Instances to be deleted
			if Instances[0]['ChildAccount'] is None:
				# skip the check to see if stack instances are gone
				RemoveStackInstanceResult['OperationId'] = None
				StackInstancesAreGone = dict()
				StackInstancesAreGone['Success'] = True
				StackInstancesAreGone['OperationId'] = None
				StackInstancesAreGone['StackSetStatus'] = "Not yet assigned"
			# else if there WERE child stacks that were deleted
			else:
				StackInstancesAreGone = Inventory_Modules.check_stack_set_status3(aws_acct, StackSetName, RemoveStackInstanceResult['OperationId'])
				logging.debug(f"The operation id {RemoveStackInstanceResult['OperationId']} is {StackInstancesAreGone['StackSetStatus']}")
			if not StackInstancesAreGone['Success']:
				logging.critical(f"There was a problem with removing the stack instances from stackset {StackSetName}."
				                 f"Moving to the next stackset in the list")
				break
			intervals_waited = 1
			while StackInstancesAreGone['StackSetStatus'] in ['RUNNING']:
				print(f"Waiting for operation {RemoveStackInstanceResult['OperationId']} to finish",
				      # f"." * intervals_waited,
				      f"{sleep_interval * intervals_waited} seconds waited so far", end='\r')
				sleep(sleep_interval)
				intervals_waited += 1
				StackInstancesAreGone = Inventory_Modules.check_stack_set_status3(aws_acct, StackSetName, RemoveStackInstanceResult['OperationId'])
				if not StackInstancesAreGone['Success']:
					logging.critical(f"There was a problem with removing the stack instances from stackset {StackSetName}.")
			StackSetResult = Inventory_Modules.delete_stackset3(aws_acct, pRegion, StackSetName)
			if StackSetResult['Success']:
				print(f"{ERASE_LINE}Removal of stackset {StackSetName} took {sleep_interval * intervals_waited} seconds")
			else:
				print(f"{ERASE_LINE}{Fore.RED}Removal of stackset {StackSetName} {Style.BRIGHT}failed{Style.NORMAL} due to:\n\t{StackSetResult['ErrorMessage']}.{Fore.RESET}")
elif pRefresh:
	RefreshOpsList = []
	for stackset in ApplicableStackSetsList:
		print(f"Beginning to refresh stackset {Fore.RED}{stackset}{Fore.RESET} as you requested...")
		cfn_client = aws_acct.session.client('cloudformation')
		# Get current attributes for the stacksets we've found...
		stacksetAttributes = cfn_client.describe_stack_set(StackSetName=stackset)
		# Then re-run those same stacksets, supplying the same information back to them -
		ReallyRefresh = False
		ReallyRefresh = (input(f"Refresh of {Fore.RED}{stackset}{Fore.RESET} has been requested.\n"
		                       f"Drift Status of the stackset is: {stacksetAttributes['StackSet']['StackSetDriftDetectionDetails']['DriftStatus']}\n"
		                       # f"as of {stacksetAttributes['StackSet']['StackSetDriftDetectionDetails']['DriftStatus']}"
		                       f"Are you still sure? (y/n): ") in ['y', 'Y']) if not pForce else False
		if ReallyRefresh or pForce:
			# WE have to separate the use-cases here, since the "Service Managed" update operation won't accept a "AdministrationRoleArn",
			# but the "Self Managed" *requires* it.
			if stacksetAttributes['StackSet']['PermissionModel'] == 'SERVICE_MANAGED':
				refresh_stack_set = cfn_client.update_stack_set(StackSetName=stacksetAttributes['StackSet']['StackSetName'],
				                                                UsePreviousTemplate=True,
				                                                Capabilities=stacksetAttributes['StackSet']['Capabilities'],
				                                                OperationPreferences={
					                                                'RegionConcurrencyType'  : 'PARALLEL',
					                                                'FailureToleranceCount'  : 0,
					                                                'MaxConcurrentPercentage': 100
				                                                })
			else:
				refresh_stack_set = cfn_client.update_stack_set(StackSetName=stacksetAttributes['StackSet']['StackSetName'],
				                                                UsePreviousTemplate=True,
				                                                Capabilities=stacksetAttributes['StackSet']['Capabilities'],
				                                                OperationPreferences={
					                                                'RegionConcurrencyType'  : 'PARALLEL',
					                                                'FailureToleranceCount'  : 0,
					                                                'MaxConcurrentPercentage': 100
				                                                },
				                                                AdministrationRoleARN=stacksetAttributes['StackSet']['AdministrationRoleARN'],
				                                                )
			RefreshOpsList.append({'StackSetName': stackset,
			                       'OperationId' : refresh_stack_set['OperationId']})
	for operation in RefreshOpsList:
		print(f"Checking on operations... ")
		StackSetStatus = cfn_client.describe_stack_set_operation(StackSetName=operation['StackSetName'], OperationId=operation['OperationId'])
		print(f"StackSet: {operation['StackSetName']} | Status: {StackSetStatus['StackSetOperation']['Status']}")

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
print()
print("Thanks for using this script...")
print()
