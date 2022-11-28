#!/usr/bin/env python3

import logging
import sys
import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore, Style
from queue import Queue
from threading import Thread
from time import sleep, time

'''
TODO:
	- Pythonize the whole thing
	- More Commenting throughout script
	Make deleting multiple closed accounts easier - needs a parameter that comprises "+delete +force -A -check" all in one - to delete all closed accounts at one time... 

	- There are four possible use-cases:
		- The stack exists as an association within the stackset AND it exists within the child account (typical)
			- We should remove the stackset-association with "--RetainStacks=False" and that will remove the child stack in the child account.
		- The stack exists as an association within the stackset, but has been manually deleted within the child account
			- If we remove the stackset-association with "--RetainStacks=False", it won't error, even when the stack doesn't exist within the child.
			- There is a special use case here where the child account has been deleted or suspended. This is a difficult use-case to test12.
		- The stack doesn't exist within the stackset association, but DOES exist within the child account (because its association was removed from the stackset)
			- The only way to remove this is to remove the stack from the child account. This would have to be done after having found the stack within the child account. This will be a ToDo for later...
		- The stack doesn't exist within the child account, nor within the stack-set
			- Nothing to do here
'''

init()

parser = CommonArguments()
parser.verbosity()
parser.singleprofile()
parser.singleregion()
parser.extendedargs()
parser.my_parser.add_argument(
	"-f", "--fragment",
	dest="pStackfrag",
	nargs="*",
	metavar="CloudFormation stack fragment",
	default=["all"],
	help="List containing fragment(s) of the cloudformation stack or stackset(s) you want to check for.")
# parser.my_parser.add_argument(
# 	"-s", "--status",
# 	dest="pstatus",
# 	metavar="Stack instance status",
# 	default="CURRENT",
# 	help="Filter for the status of the stack *instances*")
parser.my_parser.add_argument(
	"-A", "--RemoveAccount",
	dest="pAccountRemoveList",
	default=None,
	nargs="*",
	metavar="Account to remove from stacksets",
	help="The Account(s) number you want removed from ALL of the stacksets and ALL of the regions it's been found.")
parser.my_parser.add_argument(
	'-R', "--RemoveRegion",
	help="The region(s) you want to remove from all the stacksets.",
	default=None,
	nargs="*",
	metavar="region-name",
	dest="pRegionRemove")
parser.my_parser.add_argument(
	'-check',
	help="Do a comparison of the accounts found in the stacksets to the accounts found in the Organization and list out any that have been closed or suspended, but never removed from the stacksets.",
	action="store_const",
	const=True,
	default=False,
	dest="AccountCheck")
parser.my_parser.add_argument(
	'+delete',
	help="[Default] Do a Dry-run; if this parameter is specified, we'll delete stacksets we find, with no additional confirmation.",
	action="store_const",
	const=False,
	default=True,
	dest="DryRun")
# parser.my_parser.add_argument(
# 	'+force',
# 	help="This parameter will remove the account from a stackset - WITHOUT trying to remove the stacks within the child. This is a VERY bad thing to do unless you're absolutely sure.",
# 	action="store_const",
# 	const=True,
# 	default=False,
# 	dest="RetainStacks")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Region
pTiming = args.Time
verbose = args.loglevel
pStackfrag = args.pStackfrag
pCheckAccount = args.AccountCheck
pdryrun = args.DryRun
# pstatus = args.pstatus
pRegionRemove = args.pRegionRemove
pAccountRemoveList = args.pAccountRemoveList
# pForce = args.RetainStacks
pForce = args.Force
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")


###################

def random_string(stringLength=10):
	import random
	import string
	# Generate a random string of fixed length
	letters = string.ascii_lowercase
	randomstring = (''.join(random.choice(letters) for _ in range(stringLength)))
	return(randomstring)


def _delete_stack_instances(faws_acct, fRegion, fAccountList, fRegionList, fStackSetName, fForce=True):
	"""
	Required Parameters:
	faws_acct - the object containing the account credentials and such
	fRegion - the region we're looking to make changes in
	fAccountList - this is the listing of accounts that were FOUND to be within stack instances
	fRegionList - The list of regions within the stackset to remove as well
	fStackSetName - the stackset we're removing stack instances from
	fForce - whether the user wants to be able to confirm if the delete initially fails.
	"""
	logging.warning(f"Removing instances from {fStackSetName} StackSet")
	StackSetOpId = f"DeleteInstances-{random_string(5)}"
	if not fAccountList or not fRegionList:
		logging.error(f"AccountList and RegionList cannot be null")
		logging.warning(f"AccountList: {fAccountList}")
		logging.warning(f"RegionList: {fRegionList}")
		# Note: The "Success" is True below to show that the calling function can move forward, even though the Account / Regions are null
		return_response = {'Success': True, 'ErrorMessage': "Failed - Account List or Region List was null"}
		return(return_response)
	try:
		delete_stack_instance_response = Inventory_Modules.delete_stack_instances3(faws_acct, fRegion, fAccountList, fRegionList, fStackSetName, fForce, StackSetOpId)
		if delete_stack_instance_response['Success']:
			return_response = {'Success': True, 'OperationId': delete_stack_instance_response['OperationId']}
		else:
			return_response = {'Success': False, 'ErrorMessage': delete_stack_instance_response['ErrorMessage']}
		return(return_response)
	except Exception as my_Error:
		print(my_Error)
		if my_Error.response['Error']['Code'] == 'StackSetNotFoundException':
			logging.info("Caught exception 'StackSetNotFoundException', ignoring the exception...")
			return_response = {'Success': False, 'ErrorMessage': "Failed - StackSet not found"}
			return(return_response)
		else:
			print("Failure to run: ", my_Error)
			return_response = {'Success': False, 'ErrorMessage': "Failed-Other"}
			return(return_response)

##########################

if pTiming:
	begin_time = time()

ERASE_LINE = '\x1b[2K'
sleep_interval = 5
AllInstances = []

aws_acct = aws_acct_access(pProfile)
if pRegion.lower() == 'all':
	logging.critical(f"{Fore.RED}You specified 'all' as the region, but this script only works with a single region.\n"
	                 f"Please run the command again and specify only a single region{Fore.RESET}")
print()

if pdryrun:
	print("You asked me to find (but not delete) stacksets that match the following:")
else:
	print("You asked me to find (and delete) stacksets that match the following:")

print(f"\t\tIn the {aws_acct.AccountType} account {aws_acct.acct_number}")
print(f"\t\tIn this Region: {pRegion}")
if pRegionRemove is not None:
	print(f"\t\tLimiting targets to Region: {pRegionRemove}")
print(f"\t\tFor stacksets that contain these fragments: {pStackfrag}")
# print("		For stack instances that match this status: {}".format(pstatus))

if pAccountRemoveList is None:
	pass
else:
	print(f"\t\tSpecifically to find this account number: {pAccountRemoveList}")
if pCheckAccount:
	print(f"\t\tWe'll also display those accounts in the stacksets that are no longer part of the organization")
print()

# Get the StackSet names from the Management Account
StackSetNames = Inventory_Modules.find_stacksets3(aws_acct, pRegion, pStackfrag)
if not StackSetNames['Success']:
	logging.error("Something went wrong with the AWS connection. Please check the parameters supplied and try again.")
	sys.exit(StackSetNames)
logging.error(f"Found {len(StackSetNames['StackSets'])} StackSetNames that matched your fragment")

# Now go through those stacksets and determine the instances, made up of accounts and regions
# Most time spent in this loop
for i in range(len(StackSetNames['StackSets'])):
	print(f"{ERASE_LINE}Looking through {i+1} of {len(StackSetNames['StackSets'])} stacksets found with {pStackfrag} string in them", end='\r')
	# TODO: Creating the list to delete this way prohibits this script from including stacksets that are already empty. This should be fixed.
	StackInstances = Inventory_Modules.find_stack_instances3(aws_acct, pRegion, StackSetNames['StackSets'][i]['StackSetName'])
	logging.warning(f"Found {len(StackInstances)} Stack Instances within the StackSet {StackSetNames['StackSets'][i]['StackSetName']}")
	if len(StackInstances) == 0 and not pdryrun and pAccountRemoveList is None and pRegionRemove is None:
		logging.warning(f"While we didn't find any stack instances within {StackSetNames['StackSets'][i]['StackSetName']}, we assume you want to delete it, even when it's empty")
		AllInstances.append({
			'ParentAccountNumber': aws_acct.acct_number,
			'ChildAccount'       : None,
			'ChildRegion'        : None,
			# This next line finds the value of the Child StackName (which includes a random GUID) and assigns it within our dict
			# 'StackName': StackInstance['StackId'][StackInstance['StackId'].find('/')+1:StackInstance['StackId'].find('/', StackInstance['StackId'].find('/')+1)],
			'StackStatus'        : None,
			'StackSetName'       : StackSetNames['StackSets'][i]['StackSetName']
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

			if pRegionRemove is None or (StackInstance['Region'] in pRegionRemove):
				AllInstances.append({
					'ParentAccountNumber': aws_acct.acct_number,
					'ChildAccount'       : StackInstance['Account'],
					'ChildRegion'        : StackInstance['Region'],
					# This next line finds the value of the Child StackName (which includes a random GUID) and assigns it within our dict
					# 'StackName': StackInstance['StackId'][StackInstance['StackId'].find('/')+1:StackInstance['StackId'].find('/', StackInstance['StackId'].find('/')+1)],
					'StackStatus'        : StackInstance['Status'],
					'StackSetName'       : StackSetNames['StackSets'][i]['StackSetName']
					})
		elif not (StackInstance['Account'] in pAccountRemoveList):
			# If the user only wants to remove the stack instances associated with specific accounts,
			# then we only want to capture those stack instances where the account number shows up.
			# The following code captures this scenario
			logging.info(f"Found a stack instance, but the account didn't match {pAccountRemoveList}... exiting")
			continue


print(ERASE_LINE)
logging.error(f"Found {len(AllInstances)} stack instances.")

# for i in range(len(AllInstances)):
# 	logging.info("Account %s in Region %s has Stack %s in status %s", AllInstances[i]['ChildAccount'], AllInstances[i]['ChildRegion'], AllInstances[i]['StackName'], AllInstances[i]['StackStatus'])

AccountList = []
ApplicableStackSetsList = []
RegionList = []

for _ in range(len(AllInstances)):
	if pAccountRemoveList is None:  # Means we want to skip this account when removing
		ApplicableStackSetsList.append(AllInstances[_]['StackSetName'])
		AccountList.append(AllInstances[_]['ChildAccount'])
		RegionList.append(AllInstances[_]['ChildRegion'])
	elif pAccountRemoveList is not None:
		if AllInstances[_]['ChildAccount'] in pAccountRemoveList:
			ApplicableStackSetsList.append(AllInstances[_]['StackSetName'])
			AccountList.append(AllInstances[_]['ChildAccount'])
			RegionList.append(AllInstances[_]['ChildRegion'])

# I had to add this list comprehension to filter out the "None" types that happen when there are no stack-instances within a stack-set
AccountList = sorted(list(set([item for item in AccountList if item is not None])))
# RegionList isn't specific per account, as the deletion API doesn't need it to be, and it's easier to keep a single list of all regions, instead of per StackSet
# TODO: Since we allow this now, should we revisit this?
# If we update this script to allow the removal of individual regions as well as individual accounts, then we'll do that.
RegionList = sorted(list(set([item for item in RegionList if item is not None])))

ApplicableStackSetsList = sorted(list(set(ApplicableStackSetsList)))

if pCheckAccount:
	OrgAccounts = aws_acct.ChildAccounts
	OrgAccountList = []
	for i in range(len(OrgAccounts)):
		OrgAccountList.append(OrgAccounts[i]['AccountId'])
	print("Displaying accounts within the stacksets that aren't a part of the Organization")
	logging.info(f"There are {len(OrgAccountList)} accounts in the Org, and {len(AccountList)} unique accounts in all stacksets found")
	ClosedAccounts = list(set(AccountList)-set(OrgAccountList))
	InaccessibleAccounts = []
	for accountnum in AccountList:
		if verbose < 50:
			print(f"{ERASE_LINE}Trying to gain access to account number {accountnum}", end='\r')
		my_creds = Inventory_Modules.get_child_access3(aws_acct, accountnum)
		if 'AccessError' in my_creds.keys():
			InaccessibleAccounts.append(accountnum)
	print()
	logging.info(f"Found {len(InaccessibleAccounts) + len(ClosedAccounts)} accounts that don't belong")
	print(f"There were {len(ClosedAccounts)} accounts found in the {len(StackSetNames['StackSets'])} Stacksets we looked through, that are not a part of the Organization")
	print(f"There are {len(InaccessibleAccounts)} accounts that appear inaccessible, using typical role names")
	for item in ClosedAccounts:
		print(f"Account {item} is not in the Organization")
	for item in InaccessibleAccounts:
		print(f"Account {item} is unreachable using known roles")
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
* If this is NOT a dry-run (meaning you want to take action on the stacksets)
 - We assume you're looking to remove accounts from a specific stackset
 - We ask whether you're sure if you want to remove the account, unless you've also supplied the "+force" parameter, which bypasses the extra check
* If you didn't supply the Account Number
 - then we assume you wanted to remove the stack instances from the stackset(s)
 - except we previously allowed certain accounts to be "skipped", so we need to make sure we're skipping those accounts when we remove stack instances from these stacksets.
 - 
'''

if pdryrun and pAccountRemoveList is None:
	print(f"Found {len(StackSetNames['StackSets'])} StackSets that matched, with {len(AllInstances)} total instances across {len(AccountList)} accounts, across {len(RegionList)} regions")
	print(f"We found the following StackSets with the fragment you provided {pStackfrag}:")
	for n in range(len(StackSetNames['StackSets'])):
		print(f"{StackSetNames['StackSets'][n]['StackSetName']}")
	if args.loglevel < 50:
		print()
		print("We found the following unique accounts across all StackSets found")
		for accountid in AccountList:
			print(f"|{accountid}", end=' ')
			JustThisRegion = []
			for _ in range(len(AllInstances)):
				if AllInstances[_]['ChildAccount'] == accountid:
					JustThisRegion.append(AllInstances[_]['ChildRegion'])
			JustThisRegion = list(set(JustThisRegion))
			for _ in JustThisRegion:
				print(f"|{_}", end='')
			print()
elif pdryrun:
	print()
	print(f"We found that stacks that match these accounts {pAccountRemoveList} show up in these regions:")
	for i in range(len(AllInstances)):
		if AllInstances[i]['ChildAccount'] in pAccountRemoveList:
			print(f"\t{AllInstances[i]['StackSetName']} \t {AllInstances[i]['ChildRegion']} \t {AllInstances[i]['ChildAccount']}")
elif not pdryrun:
	print()
	print(f"Removing {len(AllInstances)} stack instances from the {len(StackSetNames['StackSets'])} StackSets found")
	StackInstanceItem = 0
	for StackSetName in ApplicableStackSetsList:
		StackInstanceItem += 1
		print(f"Now deleting stackset {StackSetName}. {StackInstanceItem} of {len(ApplicableStackSetsList)} done")
		# TODO: This needs to be wrapped in a try...except
		if RegionList is None:
			print(f"There appear to be no stack instances for this stack-set")
			continue
		if pAccountRemoveList is None:  # Remove all instances from the stackset
			if pRegionRemove is not None:
				logging.error(f"About to update stackset {StackSetName} to remove all accounts within {str(RegionList)}")
				RemoveStackSet = False
			else:
				logging.error(f"About to update stackset {StackSetName} to remove ALL accounts from all regions")
				RemoveStackSet = True
			RemoveStackInstanceResult = _delete_stack_instances(aws_acct, pRegion, AccountList, RegionList, StackSetName, pForce)
		else:
			logging.error(f"About to remove account {pAccountRemoveList} from stackset {StackSetName} in regions {str(RegionList)}")
			RemoveStackSet = False
			RemoveStackInstanceResult = _delete_stack_instances(aws_acct, pRegion, AccountList, RegionList, StackSetName, pForce)
		if RemoveStackInstanceResult['Success']:
			Instances = [item for item in AllInstances if item['StackSetName'] == StackSetName]
			print(f"{ERASE_LINE}Successfully initiated removal of {len(Instances)} instances from StackSet {StackSetName}")
		elif RemoveStackInstanceResult['ErrorMessage'] == 'Failed-ForceIt' and pForce:
			print("We tried to force the deletion, but some other problem happened.")
		elif RemoveStackInstanceResult['ErrorMessage'] == 'Failed-ForceIt' and not pForce:
			Decision = (input("Deletion of Stack Instances failed, but might work if we force it. Shall we force it? (y/n): ") in ['y', 'Y'])
			if Decision:
				RemoveStackInstanceResult = _delete_stack_instances(aws_acct, pRegion, AccountList, RegionList, StackSetName, True) 	# Try it again, forcing it this time
				if RemoveStackInstanceResult['Success']:
					print(f"{ERASE_LINE}Successfully retried StackSet {StackSetName}")
				elif pForce is True and RemoveStackInstanceResult['ErrorMessage'] == 'Failed-ForceIt':
					print(f"{ERASE_LINE}Some other problem happened on the retry.")
				elif RemoveStackInstanceResult['ErrorMessage'] == 'Failed-Other':
					print(f"{ERASE_LINE}Something else failed on the retry... Please report the error received.")
		elif RemoveStackInstanceResult['ErrorMessage'] == 'Failed-Other':
			print(f"{Fore.RED}Something else failed... Please report the error below{Fore.RESET}")
			logging.critical(f"{RemoveStackInstanceResult['ErrorMessage']}")
			sys.exit(RemoveStackInstanceResult['ErrorMessage'])
		elif str(RemoveStackInstanceResult['ErrorMessage']).find('OperationInProgressException') > 0:
			print(f"{Fore.RED}Another operation is running on this StackSet... Please wait for that operation to end and re-run this script{Fore.RESET}")
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

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time()-begin_time} seconds{Fore.RESET}")
print()
print("Thanks for using this script...")
print()
