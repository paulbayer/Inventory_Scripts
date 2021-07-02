#!/usr/bin/env python3

import pprint
import logging
import time
import Inventory_Modules
import argparse
import boto3
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

parser = argparse.ArgumentParser(
	description="This script removes stacksets entirely, or removes accounts from specific stacksets. This script can also determine if you have included accounts in your stacksets that have been removed (closed or suspended) from your Organization",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	help="You need to specify a specific ROOT profile")
parser.add_argument(
	"-f", "--fragment",
	dest="pStackfrag",
	nargs="*",
	metavar="CloudFormation stack fragment",
	default=["all"],
	help="List containing fragment(s) of the cloudformation stack or stackset(s) you want to check for.")
parser.add_argument(
	"-s", "--status",
	dest="pstatus",
	metavar="Stack instance status",
	default="CURRENT",
	help="Filter for the status of the stack *instances*")
parser.add_argument(
	"-k", "--skip",
	dest="pSkipAccounts",
	nargs="*",
	metavar="Accounts to leave alone",
	default=[],
	help="These are the account numbers you don't want to screw with. Likely the core accounts.")
parser.add_argument(
	"-r", "--region",
	dest="pRegion",
	metavar="region name string",
	default="us-east-1",
	help="The Master region you want to check for StackSets. Only one region is checked per script run.")
parser.add_argument(
	"-A", "--RemoveAccount",
	dest="pAccountRemove",
	default="NotProvided",
	metavar="Account to remove from stacksets",
	help="The Account number you want removed from ALL of the stacksets and ALL of the regions it's been found.")
parser.add_argument(
	'-R', "--RemoveRegion",
	help="The region you want to remove from all the stacksets.",
	default="NotProvided",
	metavar="region-name",
	dest="pRegionRemove")
parser.add_argument(
	'-check',
	help="Do a comparison of the accounts found in the stacksets to the accounts found in the Organization and list out any that have been closed or suspended, but never removed from the stacksets.",
	action="store_const",
	const=True,
	default=False,
	dest="AccountCheck")
parser.add_argument(
	'+delete',
	help="[Default] Do a Dry-run; if this parameter is specified, we'll delete stacksets we find, with no additional confirmation.",
	action="store_const",
	const=False,
	default=True,
	dest="DryRun")
parser.add_argument(
	'+force',
	help="This parameter will remove the account from a stackset - WITHOUT trying to remove the stacks within the child. This is a VERY bad thing to do unless you're absolutely sure.",
	action="store_const",
	const=True,
	default=False,
	dest="RetainStacks")
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,  # args.loglevel = 40
	default=logging.CRITICAL)  # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,  # args.loglevel = 30
	default=logging.CRITICAL)  # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,  # args.loglevel = 20
	default=logging.CRITICAL)  # args.loglevel = 50
parser.add_argument(
	'-d', '--debug',
	help="Print debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,  # args.loglevel = 10
	default=logging.CRITICAL)  # args.loglevel = 50
args = parser.parse_args()

pProfile = args.pProfile
pRegion = args.pRegion
pForce = args.RetainStacks
pStackfrag = args.pStackfrag
AccountsToSkip = args.pSkipAccounts
pCheckAccount = args.AccountCheck
verbose = args.loglevel
pdryrun = args.DryRun
pstatus = args.pstatus
pAccountRemove = args.pAccountRemove
pRegionRemove = args.pRegionRemove
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")


###################

def randomString(stringLength=10):
	import random
	import string
	# Generate a random string of fixed length
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for i in range(stringLength))

########################
#### delete_stack_instances #####
# Required Parameters:
# StackSetNames
# RegionList
# AccountList
# pProfile
# pRegion
# pAccountRemove
# pForce
#
####################


def _delete_stack_instances(fProfile, fRegion, fAccountList, fAccountRemove, fAccountsToSkip, fRegionList, fStackSet, fForce=True):
	session_cfn = boto3.Session(profile_name=pProfile, region_name=pRegion)
	logging.warning(f"Removing instances from {fStackSet['StackSetName']} StackSet")
	try:
		StackSetOpId = f"Delete-{randomString(5)}"
		response = Inventory_Modules.delete_stack_instances(fProfile, fRegion, fAccountList, fRegionList, fStackSet['StackSetName'], fForce, StackSetOpId)
		# pprint.pprint(response)
	except Exception as e:
		if e.response['Error']['Code'] == 'StackSetNotFoundException':
			logging.info("Caught exception 'StackSetNotFoundException', ignoring the exception...")
		else:
			print("Error: ", e)
			return("Failed-Other")
	StackOperationsRunning = True
	client_cfn = session_cfn.client('cloudformation')
	timer = 10
	while StackOperationsRunning:
		InstancesToSkip = 0
		SpecificInstancesLeft = 0
		logging.debug("Got into the While Loop")
		logging.warning(fStackSet['StackSetName'])
		try:
			time.sleep(3)
			Status = client_cfn.list_stack_set_operations(StackSetName=fStackSet['StackSetName'])
			# pprint.pprint(Status)
			logging.info(f"StackSet Operation state is {Status['Summaries'][0]['Status']}")
			if Status['Summaries'][0]['Status'] in ['CANCELLED', 'FAILED']:
				time.sleep(2)
				Reason = client_cfn.list_stack_set_operation_results(StackSetName=fStackSet['StackSetName'], OperationId=StackSetOpId)
				for k in range(len(Reason)):
					logging.info("Reason: %s", Reason['Summaries'][k]['StatusReason'])
					if Reason['Summaries'][k]['Status'] == 'FAILED' and Reason['Summaries'][k]['StatusReason'].find("role with trust relationship to Role") > 0:
						logging.info(f"StackSet Operation status reason is: {Reason['Summaries'][k]['StatusReason']}")
						print(f"Error removing account {pAccountRemove} from the StackSet {fStackSet['StackSetName']}. We should try to delete the stack instance with '--retain-stacks' enabled...")
						return("Failed-ForceIt")
			response2 = client_cfn.list_stack_instances(StackSetName=fStackSet['StackSetName'])['Summaries']
			for j in range(len(response2)):
				if response2[j]['Account'] in fAccountsToSkip:
					InstancesToSkip += 1
				elif response2[j]['Account'] == fAccountRemove:
					SpecificInstancesLeft += 1
				# elif response2[j]['Region'] == fRegionRemove:
				# 	SpecificInstancesLeft+=1
			# if fAccountRemove=='NotProvided' and fRegionRemove=='NotProvided':
				# InstancesLeft=len(response2)-InstancesToSkip
				# logging.info("There are still %s instances left in the stackset" % InstancesLeft)
			if fAccountRemove == 'NotProvided':
				InstancesLeft = len(response2)-InstancesToSkip
				logging.info(f"There are still {InstancesLeft} instances left in the stackset")
			else:  # A specific account was provided to remove from all stacksets
				InstancesLeft = SpecificInstancesLeft
				logging.info("There are still %s instances of account %s left in the stackset", SpecificInstancesLeft, fAccountRemove)
			StackOperationsRunning = (Status['Summaries'][0]['Status'] in ['RUNNING', 'PENDING'])
			logging.info(f"StackOperationsRunning is {StackOperationsRunning}")
			if StackOperationsRunning:
				print(f"{ERASE_LINE}Waiting {timer} seconds for {fStackSet['StackSetName']} to be fully deleted. There's still {InstancesLeft} instances left.", end='\r')
				time.sleep(10)
				timer += 10
			elif Status['Summaries'][0]['Status'] == 'SUCCEEDED':
				# pprint.pprint(Status['Summaries'])
				logging.info("Successfully removed %s from %s", fAccountRemove, fStackSet['StackSetName'])
				return("Success")
			else:
				logging.info("Something else failed")
				return("Failed-Other")
		except Exception as e:
			# if e.response['Error']['Code'] == 'StackSetNotFoundException':
			# 	logging.info("Caught exception 'StackSetNotFoundException', ignoring the exception...")
			# 	StackOperationsRunning=True
			# 	pass
			# else:
			print("Error: ", e)
			break

##########################
ERASE_LINE = '\x1b[2K'

AllInstances = []
# StackSetNames2=[]

print()

if pdryrun:
	print("You asked me to find (but not delete) stacksets that match the following:")
else:
	print("You asked me to find (and delete) stacksets that match the following:")
print(f"\t\tIn the ROOT profile {pProfile} and all children")
print(f"\t\tIn these regions: {pRegion}")
print(f"\t\tFor stacksets that contain these fragments: {pStackfrag}")
# print("		For stack instances that match this status: {}".format(pstatus))
if pAccountRemove == "NotProvided":
	pass
else:
	print(f"\t\tSpecifically to find this account number: {pAccountRemove}")
if pCheckAccount:
	print("		We'll also display those accounts in the stacksets that are no longer part of the organization")
print()

# Get the StackSet names from the Master Profile
StackSetNames = Inventory_Modules.find_stacksets(pProfile, pRegion, pStackfrag)
ProfileAccountNumber = Inventory_Modules.find_account_number(pProfile)
logging.error(f"Found {len(StackSetNames)} StackSetNames that matched your fragment")

# Now go through those stacksets and determine the instances, made up of accounts and regions
for i in range(len(StackSetNames)):
	print(ERASE_LINE, f"Looking for stacksets with {pStackfrag} string in account {ProfileAccountNumber} in region {pRegion}", end='\r')
	StackInstances = Inventory_Modules.find_stack_instances(pProfile, pRegion, StackSetNames[i]['StackSetName'])
	# pprint.pprint(StackInstances)
	# sys.exit(99)
	logging.warning(f"Found {len(StackInstances)} Stack Instances within the StackSet {StackSetNames[i]['StackSetName']}")
	for j in range(len(StackInstances)):
		if 'StackId' not in StackInstances[j].keys():
			logging.info("The stack instance found doesn't have a stackid associated. Which means it's never been deployed and probably OUTDATED")
			pass
		if pAccountRemove == 'NotProvided':
			pass
		elif not (StackInstances[j]['Account'] == pAccountRemove):
			logging.info("Found a stack instance, but the account didn't match %s... exiting", pAccountRemove)
			continue
		# pprint.pprint(StackInstances[j])
		logging.debug("This is Instance #: %s", str(j))
		# logging.debug("This is StackId: %s", str(StackInstances[j]['StackId']))
		logging.debug("This is instance status: %s", str(StackInstances[j]['Status']))
		logging.debug("This is ChildAccount: %s", StackInstances[j]['Account'])
		logging.debug("This is ChildRegion: %s", StackInstances[j]['Region'])
		AllInstances.append({
			'ParentAccountNumber': ProfileAccountNumber,
			'ChildAccount': StackInstances[j]['Account'],
			'ChildRegion': StackInstances[j]['Region'],
			# This next line finds the value of the Child StackName (which includes a random GUID) and assigns it within our dict
			# 'StackName': StackInstances[j]['StackId'][StackInstances[j]['StackId'].find('/')+1:StackInstances[j]['StackId'].find('/', StackInstances[j]['StackId'].find('/')+1)],
			'StackStatus': StackInstances[j]['Status'],
			'StackSetName': StackInstances[j]['StackSetId'][:StackInstances[j]['StackSetId'].find(':')]
		})
		# pprint.pprint(AllInstances)
		print(".", end='')

print(ERASE_LINE)
logging.error(f"Found {len(AllInstances)} stack instances.")

# for i in range(len(AllInstances)):
# 	logging.info("Account %s in Region %s has Stack %s in status %s", AllInstances[i]['ChildAccount'], AllInstances[i]['ChildRegion'], AllInstances[i]['StackName'], AllInstances[i]['StackStatus'])

AccountList = []
StackSetStillInUse = []
RegionList = []
for i in range(len(AllInstances)):
	if AllInstances[i]['ChildAccount'] in AccountsToSkip:  # Means we want to skip this account when removing
		StackSetStillInUse.append(AllInstances[i]['StackSetName'])
	elif not pAccountRemove == 'NotProvided':     # Meaning that we're looking to remove this account from stacksets
		StackSetStillInUse.append(AllInstances[i]['StackSetName'])
		AccountList.append(AllInstances[i]['ChildAccount'])
	else:   # Meaning we *didn't* provide an account to remove from stacksets
		AccountList.append(AllInstances[i]['ChildAccount'])
for i in range(len(AllInstances)):
	# This isn't specific per account, as the deletion API doesn't need it to be, and it's easier to keep a single list of all regions, instead of per StackSet
	# If we update this script to allow the removal of individual regions as well as individual accounts, then we'll do that.
	RegionList.append(AllInstances[i]['ChildRegion'])
AccountList = sorted(list(set(AccountList)))
StackSetStillInUse = sorted(list(set(StackSetStillInUse)))
RegionList = sorted(list(set(RegionList)))

if pCheckAccount:
	OrgAccounts = Inventory_Modules.find_child_accounts2(pProfile)
	OrgAccountList = []
	for i in range(len(OrgAccounts)):
		OrgAccountList.append(OrgAccounts[i]['AccountId'])
	print("Displaying accounts within the stacksets that aren't a part of the Organization")
	logging.info("There are %s accounts in the Org, and %s unique accounts in all stacksets found", len(OrgAccountList), len(AccountList))
	ClosedAccounts = list(set(AccountList)-set(OrgAccountList))
	InaccessibleAccounts = []
	for eachaccount in AccountList:
		my_creds, role_tried = Inventory_Modules.get_child_access2(pProfile, eachaccount)
		if role_tried.find("failed") > 0:
			InaccessibleAccounts.append(eachaccount)
	# InaccessibleAccounts.extend(ClosedAccounts)
	logging.info("Found %s accounts that don't belong", len(InaccessibleAccounts)+len(ClosedAccounts))
	print("There were {} accounts found in the {} Stacksets we looked through, that are not a part of the Organization".format(len(ClosedAccounts), len(StackSetNames)))
	print("There are {} accounts that appear inaccessible, using typical role names".format(len(InaccessibleAccounts)))
	for item in ClosedAccounts:
		print(f"Account {item} is not in the Organization")
	for item in InaccessibleAccounts:
		print(f"Account {item} is unreachable using known roles")
	print()


'''
The next section is broken up into a few pieces. I should try to re-write this to make it easier to read, but I decided to comment here instead.

* if pdryrun and pAccountRemove=='NotProvided'
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

if pdryrun and pAccountRemove == 'NotProvided':
	# pprint.pprint(AllInstances)
	print("Found {} StackSets that matched, with {} total instances across {} accounts, across {} regions".format(len(StackSetNames), len(AllInstances), len(AccountList), len(RegionList)))
	if args.loglevel < 50:
		print(f"We found the following StackSets with the fragment you provided {pStackfrag}:")
		for n in range(len(StackSetNames)):
			print(f"{StackSetNames[n]['StackSetName']}")
		print()
		print("We found the following unique accounts across all StackSets found")
		for n in range(len(AccountList)):
			print(f"|{AccountList[n]}", end=' ')
			JustThisRegion = []
			for p in range(len(AllInstances)):
				if AllInstances[p]['ChildAccount'] == AccountList[n]:
					JustThisRegion.append(AllInstances[p]['ChildRegion'])
			JustThisRegion = list(set(JustThisRegion))
			for p in range(len(JustThisRegion)):
				print(f"|{JustThisRegion[p]}", end='')
			print()
elif pdryrun:
	print()
	print("Out of {} StackSets that matched, there are {} instances of account {}".format(len(StackSetNames), len(AllInstances), pAccountRemove))
	if args.loglevel < 50:
		print(f"We found that account {pAccountRemove} shows up in these stacksets in these regions:")
		for i in range(len(AllInstances)):
			if AllInstances[i]['ChildAccount'] == pAccountRemove:
				fmt = '%-50s %-15s'
				print(fmt % (f"\t{AllInstances[i]['StackSetName']}", f"{AllInstances[i]['ChildRegion']}"))
elif not pdryrun:
	print()
	print("Removing {} stack instances from the {} StackSets found".format(len(AllInstances), len(StackSetNames)))
	# pprint.pprint(StackSetNames)
	for m in range(len(StackSetNames)):
		logging.info("About to remove account %s from stackset %s in regions %s ", pAccountRemove, StackSetNames[m], str(RegionList))
		result = _delete_stack_instances(pProfile, pRegion, AccountList, pAccountRemove, AccountsToSkip, RegionList, StackSetNames[m], pForce)
		if result == 'Success':
			print(f"{ERASE_LINE}Successfully finished StackSet {StackSetNames[m]['StackSetName']}")
		elif pForce is True and result == 'Failed-ForceIt':
			print("Some other problem happened.")
		elif pForce is False and result == 'Failed-ForceIt':
			Decision = (input("Deletion of Stack Instances failed, but might work if we force it. Shall we force it? (y/n): ") in ['y', 'Y'])
			if Decision:
				result = _delete_stack_instances(pProfile, pRegion, AccountList, pAccountRemove, AccountsToSkip, RegionList, StackSetNames[m], True) 	# Try it again, forcing it this time
				if result == 'Success':
					print(f"{ERASE_LINE}Successfully retried StackSet {StackSetNames[m]['StackSetName']}")
				elif pForce is True and result == 'Failed-ForceIt':
					print(f"{ERASE_LINE}Some other problem happened on the retry.")
				elif result == 'Failed-Other':
					print(f"{ERASE_LINE}Something else failed on the retry... Who knows?")
		elif result == 'Failed-Other':
			print("Something else failed... Who knows?")

	if pAccountRemove == 'NotProvided':
		try:
			print()
			print(f"Now deleting {len(StackSetNames) - len(StackSetStillInUse)} stacksets from {pProfile} Profile")
			for i in range(len(StackSetNames)):
				# pprint.pprint(StackSetNames[i])
				# pprint.pprint(StackSetStillInUse)
				if StackSetNames[i]['StackSetName'] in StackSetStillInUse:
					continue
				else:
					response = Inventory_Modules.delete_stackset(pProfile, pRegion, StackSetNames[i]['StackSetName'])
					logging.warning(f"StackSet {StackSetNames[i]['StackSetName']} has been deleted from account {pProfile} in region {pRegion}")
		except Exception as e:
			pprint.pprint(e)
			pass

print()
print("Thanks for using this script...")
print()
