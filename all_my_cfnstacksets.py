#!/usr/bin/env python3

import logging
import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

init()
parser = CommonArguments()
parser.singleprofile()      # Allows for a single profile to be specified
parser.multiregion()        # Allows for multiple regions to be specified at the command line
parser.verbosity()          # Allows for the verbosity to be handled.
parser.my_parser.add_argument(
	"-f", "--fragment",
	dest="pstackfrag",
	metavar="CloudFormation stack fragment",
	default=["all"],
	help="String fragment of the cloudformation stack or stackset(s) you want to check for.")
parser.my_parser.add_argument(
	"-s", "--status",
	dest="pstatus",
	metavar="CloudFormation status",
	default="active",
	help="String that determines whether we only see 'CREATE_COMPLETE' or 'DELETE_COMPLETE' too. Valid values are 'ACTIVE' or 'DELETED'")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegionList = args.Regions
verbose = args.loglevel
pstackfrag = args.pstackfrag
pstatus = args.pstatus
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")

SkipProfiles = ["default"]
aws_acct = aws_acct_access(pProfile)
ChildAccounts = aws_acct.ChildAccounts

NumStacksFound = 0
##########################
ERASE_LINE = '\x1b[2K'

print()
fmt = '%-20s %-15s %-15s %-50s'
print(fmt % ("Account", "Region", "Status", "StackSet Name"))
print(fmt % ("-------", "------", "------", "-------------"))
RegionList = Inventory_Modules.get_ec2_regions(pRegionList)

sts_session = aws_acct.session
sts_client = sts_session.client('sts')
account_credentials = None      # This shouldn't matter, but makes the IDE checker happy.
for account in ChildAccounts:
	try:
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, account['AccountId'])

	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0 or str(my_Error).find("AccessDenied") > 0:
			logging.error("%s: Authorization Failure for account %s", pProfile, account['AccountId'])
			continue
	for region in RegionList:
		try:
			print(ERASE_LINE, f"{Fore.RED}Checking Account: ", account['AccountId'], "Region: ", region+Fore.RESET, end="\r")
			StackSets = Inventory_Modules.find_stacksets2(account_credentials, region, account['AccountId'], pstackfrag)
			logging.warning("Account: %s | Region: %s | Found %s Stacksets", account['AccountId'], region, len(StackSets))
			if not StackSets == []:
				print(ERASE_LINE, f"{Fore.RED}Account: ", account['AccountId'], "Region: ", region, "Found", len(StackSets), f"Stacksets{Fore.RESET}", end="\r")
			for y in range(len(StackSets)):
				StackName = StackSets[y]['StackSetName']
				StackStatus = StackSets[y]['Status']
				print(fmt % (account['AccountId'], region, StackStatus, StackName))
				NumStacksFound += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{account['AccountId']}: Authorization Failure")
print(ERASE_LINE)
print(f"{Fore.RED}Found", NumStacksFound, "Stacksets across", len(ChildAccounts), "accounts across", len(RegionList), f"regions{Fore.RESET}")
print()
print("Thanks for using this script...")
