#!/usr/bin/env python3
import sys

from Inventory_Modules import display_results, get_all_credentials, find_in
import boto3
import simplejson as json
from ArgumentsClass import CommonArguments
from time import sleep, time
from colorama import init, Fore
from botocore.exceptions import ClientError
import logging
from json.decoder import JSONDecodeError


init()
__version__ = "2025.04.15"

#
# iam = boto3.client('iam')
#
# response = iam.get_role(RoleName='YourRoleName')
# trust_policy = response['Role']['AssumeRolePolicyDocument']
# print(json.dumps(trust_policy, indent=4))
#

###########################
def parse_args(f_args):
	"""
	Description: Parses the arguments passed into the script
	@param f_args: args represents the list of arguments passed in
	@return: returns an object namespace that contains the individualized parameters passed in
	"""
	parser = CommonArguments()
	parser.my_parser.description = "We're going to find all roles within any of the accounts we have access to, given the profile(s) provided."
	parser.multiprofile()
	parser.multiregion()
	parser.extendedargs()
	parser.fragment()
	parser.deletion()
	parser.rootOnly()
	parser.verbosity()
	parser.timing()
	parser.save_to_file()
	parser.version(__version__)
	parser.my_parser.add_argument(
		"--policy",
		dest="pPolicy",
		metavar="Policy file to attach to the role",
		default=None,
		help="Policy you'd like attached to role in child accounts.")
	return parser.my_parser.parse_args(f_args)


def find_and_collect_roles_across_accounts(fAllCredentials:list, frole_fragments:list) -> list:
	"""
	TODO: Need to add multi-threading here
	Description: Finds roles in Org Accounts that contains supplied fragments
	@param fAllCredentials: Listing of Credentials
	@param frole_fragments: list of strings to find roles that match
	@return: List of roles found across all accounts
	"""
	print()
	if pFragments is None:
		print(f"Listing out all roles across {len(fAllCredentials)} accounts")
		print()
	elif pExact:
		print(f"Looking for a role {Fore.RED}exactly{Fore.RESET} named one of these strings {frole_fragments} across {len(fAllCredentials)} accounts")
		print()
	else:
		print(f"Looking for a role containing one of these strings {frole_fragments} across {len(fAllCredentials)} accounts")
		print()

	Roles = []
	for account in fAllCredentials:
		if account['Success']:
			iam_session = boto3.Session(aws_access_key_id=account['AccessKeyId'],
			                            aws_secret_access_key=account['SecretAccessKey'],
			                            aws_session_token=account['SessionToken'],
			                            region_name=account['Region'])
			iam_client = iam_session.client('iam')
		else:
			continue
		try:
			response = iam_client.list_roles()
			for i in range(len(response['Roles'])):
				Roles.append({
					'AccessKeyId'    : account['AccessKeyId'],
					'SecretAccessKey': account['SecretAccessKey'],
					'SessionToken'   : account['SessionToken'],
					'MgmtAcct'       : account['MgmtAccount'],
					'Region'         : account['Region'],
					'AccountId'      : account['AccountNumber'],
					'RoleName'       : response['Roles'][i]['RoleName']
				})
			num_of_roles_in_account = len(response['Roles'])
			while response['IsTruncated']:
				response = iam_client.list_roles(Marker=response['Marker'])
				for i in range(len(response['Roles'])):
					Roles.append({
						'AccessKeyId'    : account['AccessKeyId'],
						'SecretAccessKey': account['SecretAccessKey'],
						'SessionToken'   : account['SessionToken'],
						'MgmtAcct'       : account['MgmtAccount'],
						'Region'         : account['Region'],
						'AccountId'      : account['AccountNumber'],
						'RoleName'       : response['Roles'][i]['RoleName']
					})
				num_of_roles_in_account = len(response['Roles'])
			print(f"Found {num_of_roles_in_account} roles in account {account['AccountNumber']}", end="\r")
		except ClientError as my_Error:
			if "AuthFailure" in str(my_Error):
				print(f"\nAuthorization Failure for account {account['AccountId']}")
			else:
				print(f"\nError: {my_Error}")
	if pFragments is None:
		found_roles = Roles
	else:
		found_roles = [x for x in Roles if find_in([x['RoleName']], pFragments, pExact)]
	return found_roles


def update_role_policy(fRole: dict, fPolicy: str) -> dict:
	"""
	Description: Updates the role policy
	@param fRole: Role to update
	@param fPolicy: Policy to attach to role
	@return: Dictionary of the response

	### Example
	response = client.update_assume_role_policy(
    PolicyDocument='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":["ec2.amazonaws.com"]},"Action":["sts:AssumeRole"]}]}',
    RoleName='S3AccessForEC2Instances',
	)
	"""
	iam_session = boto3.Session(aws_access_key_id=fRole['AccessKeyId'],
	                            aws_secret_access_key=fRole['SecretAccessKey'],
	                            aws_session_token=fRole['SessionToken'],
	                            region_name=fRole['Region'])
	iam_client = iam_session.client('iam')
	try:
		response = iam_client.update_assume_role_policy(
			RoleName=fRole['RoleName'],
			PolicyDocument=fPolicy
		)
		return {'Success': True, 'Response': response}
	except ClientError as my_Error:
		return {'Success': False, 'Response': my_Error}


def check_json(fPolicy_string:str):
	try:
		json.loads(fPolicy_string)
	except JSONDecodeError as e:
		logging.error(f"Error position: {e.pos}")
		logging.error(f"Error message: {e.msg}")
		logging.error(f"Error line: {e.lineno}")
		return False
	return True

###########################

if __name__ == '__main__':
	args = parse_args(sys.argv[1:])
	pProfiles = args.Profiles
	pRegionList = args.Regions
	# pRole = args.pRole
	pFragments = args.Fragments
	pAccounts = args.Accounts
	pSkipAccounts = args.SkipAccounts
	pSkipProfiles = args.SkipProfiles
	pForce = args.Force
	pExact = args.Exact
	pRootOnly = args.RootOnly
	pFilename = args.Filename
	pTiming = args.Time
	verbose = args.loglevel
	pPolicy = args.pPolicy
	# Setup logging levels
	logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(""message)s")
	logging.getLogger("boto3").setLevel(logging.CRITICAL)
	logging.getLogger("botocore").setLevel(logging.CRITICAL)
	logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
	logging.getLogger("urllib3").setLevel(logging.CRITICAL)


	ERASE_LINE = '\x1b[2K'
	time_to_sleep = 5
	begin_time = time()

	print()

	if pPolicy:
		with open(pPolicy, 'r') as pPolicy:
			policy_file = pPolicy.read()

		if not check_json(policy_file):
			print(f"Policy provided is not valid JSON, please check and try again")
			sys.exit(1)

	# Get credentials for all Child Accounts
	print(f"Checking accounts for roles containing this fragment {pFragments}")
	print(f"Will add provided policy to all roles found...") if pPolicy else ''
	print()
	AllCredentials = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)
	# Collect the stacksets, AccountList and RegionList involved
	all_found_roles = find_and_collect_roles_across_accounts(AllCredentials, pFragments)
	# Display the information we've found this far
	sorted_Results = sorted(all_found_roles, key=lambda d: (d['MgmtAcct'], d['AccountId'], d['RoleName']))
	display_dict = {'AccountId': {'DisplayOrder': 2, 'Heading': 'Account Number'},
	                'MgmtAcct' : {'DisplayOrder': 1, 'Heading': 'Parent Acct'},
	                'RoleName' : {'DisplayOrder': 3, 'Heading': 'Role Name'},
	                'Action'   : {'DisplayOrder': 4, 'Heading': 'Action Taken'}}

	display_results(sorted_Results, display_dict, "No Action", pFilename)

	# Modify stacks, if requested
	if pPolicy:
		for role in sorted_Results:
			update_role_policy(role, policy_file)

	print()
	AccountNum = list(set([x['AccountId'] for x in sorted_Results]))
	if pFragments is None:
		print(f"Found {len(sorted_Results)} roles across {AccountNum} accounts")
	else:
		print(f"Found {len(sorted_Results)} instances where role containing {pFragments} was found across {AccountNum} accounts")

	if pTiming:
		print(ERASE_LINE)
		print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
	print()
	print("Thanks for using this script...")
	print()
