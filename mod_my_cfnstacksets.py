#!/usr/bin/env python3

import logging
import time
import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init

'''
TODO:
	- Enable this script to accept a Session Token to allow for Federated users
	- Figure a way to report on which stacksets an account that doesn't belong in the Organization was found in
	- Pythonize the whole thing
	- More Commenting throughout script

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
	help="The Account number you want removed from ALL of the stacksets and ALL of the regions it's been found.")
# parser.my_parser.add_argument(
# 	'-R', "--RemoveRegion",
# 	help="The region you want to remove from all the stacksets.",
# 	default=None,
# 	metavar="region-name",
# 	dest="pRegionRemove")
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
parser.my_parser.add_argument(
	'+force',
	help="This parameter will remove the account from a stackset - WITHOUT trying to remove the stacks within the child. This is a VERY bad thing to do unless you're absolutely sure.",
	action="store_const",
	const=True,
	default=False,
	dest="RetainStacks")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Region
verbose = args.loglevel
AccountsToSkip = args.SkipAccounts
pStackfrag = args.pStackfrag
pCheckAccount = args.AccountCheck
pdryrun = args.DryRun
# pstatus = args.pstatus
pAccountRemoveList = args.pAccountRemoveList
# pRegionRemove = args.pRegionRemove
pForce = args.RetainStacks
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
	try:
		response = Inventory_Modules.delete_stack_instances2(faws_acct, fRegion, fAccountList, fRegionList, fStackSetName, fForce, StackSetOpId)
		return("Success")
	except Exception as my_Error:
		if my_Error.response['Error']['Code'] == 'StackSetNotFoundException':
			logging.info("Caught exception 'StackSetNotFoundException', ignoring the exception...")
		else:
			print("Failure to run: ", my_Error)
			return("Failed-Other")
	"""
	session_cfn = faws_acct.session
	client_cfn = session_cfn.client('cloudformation')
	timewaited = 10
	while StackOperationsRunning:
		InstancesToSkip = 0
		SpecificInstancesLeft = 0
		logging.debug("Got into the While Loop")
		logging.warning(f"Began working on stackset: {fStackSetName['StackSetName']}")
		try:
			time.sleep(3)
			Status = client_cfn.list_stack_set_operation_results(StackSetName=fStackSetName['StackSetName'], OperationId=response['OperationId'])
			logging.info(f"StackSet Operation state is {Status['Summaries']}")
			if Status['Summaries'][0]['Status'] in ['CANCELLED', 'FAILED']:
				time.sleep(2)
				Reason = client_cfn.list_stack_set_operation_results(StackSetName=fStackSetName['StackSetName'], OperationId=StackSetOpId)
				for k in range(len(Reason)):
					logging.info("Reason: %s", Reason['Summaries'][k]['StatusReason'])
					if Reason['Summaries'][k]['Status'] == 'FAILED' and Reason['Summaries'][k]['StatusReason'].find("role with trust relationship to Role") > 0:
						logging.info(f"StackSet Operation status reason is: {Reason['Summaries'][k]['StatusReason']}")
						print(f"Error removing account(s) {fAccountList} from the StackSet {fStackSetName['StackSetName']}. We should try to delete the stack instance with '--retain-stacks' enabled...")
						return("Failed-ForceIt")
			response2 = client_cfn.list_stack_instances(StackSetName=fStackSetName['StackSetName'])['Summaries']
			for _ in range(len(response2)):
				if response2[_]['Account'] in fAccountsToSkip:
					InstancesToSkip += 1
				elif response2[_]['Account'] in fAccountRemoveList:
					SpecificInstancesLeft += 1
			if fAccountRemoveList is None:
				InstancesLeft = len(response2)-InstancesToSkip
				logging.info(f"There are still {InstancesLeft} instances left in the stackset")
			else:  # A specific account was provided to remove from all stacksets
				InstancesLeft = SpecificInstancesLeft
				logging.info(f"There are still {SpecificInstancesLeft} instances of account {fAccountRemoveList} left in the stackset")
			StackOperationsRunning = (Status['Summaries'][0]['Status'] in ['RUNNING', 'PENDING'])
			logging.info(f"StackOperationsRunning is {StackOperationsRunning}")
			if StackOperationsRunning:
				print(f"{ERASE_LINE}Waiting {timewaited} seconds for {fStackSetName['StackSetName']} to be fully deleted. There's still {InstancesLeft} instances left.", end='\r')
				time.sleep(10)
				timewaited += 10
			elif Status['Summaries'][0]['Status'] == 'SUCCEEDED':
				logging.info(f"Successfully removed {fAccountRemoveList} instances from stackset {fStackSetName['StackSetName']}")
				return("Success")
			else:
				logging.info("Something else failed")
				return("Failed-Other")

		except Exception as my_Error:
			# if my_Error.response['Error']['Code'] == 'StackSetNotFoundException':
			# 	logging.info("Caught exception 'StackSetNotFoundException', ignoring the exception...")
			# 	StackOperationsRunning=True
			# 	pass
			# else:
			print("Last Error: ", my_Error)
			break
			return("Failed-Unsure")
	return("Success")
	"""

##########################
ERASE_LINE = '\x1b[2K'

AllInstances = []

aws_acct = aws_acct_access(pProfile)

print()

if pdryrun:
	print("You asked me to find (but not delete) stacksets that match the following:")
else:
	print("You asked me to find (and delete) stacksets that match the following:")
print(f"\t\tIn the {aws_acct.AccountType} account {aws_acct.acct_number}")
print(f"\t\tIn this Region: {pRegion}")
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
StackSetNames = Inventory_Modules.find_stacksets2(aws_acct, pRegion, pStackfrag)
logging.error(f"Found {len(StackSetNames)} StackSetNames that matched your fragment")

# Now go through those stacksets and determine the instances, made up of accounts and regions
for i in range(len(StackSetNames)):
	print(f"{ERASE_LINE}Looking through {i} of {len(StackSetNames)} stacksets found with {pStackfrag} string in them", end='\r')
	StackInstances = Inventory_Modules.find_stack_instances2(aws_acct, pRegion, StackSetNames[i]['StackSetName'])
	logging.warning(f"Found {len(StackInstances)} Stack Instances within the StackSet {StackSetNames[i]['StackSetName']}")
	for j in range(len(StackInstances)):
		if 'StackId' not in StackInstances[j].keys():
			logging.info("The stack instance found doesn't have a stackid associated. Which means it's never been deployed and probably OUTDATED")
			pass
		if pAccountRemoveList is None:
			pass
		elif not (StackInstances[j]['Account'] in pAccountRemoveList):
			logging.info(f"Found a stack instance, but the account didn't match {pAccountRemoveList}... exiting")
			continue
		logging.debug(f"This is Instance #: {str(j)}")
		# logging.debug("This is StackId: %s", str(StackInstances[j]['StackId']))
		logging.debug(f"This is instance status: {str(StackInstances[j]['Status'])}")
		logging.debug(f"This is ChildAccount: {StackInstances[j]['Account']}")
		logging.debug(f"This is ChildRegion: {StackInstances[j]['Region']}")
		AllInstances.append({
			'ParentAccountNumber': aws_acct.acct_number,
			'ChildAccount': StackInstances[j]['Account'],
			'ChildRegion': StackInstances[j]['Region'],
			# This next line finds the value of the Child StackName (which includes a random GUID) and assigns it within our dict
			# 'StackName': StackInstances[j]['StackId'][StackInstances[j]['StackId'].find('/')+1:StackInstances[j]['StackId'].find('/', StackInstances[j]['StackId'].find('/')+1)],
			'StackStatus': StackInstances[j]['Status'],
			'StackSetName': StackInstances[j]['StackSetId'][:StackInstances[j]['StackSetId'].find(':')]
			})
		# print(".", end='')

print(ERASE_LINE)
logging.error(f"Found {len(AllInstances)} stack instances.")

# for i in range(len(AllInstances)):
# 	logging.info("Account %s in Region %s has Stack %s in status %s", AllInstances[i]['ChildAccount'], AllInstances[i]['ChildRegion'], AllInstances[i]['StackName'], AllInstances[i]['StackStatus'])

AccountList = []
ApplicableStackSetsList = []
RegionList = []

if pAccountRemoveList is None:  # Means we want to skip this account when removing
	ApplicableStackSetsList = [AllInstances[_]['StackSetName'] for _ in range(len(AllInstances))]
	AccountList = [AllInstances[_]['ChildAccount'] for _ in range(len(AllInstances))]
	RegionList = [AllInstances[_]['ChildRegion'] for _ in range(len(AllInstances))]
elif pAccountRemoveList is not None:
	ApplicableStackSetsList = [(AllInstances[_]['StackSetName'] for _ in range(len(AllInstances)) if AllInstances[_]['ChildAccount'] in pAccountRemoveList)]
	AccountList = [(AllInstances[_]['ChildAccount'] for _ in range(len(AllInstances)) if AllInstances[_]['ChildAccount'] in pAccountRemoveList)]
	RegionList = [(AllInstances[_]['ChildRegion'] for _ in range(len(AllInstances)) if AllInstances[_]['ChildAccount'] in pAccountRemoveList)]

AccountList = sorted(list(set(AccountList)))
ApplicableStackSetsList = sorted(list(set(ApplicableStackSetsList)))
# RegionList isn't specific per account, as the deletion API doesn't need it to be, and it's easier to keep a single list of all regions, instead of per StackSet
# If we update this script to allow the removal of individual regions as well as individual accounts, then we'll do that.
RegionList = sorted(list(set(RegionList)))

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
	print(f"There were {len(ClosedAccounts)} accounts found in the {len(StackSetNames)} Stacksets we looked through, that are not a part of the Organization")
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
	print(f"Found {len(StackSetNames)} StackSets that matched, with {len(AllInstances)} total instances across {len(AccountList)} accounts, across {len(RegionList)} regions")
	print(f"We found the following StackSets with the fragment you provided {pStackfrag}:")
	for n in range(len(StackSetNames)):
		print(f"{StackSetNames[n]['StackSetName']}")
	if args.loglevel < 50:
		print()
		print("We found the following unique accounts across all StackSets found")
		for accountid in AccountList:
			print(f"|{accountid}", end=' ')
			JustThisRegion = []
			for _ in range(len(AllInstances)):
				if AllInstances[p]['ChildAccount'] == accountid:
					JustThisRegion.append(AllInstances[_]['ChildRegion'])
			JustThisRegion = list(set(JustThisRegion))
			for _ in JustThisRegion:
				print(f"|{_}", end='')
			print()
elif pdryrun:
	print()
	print(f"Out of {len(StackSetNames)} StackSets that matched, these accounts {pAccountRemoveList} show up in {len(AllInstances)} instances")
	if args.loglevel < 50:
		print(f"We found that account {pAccountRemoveList} shows up in these stacksets in these regions:")
		for i in range(len(AllInstances)):
			if AllInstances[i]['ChildAccount'] in pAccountRemoveList:
				print(f"\t{AllInstances[i]['StackSetName']} \t {AllInstances[i]['ChildRegion']} \t {AllInstances[i]['ChildAccount']}")
	else:
		print("For specific information on which stacks and regions, please enable verbose output")
elif not pdryrun:
	print()
	print(f"Removing {len(AllInstances)} stack instances from the {len(StackSetNames)} StackSets found")
	for StackSetName in ApplicableStackSetsList:
		# TODO: This needs to be wrapped in a try...except
		if RegionList is None:
			print(f"There appear to be no stack instances for this stack-set")
			continue
		if pAccountRemoveList is None:  # Remove all instances from the stackset
			logging.error(f"About to remove ALL stack instances from stackset {StackSetName}")
			AllAccounts = [accountid['AccountId'] for accountid in aws_acct.ChildAccounts]
			result = _delete_stack_instances(aws_acct, pRegion, AccountList, AllAccounts, AccountsToSkip, RegionList, StackSetName, pForce)
		else:
			logging.error(f"About to remove account {pAccountRemoveList} from stackset {StackSetName} in regions {str(RegionList)}")
			result = _delete_stack_instances(aws_acct, pRegion, AccountList, pAccountRemoveList, AccountsToSkip, RegionList, StackSetName, pForce)
		if result == 'Success':
			print(f"{ERASE_LINE}Successfully removed accounts {AccountList} from StackSet {StackSetName}")
		elif result == 'Failed-ForceIt' and pForce:
			print("We tried to force the deletion, but some other problem happened.")
		elif result == 'Failed-ForceIt' and not pForce:
			Decision = (input("Deletion of Stack Instances failed, but might work if we force it. Shall we force it? (y/n): ") in ['y', 'Y'])
			if Decision:
				result = _delete_stack_instances(aws_acct, pRegion, AccountList, pAccountRemoveList, AccountsToSkip, RegionList, StackSetName, True) 	# Try it again, forcing it this time
				if result == 'Success':
					print(f"{ERASE_LINE}Successfully retried StackSet {StackSetName}")
				elif pForce is True and result == 'Failed-ForceIt':
					print(f"{ERASE_LINE}Some other problem happened on the retry.")
				elif result == 'Failed-Other':
					print(f"{ERASE_LINE}Something else failed on the retry... Who knows?")
		elif result == 'Failed-Other':
			print("Something else failed... Please report the error received")

print()
print("Thanks for using this script...")
print()
