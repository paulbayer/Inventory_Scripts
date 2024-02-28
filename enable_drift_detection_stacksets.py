#!/usr/bin/env python3


import logging
import sys
from os.path import split

from botocore.exceptions import ClientError
from colorama import Fore, init

import Inventory_Modules
from ArgumentsClass import CommonArguments
from Inventory_Modules import display_results
from account_class import aws_acct_access

init()
__version__ = "2024.02.27"


def parse_args(args):
	script_path, script_name = split(sys.argv[0])
	parser = CommonArguments()
	parser.singleprofile()
	parser.multiregion()
	parser.extendedargs()
	parser.fragment()
	parser.save_to_file()
	parser.timing()
	parser.verbosity()
	parser.version(__version__)
	local = parser.my_parser.add_argument_group(script_name, 'Parameters specific to this script')

	# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
	# local.add_argument(
	# 		"-f", "--fragment",
	# 		dest="pstacksetfrag",
	# 		metavar="CloudFormation StackSet fragment",
	# 		default="all",
	# 		nargs="+",
	# 		help="String fragment of the cloudformation stackset(s) you want to check for.")
	local.add_argument(
		"-s", "--status",
		dest="pstatus",
		metavar="CloudFormation status",
		default="active",
		help="String that determines whether we only see 'CREATE_COMPLETE' or 'DELETE_COMPLETE' too")
	# local.add_argument(
	# 		"-k", "--skip",
	# 		dest="pSkipAccounts",
	# 		nargs="*",
	# 		metavar="Accounts to leave alone",
	# 		default=[],
	# 		help="These are the account numbers you don't want to screw with. Likely the core accounts.")
	return (parser.my_parser.parse_args(args))


def find_stack_sets(faws_acct: aws_acct_access, fStackSetFragmentlist: list = None, fExact: bool = False):
	if fStackSetFragmentlist is None:
		fStackSetFragmentlist = ['all']
	StackSets = {'Success': False, 'ErrorMessage': '', 'StackSets': {}}
	try:
		StackSets = Inventory_Modules.find_stacksets3(faws_acct, faws_acct.Region, fStackSetFragmentlist, fExact)
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			error_message = (f"{MgmtAccount['AccountId']}: Authorization Failure")
			logging.error(error_message)
		else:
			error_message = f"Error: {my_Error}"
			logging.error(error_message)
		StackSets['ErrorMessage'] = error_message
	except Exception as my_Error:
		error_message = f"Error: {my_Error}"
		logging.error(error_message)
		StackSets['ErrorMessage'] = error_message
	return(StackSets)


def enable_stack_set_drift_detection(faws_acct: aws_acct_access, fStackSets: dict = None):
	if len(fStackSets) == 0:
		logging.info(f"We connected to account {faws_acct.acct_number} in region {aws_acct.Region}, but found no stacksets")
	else:
		logging.info(f"Account: {faws_acct.acct_number} | Region: {aws_acct.Region} | Found {len(fStackSets)} Stacksets")
	for stackset_name, stackset_attributes in fStackSets.items():
		try:
			# TODO: Eventually will need to multi-thread this...
			DriftStatus = Inventory_Modules.enable_drift_on_stackset3(faws_acct, stackset_name)
			stackset_attributes['AccountNumber'] = faws_acct.acct_number
			stackset_attributes['Region'] = faws_acct.Region
			if DriftStatus['Success']:
				stackset_attributes['DriftStatus_Operation'] = DriftStatus['OperationId']
			else:
				stackset_attributes['DriftStatus_Operation'] = DriftStatus['Success']
				stackset_attributes['ErrorMessage'] = DriftStatus['ErrorMessage']
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"{MgmtAccount['AccountId']}: Authorization Failure")
			continue

	return (fStackSets)


##################
# Main
##################
if __name__ == '__main__':
	args = parse_args(sys.argv[1:])
	pProfile = args.Profile
	pRegionList = args.Regions
	pFragments = args.Fragments
	pExact = args.Exact
	pstatus = args.pstatus
	pFilename = args.Filename
	pTiming = args.Time
	AccountsToSkip = args.SkipAccounts
	ProfilesToSkip = args.SkipProfiles
	pAccounts = args.Accounts
	pSaveFilename = args.Filename
	verbose = args.loglevel

	logging.getLogger("boto3").setLevel(logging.CRITICAL)
	logging.getLogger("botocore").setLevel(logging.CRITICAL)
	logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
	logging.getLogger("urllib3").setLevel(logging.CRITICAL)
	# Set Log Level
	logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
	"""
	We should eventually create an argument here that would check on the status of the drift-detection using
	"describe_stack_drift_detection_status", but we haven't created that function yet... 
	https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation.html#CloudFormation.Client.describe_stack_drift_detection_status
	"""

	##########################
	ERASE_LINE = '\x1b[2K'

	aws_acct = aws_acct_access(pProfile)
	# sts_client = aws_acct.session.client('sts')

	MgmtAccount = {'MgmtAccount'  : aws_acct.acct_number,
	               'AccountId'    : aws_acct.acct_number,
	               'AccountEmail' : aws_acct.MgmtEmail,
	               'AccountStatus': aws_acct.AccountStatus}

	RegionList = Inventory_Modules.get_service_regions('cloudformation', pRegionList)

	# Find StackSets to operate on and get the last detection status
	StackSets = find_stack_sets(aws_acct, pFragments, pExact)
	# Determine whether we want to update this status or not -

	# Enable drift_detection on those stacksets
	Drift_Status = enable_stack_set_drift_detection(aws_acct, StackSets['StackSets'])
	# Report back on drift from given stacksets

	display_dict = {'AccountId'   : {'DisplayOrder': 1, 'Heading': 'Acct Number'},
	                'Region'      : {'DisplayOrder': 2, 'Heading': 'Region'},
	                'DriftStatus' : {'DisplayOrder': 3, 'Heading': 'Drift Status'},
	                'StackSetName': {'DisplayOrder': 4, 'Heading': 'Stack Set Name'},
	                'StackSetId'  : {'DisplayOrder': 5, 'Heading': 'Stack Set ID'}}

	AllStackSets = get_stack_set_drift_status(aws_acct, pRegionList)

	sorted_all_stacksets = sorted(AllStackSets, key=lambda x: (x['AccountId'], x['Region'], x['StackSetName']))

	# Display results
	display_results(sorted_all_stacksets, display_dict, None, pSaveFilename)

	print(ERASE_LINE)
	print(f"{Fore.RED}Looked through {len(AllStackSets)} StackSets across Management account across "
	      f"{len(RegionList)} regions{Fore.RESET}")
	print()

	print("Thanks for using this script...")
	print()
