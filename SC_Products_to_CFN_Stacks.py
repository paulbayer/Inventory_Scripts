#!/usr/bin/env python3

import boto3
import Inventory_Modules
import argparse
from colorama import init, Fore, Style
from botocore.exceptions import ClientError

import logging

init()

UsageMsg = "This script will correlate the Service Catalog products with the CFN Stacksets and display the account numbers associated with the SC Products. It will also make recommendations on which SC Products are ok to remove to make Landing Zone troubleshooting simpler and clearer."
parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="To specify a specific profile, use this parameter. Default will be your default profile.")
parser.add_argument(
	"-r", "--region",
	dest="pregion",
	metavar="region name string",
	default="us-east-1",
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
	"+d", "+delete",
	dest="DeletionRun",
	metavar="Deletion of inactive Service Catalog provisioned products",
	const=True,
	default=False,
	action="store_const",
	help="This will delete the SC Provisioned Products found to be in error, or without active CloudFormation stacks - without any opportunity to confirm. Be careful!!")
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
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,  # args.loglevel = 10
	default=logging.CRITICAL)  # args.loglevel = 50
args = parser.parse_args()

pProfile = args.pProfile
pRegion = args.pregion
verbose = args.loglevel
DeletionRun = args.DeletionRun
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")


##########################
def sort_by_email(elem):
	return elem('AccountEmail')


##########################
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

ERASE_LINE = '\x1b[2K'

print()

SCP2Stacks = []
SCProducts = []
ErroredSCPExists = False
session_aws = boto3.Session(profile_name=pProfile, region_name=pRegion)
client_org = session_aws.client('organizations')
client_cfn = session_aws.client('cloudformation')

AcctList = Inventory_Modules.find_child_accounts2(pProfile)
AccountHistogram = {}
SuspendedAccounts=[]
for account in AcctList:
	AccountHistogram[account['AccountId']] = account['AccountStatus']
	if account['AccountStatus'] == 'SUSPENDED':
		SuspendedAccounts.append(account['AccountId'])

try:
	SCresponse = Inventory_Modules.find_sc_products(pProfile, pRegion, "All",10)
	logging.warning("A list of the SC Products found:")
	for i in range(len(SCresponse)):
		logging.warning("SC Product Name %s | SC Product Status %s", SCresponse[i]['Name'], SCresponse[i]['Status'])
		SCProducts.append({
			'SCPName': SCresponse[i]['Name'],
			'SCPId': SCresponse[i]['Id'],
			'SCPStatus': SCresponse[i]['Status'],
			'SCPRecordId': SCresponse[i]['LastRecordId'],
			'ProvisioningArtifactName': SCresponse[i]['ProvisioningArtifactName']
		})
		if SCresponse[i]['Status'] == 'ERROR' or SCresponse[i]['Status'] == 'TAINTED':
			ErroredSCPExists = True

	CFNStacks = Inventory_Modules.find_stacks(pProfile, pRegion, 'SC-' + Inventory_Modules.find_account_number(pProfile))
	SCresponse = None
	for i in range(len(SCProducts)):
		print(ERASE_LINE, Fore.RED + "Checking {} of {} products".format(i + 1, len(SCProducts)) + Fore.RESET, end='\r')
		CFNresponse = Inventory_Modules.find_stacks(pProfile, pRegion, SCProducts[i]['SCPId'])
		logging.error("There are %s matches for SC Provisioned Product Name %s", len(CFNresponse),
		              SCProducts[i]['SCPName'])
		try:
			if len(CFNresponse) > 0:
				stack_info = client_cfn.describe_stacks(
					StackName=CFNresponse[0]['StackName']
				)
				# The above command fails if the stack found (by the find_stacks function) has been deleted
				# The following section determines the NEW Account's AccountEmail and AccountID
				AccountEmail = 'None'
				AccountID = 'None'
				if 'Parameters' in stack_info['Stacks'][0].keys() and len(stack_info['Stacks'][0]['Parameters']) > 0:
					for y in range(len(stack_info['Stacks'][0]['Parameters'])):
						if stack_info['Stacks'][0]['Parameters'][y]['ParameterKey'] == 'AccountEmail':
							AccountEmail = stack_info['Stacks'][0]['Parameters'][y]['ParameterValue']
							logging.error("Account Email is %s" % AccountEmail)
				if 'Outputs' in stack_info['Stacks'][0].keys():
					for y in range(len(stack_info['Stacks'][0]['Outputs'])):
						logging.error("Output Key %s for stack %s is %s",
						              stack_info['Stacks'][0]['Outputs'][y]['OutputKey'], CFNresponse[0]['StackName'],
						              stack_info['Stacks'][0]['Outputs'][y]['OutputValue'])
						if stack_info['Stacks'][0]['Outputs'][y]['OutputKey'] == 'AccountID':
							AccountID = stack_info['Stacks'][0]['Outputs'][y]['OutputValue']
							if AccountID in AccountHistogram.keys():
								AccountStatus=AccountHistogram[AccountID]
							else:
								AccountStatus='Closed'
							logging.error(Fore.RED + "Found the Account ID: %s" % AccountID + Fore.RESET)
							if AccountID in SuspendedAccounts:
								logging.error(Fore.RED + "Account ID %s has been suspended" + Fore.RESET, AccountID)
							break
						else:
							logging.error("Outputs key present, but no account ID")
							AccountID='None'
							AccountStatus='None'
				else:
					logging.error("No Outputs key present")
					AccountID='None'
					AccountStatus='None'
				CFNStackName = CFNresponse[0]['StackName']
				CFNStackStatus = CFNresponse[0]['StackStatus']
				# AccountEmail should have been assigned in the 'Parameters' if-then above
				# AccountID should have been assigned in the 'Outputs' if-then above
				# AccountStatus should have been assigned in the 'Outputs' if-then above
			else:  # This takes effect when CFNResponse can't find any stacks with the Service Catalog Product ID
				CFNStackName = 'None'
				CFNStackStatus = 'None'
				AccountID = 'None'
				AccountEmail = 'None'
				AccountStatus = 'None'
			logging.error("AccountID: %s | AccountEmail: %s | CFNStackName: %s | CFNStackStatus: %s | SC Product: %s" % (AccountID, AccountEmail, CFNStackName, CFNStackStatus, SCProducts[i]))
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
				print("Validation Failure in profile {} looking for stack {} with status of {}".format(pProfile, CFNresponse[0]['StackName'], CFNresponse[0]['StackStatus']))
			elif str(my_Error).find("AccessDenied") > 0:
				print(pProfile + ": Access Denied Failure ")
			else:
				print(pProfile + ": Other kind of failure ")
				print(my_Error)

	# TODO: We should list out Suspended accounts in the SCP2Stacks readout at the end - in case any accounts have both a provisioned product, but are also suspended.

	# Do any of the account numbers show up more than once in this list?
	## We initialize the listing from the full list of accounts in the Org.
	## TODO: This might not be a good idea, if it misses the stacks which are associated with accounts no longer within the Org.
	## We add a one to each account which is represented within the Stacks listing. This allows us to catch duplicates and also accounts which do not have a stack associated.
	## Note it does *not* help us catch stacks associated with an account that's been removed.
	for i in range(len(SCP2Stacks)):
		if SCP2Stacks[i]['AccountID'] == 'None':
			continue
		elif not SCP2Stacks[i]['AccountID'] in AccountHistogram.keys():
			SCP2Stacks[i]['AccountStatus'] = 'CLOSED'
		else:
			if isinstance(AccountHistogram[SCP2Stacks[i]['AccountID']], str):   # This means that the value is still either "ACTIVE" or "SUSPENDED"
				AccountHistogram[SCP2Stacks[i]['AccountID']] = 1
			else:
				AccountHistogram[SCP2Stacks[i]['AccountID']] += 1
	namelength=0
	for _ in range(len(SCP2Stacks)):
		if namelength < len(SCP2Stacks[_]['SCProductName']):
			namelength=len(SCP2Stacks[_]['SCProductName'])
		else:
			pass
	print()
	fmt='{0:<15} {1:{namelength}} {2:<8} {3:<35} {4:<10} {5:<18} {6:<10} {7:<20}'
	print(fmt.format("Account Number",
                   "SC Product Name", "Version",
                   "CFN Stack Name",
                   "SC Status",
                   "CFN Stack Status",
                   "Acct Status",
                   "AccountEmail",
                   namelength=namelength))
	print(fmt.format("--------------", "---------------", "-------","--------------", "---------", "----------------", "-----------", "------------",namelength=namelength))
	for i in range(len(SCP2Stacks)):
		if SCP2Stacks[i]['SCStatus'] == 'ERROR' or SCP2Stacks[i]['SCStatus'] == 'TAINTED':
			print(Fore.RED+fmt.format(SCP2Stacks[i]['AccountID'],
                            SCP2Stacks[i]['SCProductName'],
                            SCP2Stacks[i]['ProvisioningArtifactName'],
                            SCP2Stacks[i]['CFNStackName'],
                            SCP2Stacks[i]['SCStatus'],
                            SCP2Stacks[i]['CFNStackStatus'],
                            SCP2Stacks[i]['AccountStatus'],
                            SCP2Stacks[i]['AccountEmail'],
                            namelength=namelength)+Fore.RESET)
		else:
			print(fmt.format(
				SCP2Stacks[i]['AccountID'],
				SCP2Stacks[i]['SCProductName'],
				SCP2Stacks[i]['ProvisioningArtifactName'],
				SCP2Stacks[i]['CFNStackName'],
				SCP2Stacks[i]['SCStatus'],
				SCP2Stacks[i]['CFNStackStatus'],
				SCP2Stacks[i]['AccountStatus'],
				SCP2Stacks[i]['AccountEmail'],
				namelength=namelength))

except ClientError as my_Error:
	if str(my_Error).find("AuthFailure") > 0:
		print(pProfile + ": Authorization Failure ")
	elif str(my_Error).find("AccessDenied") > 0:
		print(pProfile + ": Access Denied Failure ")
	else:
		print(pProfile + ": Other kind of failure ")
		print(my_Error)

print()
for acctnum in AccountHistogram.keys():
	if AccountHistogram[acctnum] == 1:
		pass    # This is the desired state, so no user output is needed.
	elif AccountHistogram[acctnum] == 'SUSPENDED':
		print(Fore.RED+"While there is no SC Product associated, account number {} appears to be a suspended account.".format(acctnum)+Fore.RESET)
	elif AccountHistogram[acctnum] == 'ACTIVE':  # This compare needs to be separate from below, since we can't compare a string with a "<" operator
		print("Account Number "+Fore.RED+"{}".format(acctnum)+Fore.RESET+" appears to have no SC Product associated with it. This can be a problem")
	elif AccountHistogram[acctnum] < 1:
		print("Account Number "+Fore.RED+"{}".format(acctnum)+Fore.RESET+" appears to have no SC Product associated with it. This can be a problem")
	elif AccountHistogram[acctnum] > 1:
		print("Account Number "+Fore.RED+"{}".format(acctnum)+Fore.RESET+" appears to have multiple SC Products associated with it. This can be a problem")

if ErroredSCPExists:
	print()
	print("You probably want to remove the following SC Products:")
	session_sc = boto3.Session(profile_name=pProfile, region_name=pRegion)
	client_sc = session_sc.client('servicecatalog')
	for i in range(len(SCP2Stacks)):
		if (SCP2Stacks[i]['SCStatus'] == 'ERROR') or (SCP2Stacks[i]['CFNStackName'] == 'None') and not DeletionRun:
			print(
				"aws servicecatalog terminate-provisioned-product --provisioned-product-id {} --profile {} --ignore-errors".format(
					SCP2Stacks[i]['SCProductId'], pProfile))
		elif (SCP2Stacks[i]['SCStatus'] == 'ERROR') or (SCP2Stacks[i]['CFNStackName'] == 'None') and DeletionRun:
			print(
				"Deleting Service Catalog Provisioned Product {} from {} profile".format(SCP2Stacks[i]['SCProductName'],
				                                                                         pProfile))
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
	logging.info("Account ID: %s is %s" % (i, AccountHistogram[i]))
	# if AccountHistogram[i]
print("We found {} accounts within the Org".format(len(AcctList)))
print("We found {} Service Catalog Products".format(len(SCProducts)))
print("We found {} Suspended accounts".format(len(SuspendedAccounts)))
print("We found {} Closed Accounts that still have an SC product".format('Some Number'))
print("We found {} Service Catalog Products with no account attached".format('Some Number'))
print("Thanks for using this script...")
