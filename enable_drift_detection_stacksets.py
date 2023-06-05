#!/usr/bin/env python3


import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()
__version__ = "2023.05.04"

parser = CommonArguments()
parser.singleprofile()
parser.multiregion()
parser.verbosity()
parser.version(__version__)

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser.my_parser.add_argument(
		"-f", "--fragment",
		dest="pstacksetfrag",
		metavar="CloudFormation StackSet fragment",
		default="all",
		help="String fragment of the cloudformation stackset(s) you want to check for.")
parser.my_parser.add_argument(
		"-s", "--status",
		dest="pstatus",
		metavar="CloudFormation status",
		default="active",
		help="String that determines whether we only see 'CREATE_COMPLETE' or 'DELETE_COMPLETE' too")
parser.my_parser.add_argument(
		"-k", "--skip",
		dest="pSkipAccounts",
		nargs="*",
		metavar="Accounts to leave alone",
		default=[],
		help="These are the account numbers you don't want to screw with. Likely the core accounts.")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegionList = args.Regions
pstacksetfrag = args.pstacksetfrag
pstatus = args.pstatus
AccountsToSkip = args.pSkipAccounts
verbose = args.loglevel
logging.basicConfig(level=args.loglevel,
                    format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")

"""
We should eventually create an argument here that would check on the status of the drift-detection using
"describe_stack_drift_detection_status", but we haven't created that function yet...  
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation.html#CloudFormation.Client.describe_stack_drift_detection_status
"""

##########################
ERASE_LINE = '\x1b[2K'

aws_acct = aws_acct_access(pProfile)
sts_client = aws_acct.session.client('sts')

MgmtAccount = {'MgmtAccount' : aws_acct.acct_number,
	'AccountId'    : aws_acct.acct_number,
	'AccountEmail' : aws_acct.MgmtEmail,
	'AccountStatus': aws_acct.AccountStatus}

NumStackSetsFound = 0
print()
RegionList = Inventory_Modules.get_service_regions('cloudformation', pRegionList)

fmt = '%-20s %-15s %-15s %-50s'
print(fmt % ("Account", "Region", "StackSet Status", "StackSet Name"))
print(fmt % ("-------", "------", "---------------", "-------------"))

StackSetsFound = []
try:
	account_credentials = Inventory_Modules.get_child_access3(aws_acct, MgmtAccount['AccountId'], )
	if account_credentials['AccessError']:
		logging.error(f"Accessing account {MgmtAccount['AccountId']} didn't work, so we're skipping it")
except ClientError as my_Error:
	if str(my_Error).find("AuthFailure") > 0:
		print(f"{pProfile}: Authorization Failure for account {MgmtAccount['AccountId']}")
	elif str(my_Error).find("AccessDenied") > 0:
		print(f"{pProfile}: Access Denied Failure for account {MgmtAccount['AccountId']}")
	else:
		print(f"{pProfile}: Other kind of failure for account {MgmtAccount['AccountId']}")
		print(my_Error)

for region in RegionList:
	StackSets = []
	try:
		StackSetNum = 0
		StackSets = Inventory_Modules.find_stacksets2(account_credentials, region, pstacksetfrag, pstatus)
		logging.warning(f"Account: {MgmtAccount['AccountId']} | Region: {region} | Found {len(StackSets)} Stacksets")
		if not StackSets:
			logging.info(
				f"We connected to account {MgmtAccount['AccountId']} in region {region}, but found no stacksets")
		else:
			print(
				f"{ERASE_LINE}{Fore.RED}Account: {MgmtAccount['AccountId']} Region: {region} Found {len(StackSets)} Stacksets{Fore.RESET}",
				end="\r")
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{MgmtAccount['AccountId']}: Authorization Failure")

	for StackSet in StackSets:
		StackSetName = StackSet['StackSetName']
		StackSetStatus = StackSet['Status']
		DriftStatus = Inventory_Modules.enable_drift_on_stack_set(account_credentials, region, StackSetName)
		logging.error(
			f"Enabled drift detection on {StackSetName} in account {account_credentials['AccountNumber']} in region {region}")
		NumStackSetsFound += 1

print(ERASE_LINE)
print(f"{Fore.RED}Looked through {NumStackSetsFound} Stacks across Management account across "
      f"{len(RegionList)} regions{Fore.RESET}")
print()

print("Thanks for using this script...")
print()
