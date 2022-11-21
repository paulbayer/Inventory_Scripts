#!/usr/bin/env python3

import Inventory_Modules
from account_class import aws_acct_access
from ArgumentsClass import CommonArguments
from colorama import init, Fore
from time import time
from botocore.exceptions import ClientError
import logging

init()

parser = CommonArguments()
parser.singleprofile()
parser.singleregion()
parser.extendedargs()
parser.verbosity()
parser.my_parser.add_argument(
	"+d", "+delete",
	dest="DeletionRun",
	action="store_true",
	help="This will delete the SC Provisioned Products found to be in error, or without active CloudFormation stacks - without any opportunity to confirm. Be careful!!")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Region
pTiming = args.Time
verbose = args.loglevel
DeletionRun = args.DeletionRun
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

# if pTiming:
# 	timing_logging_level = 45
# 	logging.addLevelName(timing_logging_level, 'timing')
# 	logging.basicConfig(level=timing_logging_level, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

##########################


def sort_by_email(elem):
	return elem('AccountEmail')


def define_pretty_headings(fSCP2Stacks):
	namelength = 3
	for _ in range(len(fSCP2Stacks)):
		if namelength < len(fSCP2Stacks[_]['SCProductName']):
			namelength = len(fSCP2Stacks[_]['SCProductName'])
		else:
			pass
	fDisplaySpacing = {
		'AccountNumber'           : 15,
		'SCProductName'           : namelength,
		'ProvisioningArtifactName': 8,
		'CFNStackName'            : 35,
		'SCStatus'                : 10,
		'CFNStackStatus'          : 18,
		'AccountStatus'           : 10,
		'AccountEmail'            : 20}
	return(fDisplaySpacing)

##########################

'''
TODO: 
- Need to add a parameter that allows the user to close / terminate the SC products for only the closed / suspended accounts (very safe)
- Add a parameter that refuses to close/ terminate accounts with active VPCs?
'''


'''
Significant Variable Explanation:
	'AcctList' holds a list of accounts within this Org.
	'SCresponse' holds a native list of Service Catalog Provisioned Products supplied by the native API.  
	'SCProducts' holds a refined list of the Service Catalog Provisioned Products from the 'SCresponse' list, but only the fields we're interested in. 
	** TODO: I duplicated this listing, in case later I decided to add some additional useful fields to the dict. 
	'SCP2Stacks' holds a list of the CloudFormation Stacks in this account that *match* the Provisioned Products.
	** TODO: This list should hold *all* stacks and then we could find stacks for accounts that no longer exist.
	'AccountHistogram' holds the list of accounts (the account numbers are the keys in this dict) and the number of SC products that are created for this account is the value of that key.
'''
begin_time = time()

ERASE_LINE = '\x1b[2K'

aws_acct = aws_acct_access(fProfile=pProfile, fRegion=pRegion)

print()

SCP2Stacks = []
SCProducts = []
ErroredSCPExists = False
# try:
# 	session_aws = aws_acct.session
# except AttributeError as my_Error:
# 	print(f"Profile '{pProfile}' doesn't seem to exist, or work. Please check your credentials.")
# 	print()
# 	sys.exit(1)
client_org = aws_acct.session.client('organizations')
client_cfn = aws_acct.session.client('cloudformation')

AccountHistogram = {}
SuspendedAccounts = []
ClosedAccts = []
for account in aws_acct.ChildAccounts:
	AccountHistogram[account['AccountId']] = account['AccountStatus']
	if account['AccountStatus'] == 'SUSPENDED':
		SuspendedAccounts.append(account['AccountId'])
try:
	SCresponse = Inventory_Modules.find_sc_products(pProfile, pRegion, "All", 10)
	logging.warning("A list of the SC Products found:")
	for i in range(len(SCresponse)):
		logging.warning(f"SC Product Name {SCresponse[i]['Name']} | SC Product Status {SCresponse[i]['Status']}")
		SCProducts.append({
			'SCPName': SCresponse[i]['Name'],
			'SCPId': SCresponse[i]['Id'],
			'SCPStatus': SCresponse[i]['Status'],
			'SCPRecordId': SCresponse[i]['LastRecordId'],
			'ProvisioningArtifactName': SCresponse[i]['ProvisioningArtifactName']
			})
		if SCresponse[i]['Status'] == 'ERROR' or SCresponse[i]['Status'] == 'TAINTED':
			ErroredSCPExists = True

	CFNStacks = Inventory_Modules.find_stacks3(aws_acct, pRegion, f"SC-{aws_acct.acct_number}")

	if pTiming:
		logging.critical(f"It's been {time()-begin_time} seconds now...")
	SCresponse = None

	# TODO: Create a queue - place the SCProducts on that queue, one by one, and let this code run in a multi-thread worker
	for i in range(len(SCProducts)):
		print(f"{ERASE_LINE}{Fore.RED}Checking {i + 1} of {len(SCProducts)} products{Fore.RESET}", end='\r')
		CFNresponse = Inventory_Modules.find_stacks3(aws_acct, pRegion, SCProducts[i]['SCPId'])
		logging.info(f"There are {len(CFNresponse)} matches for SC Provisioned Product Name {SCProducts[i]['SCPName']}")
		try:
			if len(CFNresponse) > 0:
				stack_info = client_cfn.describe_stacks(
					StackName=CFNresponse[0]['StackName']
					)
				# The above command fails if the stack found (by the find_stacks3 function) has been deleted
				# The following section determines the NEW Account's AccountEmail and AccountID
				AccountEmail = None
				AccountID = None
				AccountStatus = None
				if 'Parameters' in stack_info['Stacks'][0].keys() and len(stack_info['Stacks'][0]['Parameters']) > 0:
					for y in range(len(stack_info['Stacks'][0]['Parameters'])):
						if stack_info['Stacks'][0]['Parameters'][y]['ParameterKey'] == 'AccountEmail':
							AccountEmail = stack_info['Stacks'][0]['Parameters'][y]['ParameterValue']
							logging.error(f"Account Email is {AccountEmail}")
				if 'Outputs' in stack_info['Stacks'][0].keys():
					for y in range(len(stack_info['Stacks'][0]['Outputs'])):
						logging.error("Output Key %s for stack %s is %s",
									  stack_info['Stacks'][0]['Outputs'][y]['OutputKey'],
									  CFNresponse[0]['StackName'],
									  stack_info['Stacks'][0]['Outputs'][y]['OutputValue'])
						if stack_info['Stacks'][0]['Outputs'][y]['OutputKey'] == 'AccountID':
							AccountID = stack_info['Stacks'][0]['Outputs'][y]['OutputValue']
							if AccountID in AccountHistogram.keys():
								AccountStatus = AccountHistogram[AccountID]
							else:
								AccountStatus = 'Closed'
							logging.error(f"{Fore.RED}Found the Account ID: {AccountID}{Fore.RESET}")
							if AccountID in SuspendedAccounts:
								logging.error(f"{Fore.RED}Account ID {AccountID} has been suspended{Fore.RESET}")
							break
						else:
							logging.error("Outputs key present, but no account ID")
							AccountID = None
							AccountStatus = None
				else:
					logging.error("No Outputs key present")
					AccountID = 'None'
					AccountStatus = 'None'
				CFNStackName = CFNresponse[0]['StackName']
				CFNStackStatus = CFNresponse[0]['StackStatus']
				# AccountEmail should have been assigned in the 'Parameters' if-then above
				# AccountID should have been assigned in the 'Outputs' if-then above
				# AccountStatus should have been assigned in the 'Outputs' if-then above
			else:  # This takes effect when CFNResponse can't find any stacks with the Service Catalog Product ID
				CFNStackName = None
				CFNStackStatus = None
				AccountID = None
				AccountEmail = None
				AccountStatus = None
			logging.error(f"AccountID: {AccountID} | AccountEmail: {AccountEmail} | CFNStackName: {CFNStackName} | CFNStackStatus: {CFNStackStatus} | SC Product: {SCProducts[i]}")
			SCProductName = SCProducts[i]['SCPName']
			SCProductId = SCProducts[i]['SCPId']
			SCStatus = SCProducts[i]['SCPStatus']
			ProvisioningArtifactName = SCProducts[i]['ProvisioningArtifactName']
			SCP2Stacks.append({
				'SCProductName': SCProductName,
				'SCProductId': SCProductId,
				'SCStatus': SCStatus,
				'ProvisioningArtifactName': ProvisioningArtifactName,
				'CFNStackName': CFNStackName,
				'CFNStackStatus': CFNStackStatus,
				'AccountEmail': AccountEmail,
				'AccountID': AccountID,
				'AccountStatus': AccountStatus
				})
		except ClientError as my_Error:
			if str(my_Error).find("ValidationError") > 0:
				print("Validation Failure ")
				print(f"Validation Failure in profile {pProfile} looking for stack {CFNresponse[0]['StackName']} with status of {CFNresponse[0]['StackStatus']}")
			elif str(my_Error).find("AccessDenied") > 0:
				print(f"{pProfile}: Access Denied Failure ")
			else:
				print(f"{pProfile}: Other kind of failure ")
				print(my_Error)

	# TODO: We should list out Suspended accounts in the SCP2Stacks readout at the end - in case any accounts have
	#  both a provisioned product, but are also suspended.
	# Do any of the account numbers show up more than once in this list?
	# We initialize the listing from the full list of accounts in the Org.
	# TODO: This might not be a good idea, if it misses the stacks which are associated with accounts no longer within the Org.
	# We add a one to each account which is represented within the Stacks listing. This allows us to catch duplicates
	# and also accounts which do not have a stack associated.
	# Note it does *not* help us catch stacks associated with an account that's been removed.
	for i in range(len(SCP2Stacks)):
		if SCP2Stacks[i]['AccountID'] == 'None':
			continue
		elif not SCP2Stacks[i]['AccountID'] in AccountHistogram.keys():
			SCP2Stacks[i]['AccountStatus'] = 'CLOSED'
			ClosedAccts.append(SCP2Stacks[i]['AccountID'])
		else:
			# This means that the value is still either "ACTIVE" or "SUSPENDED"
			if isinstance(AccountHistogram[SCP2Stacks[i]['AccountID']], str):
				AccountHistogram[SCP2Stacks[i]['AccountID']] = 1
			else:
				AccountHistogram[SCP2Stacks[i]['AccountID']] += 1
	# TODO: See if we can't update this whole thing to PrettyTable?
	DisplaySpacing = define_pretty_headings(SCP2Stacks)
	print("Account ID".ljust(DisplaySpacing['AccountNumber']),
	      "SC Product Name".ljust(DisplaySpacing['SCProductName']),
	      "Version".ljust(DisplaySpacing['ProvisioningArtifactName']),
	      "CFN StackName".ljust(DisplaySpacing['CFNStackName']),
	      "SC Status".ljust(DisplaySpacing['SCStatus']),
	      "CFN Stack Status".ljust(DisplaySpacing['CFNStackStatus']),
	      "Account Status".ljust(DisplaySpacing['AccountStatus']),
	      "Account Email".ljust(DisplaySpacing['AccountEmail']))
	# This next line just prints the "-" header under the heading names.
	print("-" * DisplaySpacing['AccountNumber'],
	      "-" * DisplaySpacing['SCProductName'],
	      "-" * DisplaySpacing['ProvisioningArtifactName'],
	      "-" * DisplaySpacing['CFNStackName'],
	      "-" * DisplaySpacing['SCStatus'],
	      "-" * DisplaySpacing['CFNStackStatus'],
	      "-" * DisplaySpacing['AccountStatus'],
	      "-" * DisplaySpacing['AccountEmail'])

	for i in range(len(SCP2Stacks)):
		if SCP2Stacks[i]['SCStatus'] == 'ERROR' or SCP2Stacks[i]['SCStatus'] == 'TAINTED':
			print(Fore.RED, end='')     # If the SC is in error - the line is written in RED.
		print(str(SCP2Stacks[i]['AccountID']).ljust(DisplaySpacing['AccountNumber']),
		      str(SCP2Stacks[i]['SCProductName']).ljust(DisplaySpacing['SCProductName']),
		      str(SCP2Stacks[i]['ProvisioningArtifactName']).ljust(DisplaySpacing['ProvisioningArtifactName']),
		      str(SCP2Stacks[i]['CFNStackName']).ljust(DisplaySpacing['CFNStackName']),
		      str(SCP2Stacks[i]['SCStatus']).ljust(DisplaySpacing['SCStatus']),
		      str(SCP2Stacks[i]['CFNStackStatus']).ljust(DisplaySpacing['CFNStackStatus']),
		      str(SCP2Stacks[i]['AccountStatus']).ljust(DisplaySpacing['AccountStatus']),
		      str(SCP2Stacks[i]['AccountEmail']).ljust(DisplaySpacing['AccountEmail'])+Fore.RESET)
except ClientError as my_Error:
	if str(my_Error).find("AuthFailure") > 0:
		print(f"{pProfile}: Authorization Failure ")
	elif str(my_Error).find("AccessDenied") > 0:
		print(f"{pProfile}: Access Denied Failure ")
	else:
		print(f"{pProfile}: Other kind of failure ")
		print(my_Error)

print()
for acctnum in AccountHistogram.keys():
	if AccountHistogram[acctnum] == 1:
		pass    # This is the desired state, so no user output is needed.
	elif AccountHistogram[acctnum] == 'SUSPENDED':
		print(f"{Fore.RED}While there is no SC Product associated, account number {acctnum} appears to be a suspended account.{Fore.RESET}")
	elif AccountHistogram[acctnum] == 'ACTIVE':  # This compare needs to be separate from below, since we can't compare a string with a "<" operator
		print(f"Account Number {Fore.RED}{acctnum}{Fore.RESET} appears to have no SC Product associated with it. This can be a problem")
	elif AccountHistogram[acctnum] < 1:
		print(f"Account Number {Fore.RED}{acctnum}{Fore.RESET} appears to have no SC Product associated with it. This can be a problem")
	elif AccountHistogram[acctnum] > 1:
		print(f"Account Number {Fore.RED}{acctnum}{Fore.RESET} appears to have multiple SC Products associated with it. This can be a problem")

if ErroredSCPExists:
	print()
	print("You probably want to remove the following SC Products:")
	session_sc = aws_acct.session
	client_sc = session_sc.client('servicecatalog')
	for i in range(len(SCP2Stacks)):
		if ((SCP2Stacks[i]['SCStatus'] == 'ERROR') or (SCP2Stacks[i]['CFNStackName'] == 'None')) and not DeletionRun:
			print(f"aws servicecatalog terminate-provisioned-product --provisioned-product-id {SCP2Stacks[i]['SCProductId']} --ignore-errors", end='')
			# Finishes the line for display, based on whether they used a profile or not to run this command
			if pProfile is None:
				print()
			elif pProfile is not None:
				print(f" --profile {pProfile}")
		elif ((SCP2Stacks[i]['SCStatus'] == 'ERROR') or (SCP2Stacks[i]['CFNStackName'] == 'None')) and DeletionRun:
			print(f"Deleting Service Catalog Provisioned Product {SCP2Stacks[i]['SCProductName']} from account {aws_acct.acct_number}")
			StackDelete = client_sc.terminate_provisioned_product(
				ProvisionedProductId=SCP2Stacks[i]['SCProductId'],
				IgnoreErrors=True,
				)
			logging.error("Result of Deletion: %s", StackDelete['RecordDetail']['Status'])
			if len(StackDelete['RecordDetail']['RecordErrors']) > 0:
				logging.error("Error code: %s", StackDelete['RecordDetail']['RecordErrors'][0]['Code'])
				logging.error("Error description: %s", StackDelete['RecordDetail']['RecordErrors'][0]['Description'])

print()
for i in AccountHistogram:
	logging.info(f"Account ID: {i} is {AccountHistogram[i]}")
end_time = time()
duration = end_time - begin_time
if pTiming:
	print(f"{Fore.GREEN}This script took {duration} seconds{Fore.RESET}")
print(f"We found {len(aws_acct.ChildAccounts)} accounts within the Org")
print(f"We found {len(SCProducts)} Service Catalog Products")
print(f"We found {len(SuspendedAccounts)} Suspended accounts")
print(f"We found {len(ClosedAccts)} Closed Accounts that still have an SC product")
# print("We found {} Service Catalog Products with no account attached".format('Some Number'))
print("Thanks for using this script...")
