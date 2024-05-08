#!/usr/bin/env python3

import sys
from os.path import split
from time import time
from tqdm.auto import tqdm
from Inventory_Modules import find_iam_users2, display_results, get_all_credentials, find_idc_users2, find_idc_directory_id2
from ArgumentsClass import CommonArguments
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()
__version__ = "2024.05.07"
ERASE_LINE = '\x1b[2K'
begin_time = time()


##################
# Functions
##################
def parse_args(arguments):
	"""
	Description: Parses the arguments passed into the script
	@param arguments: args represents the list of arguments passed in
	@return: returns an object namespace that contains the individualized parameters passed in
	"""
	script_path, script_name = split(sys.argv[0])
	parser = CommonArguments()
	parser.my_parser.description = "We're going to find all IAM users within any of the accounts we have access to, given the profile(s) provided."
	parser.multiprofile()
	parser.multiregion()
	parser.extendedargs()
	parser.rootOnly()
	parser.rolestouse()
	parser.save_to_file()
	parser.verbosity()
	parser.timing()
	parser.version(__version__)
	local = parser.my_parser.add_argument_group(script_name, 'Parameters specific to this script')
	local.add_argument(
		"--idc",
		dest="pIdentityCenter",
		action="store_true",  # Defaults to False
		help="Flag that determines whether look for Identity Center users")
	local.add_argument(
		"--iam",
		dest="pIAM",
		action="store_true",  # Defaults to False
		help="Flag that determines whether look for IAM users ")
	return parser.my_parser.parse_args(arguments)


def find_all_org_users(f_credentials, f_IDC: bool, f_IAM: bool) -> list:
	User_List = []
	directories_seen = set()
	for credential in tqdm(f_credentials, desc=f"Looking for users across {len(f_credentials)} Accounts"):
		if not credential['Success']:
			logging.info(f"{credential['ErrorMessage']} with roles: {credential['RolesTried']}")
			continue
		if f_IAM:
			try:
				User_List.extend(find_iam_users2(credential))
			# logging.info(f"{ERASE_LINE}Account: {credential['AccountId']} Found {len(User_List)} users")
			except ClientError as my_Error:
				if 'AuthFailure' in str(my_Error):
					logging.error(f"{ERASE_LINE}{credential}: Authorization Failure")
		if f_IDC:
			try:
				# Find out if this account hosts an IDC with a user directory
				directory_ids = find_idc_directory_id2(credential)
				for directory_instance_id in directory_ids:
					# If we've already interrogated this one before... don't do it again
					if directory_instance_id in directories_seen:
						continue
					else:
						directories_seen.update(directory_ids)
						User_List.extend(find_idc_users2(credential, directory_instance_id))
			# logging.info(f"{ERASE_LINE}Account: {credential['AccountId']} Found {len(User_List)} users")
			except ClientError as my_Error:
				if 'AuthFailure' in str(my_Error):
					logging.error(f"{ERASE_LINE}{credential}: Authorization Failure")
	return User_List


##################
# Main
##################

if __name__ == '__main__':
	args = parse_args(sys.argv[1:])
	pProfiles = args.Profiles
	pRegionList = args.Regions
	pAccounts = args.Accounts
	pSkipAccounts = args.SkipAccounts
	pSkipProfiles = args.SkipProfiles
	pAccessRoles = args.AccessRoles
	pFilename = args.Filename
	pIdentityCenter = args.pIdentityCenter
	pIAM = args.pIAM
	pRootOnly = args.RootOnly
	pTiming = args.Time
	verbose = args.loglevel
	logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
	logging.getLogger("boto3").setLevel(logging.CRITICAL)
	logging.getLogger("botocore").setLevel(logging.CRITICAL)
	logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
	logging.getLogger("urllib3").setLevel(logging.CRITICAL)

	CredentialList = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList, pAccessRoles)
	UserListing = find_all_org_users(CredentialList, pIdentityCenter, pIAM)
	sorted_UserListing = sorted(UserListing, key=lambda k: (k['MgmtAccount'], k['AccountId'], k['Region'], k['UserName']))


	display_dict = {'MgmtAccount'     : {'DisplayOrder': 1, 'Heading': 'Mgmt Acct'},
	                'AccountId'       : {'DisplayOrder': 2, 'Heading': 'Acct Number'},
	                'Region'          : {'DisplayOrder': 3, 'Heading': 'Region'},
	                'UserName'        : {'DisplayOrder': 4, 'Heading': 'User Name'},
	                'PasswordLastUsed': {'DisplayOrder': 5, 'Heading': 'Last Used'},
	                'Type'            : {'DisplayOrder': 6, 'Heading': 'Source'},
	                }
	display_results(sorted_UserListing, display_dict, 'N/A', pFilename)
	if pTiming:
		print(ERASE_LINE)
		print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
	print(ERASE_LINE)
	print(f"Found {len(UserListing)} users across {len(CredentialList)} accounts")
	print()
	print("Thank you for using this script")
	print()
