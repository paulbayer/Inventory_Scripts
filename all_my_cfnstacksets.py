#!/usr/bin/env python3

import logging
import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

init()

parser = CommonArguments()
parser.singleprofile()  # Allows for a single profile to be specified
parser.multiregion()  # Allows for multiple regions to be specified at the command line
parser.rootOnly()
parser.verbosity()  # Allows for the verbosity to be handled.
parser.my_parser.add_argument(
	"-f", "--fragment",
	dest="pstackfrag",
	nargs='*',
	metavar="CloudFormation stack fragment",
	default=["all"],
	help="List of fragments of the cloudformation stackset(s) you want to check for.")
parser.my_parser.add_argument(
	"-i", "--instances",
	dest="pinstancecount",
	action="store_true",
	default=False,
	help="Flag to determine whether you want to see the instance totals for each stackset")
parser.my_parser.add_argument(
	"-s", "--status",
	dest="pstatus",
	metavar="CloudFormation status",
	default="Active",
	help="String that determines whether we only see 'CREATE_COMPLETE' or 'DELETE_COMPLETE' too. Valid values are 'ACTIVE' or 'DELETED'")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegionList = args.Regions
pInstanceCount = args.pinstancecount
pRootOnly = args.RootOnly
verbose = args.loglevel
pstackfrag = args.pstackfrag
pstatus = args.pstatus
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

aws_acct = aws_acct_access(pProfile)
if pRootOnly:
	ChildAccounts = [childaccount for childaccount in aws_acct.ChildAccounts if
	                 childaccount['AccountId'] == aws_acct.acct_number]
else:
	ChildAccounts = aws_acct.ChildAccounts

NumStacksFound = 0
##########################
ERASE_LINE = '\x1b[2K'

print()
# TODO: Gotta find a way to dynamically size the columns below
if pInstanceCount:
	fmt = '%-20s %-15s %-15s %-50s %-5s'
	print(fmt % ("Account", "Region", "Status", "StackSet Name", "# of instances"))
	print(fmt % ("-------", "------", "------", "-------------", "--------------"))
else:
	fmt = '%-20s %-15s %-15s %-50s'
	print(fmt % ("Account", "Region", "Status", "StackSet Name"))
	print(fmt % ("-------", "------", "------", "-------------"))
RegionList = Inventory_Modules.get_ec2_regions3(aws_acct, pRegionList)

sts_session = aws_acct.session
sts_client = sts_session.client('sts')
account_credentials = {'AccessError': False}  # This shouldn't matter, but makes the IDE checker happy.
for account in ChildAccounts:
	try:
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, account['AccountId'])
		if account_credentials['AccessError']:
			logging.error(f"Accessing account {account['AccountId']} didn't work, so we're skipping it")
			continue
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0 or str(my_Error).find("AccessDenied") > 0:
			logging.error("%s: Authorization Failure for account %s", pProfile, account['AccountId'])
			continue
		else:
			print(my_Error)
			break
	# logging.info(f"Account Creds: {account_credentials}")
	for region in RegionList:
		try:
			print(
				f"{ERASE_LINE}{Fore.RED}Checking Account: {account['AccountId']} Region: {region} for stacksets matching {pstackfrag} with status: {pstatus}{Fore.RESET}",
				end="\r")
			StackSets = Inventory_Modules.find_stacksets2(account_credentials, region, pstackfrag, pstatus)
			logging.warning(f"Account: {account['AccountId']} | Region: {region} | Found {len(StackSets)} Stacksets")
			if not StackSets:
				logging.info(
					f"We connected to account {account['AccountId']} in region {region}, but found no stacksets")
			else:
				print(
					f"{ERASE_LINE}{Fore.RED}Account: {account['AccountId']} Region: {region} Found {len(StackSets)} Stacksets{Fore.RESET}",
					end="\r")
			for y in range(len(StackSets)):
				StackName = StackSets[y]['StackSetName']
				StackStatus = StackSets[y]['Status']
				if pInstanceCount:
					ListOfStackInstances = Inventory_Modules.find_stack_instances2(account_credentials, region, StackName)
					print(fmt % (account['AccountId'], region, StackStatus, StackName, len(ListOfStackInstances)))
				else:
					print(fmt % (account['AccountId'], region, StackStatus, StackName))
				NumStacksFound += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{account['AccountId']}: Authorization Failure")
print(ERASE_LINE)
print(
	f"{Fore.RED}Found {NumStacksFound} Stacksets across {len(ChildAccounts)} accounts across {len(RegionList)} regions{Fore.RESET}")
print()
print("Thanks for using this script...")
