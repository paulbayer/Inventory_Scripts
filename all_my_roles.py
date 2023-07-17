#!/usr/bin/env python3

from Inventory_Modules import display_results, get_all_credentials, find_in
import boto3
from ArgumentsClass import CommonArguments
from time import sleep, time
from colorama import init, Fore
from botocore.exceptions import ClientError
import logging

init()
__version__ = "2023.07.17"

parser = CommonArguments()
parser.my_parser.description = ("We're going to find all roles within any of the accounts we have access to, given the profile(s) provided.")
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
parser.deletion()
parser.rootOnly()
parser.verbosity()
parser.timing()
parser.save_to_file()
parser.version(__version__)
parser.my_parser.add_argument(
	"--role",
	dest="pRole",
	metavar="specific role to find",
	default=None,
	help="Please specify the role you're searching for")
parser.my_parser.add_argument(
	"+d", "--delete",
	dest="pDelete",
	action="store_const",
	const=True,
	default=False,
	help="Whether you'd like to delete that specified role.")
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pRole = args.pRole
pAccounts = args.Accounts
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pDelete = args.pDelete
pForce = args.Force
pRootOnly = args.RootOnly
pFilename = args.Filename
pTiming = args.Time
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(""message)s")

##########################
ERASE_LINE = '\x1b[2K'
if pTiming:
	begin_time = time()


##########################


def my_delete_role(fRoleList):
	iam_session = boto3.Session(
		aws_access_key_id=fRoleList['AccessKeyId'],
		aws_secret_access_key=fRoleList['SecretAccessKey'],
		aws_session_token=fRoleList['SessionToken'],
		region_name=fRoleList['Region']
	)
	iam_client = iam_session.client('iam')
	try:
		attached_role_policies = iam_client.list_attached_role_policies(RoleName=fRoleList['RoleName'])['AttachedPolicies']
		for _ in range(len(attached_role_policies)):
			response = iam_client.detach_role_policy(
				RoleName=fRoleList['RoleName'],
				PolicyArn=attached_role_policies[_]['PolicyArn']
			)
		inline_role_policies = iam_client.list_role_policies(RoleName=fRoleList['RoleName'])['PolicyNames']
		for _ in range(len(inline_role_policies)):
			response = iam_client.delete_role_policy(
				RoleName=fRoleList['RoleName'],
				PolicyName=inline_role_policies[_]['PolicyName']
			)
		response = iam_client.delete_role(
			RoleName=fRoleList['RoleName']
		)
		return (True)
	except ClientError as my_Error:
		logging.error(f"Error: {my_Error}")
		return (False)


##########################


AllCredentials = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)

print()
if pRole is not None:
	print(f"Looking for a specific role called '{pRole}' across {len(AllCredentials)} accounts")
	print()
else:
	print(f"Listing out all roles across {len(AllCredentials)} accounts")
	print()

Roles = []
for account in AllCredentials:
	if account['Success']:
		iam_session = boto3.Session(aws_access_key_id=account['AccessKeyId'],
		                            aws_secret_access_key=account['SecretAccessKey'],
		                            aws_session_token=account['SessionToken'],
		                            region_name=account['Region'])
		iam_client = iam_session.client('iam')
	else:
		continue
	try:
		# TODO: Paging needed here
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
		RoleNum = len(response['Roles'])
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
				RoleNum += len(response['Roles'])
		print(f" - Found {RoleNum} roles in account {account['AccountNumber']}", end="\r")
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"Authorization Failure for account {account['AccountId']}")
		else:
			print(f"Error: {my_Error}")

time_to_sleep = 5
confirm = False

DisplayList = [x for x in Roles if find_in([x['RoleName']], [pRole])]
sorted_Results = sorted(DisplayList, key=lambda d: (d['MgmtAcct'], d['AccountId'], d['RoleName']))

if pDelete:
	if pRole is None:
		print(f"You asked to delete roles, but didn't give a specific role to delete, so we're not going to delete anything.")
	elif len(sorted_Results) > 0 and not pForce:
		print(f"Your specified role fragment matched at least 1 role.\n"
		      f"Please confirm you want to really delete all {len(sorted_Results)} roles found")
		confirm = (input(f"Really delete {len(sorted_Results)} across {len(AllCredentials)} accounts. Are you still sure? (y/n): ").lower() == 'y')
	elif pForce and len(sorted_Results) > 0:
		print(f"You specified a fragment that matched multiple roles.\n"
		      f"And you specified the 'FORCE' parameter - so we're not asking again, BUT we'll wait {time_to_sleep} seconds to give you the option to Ctrl-C here...")
		sleep(time_to_sleep)

if (pDelete and confirm) or (pDelete and pForce):
	for i in range(len(sorted_Results)):
		logging.info(f"Deleting role {sorted_Results[i]['RoleName']} from account {sorted_Results[i]['AccountId']}")
		result = my_delete_role(sorted_Results[i])
		if result:
			sorted_Results[i].update({'Action': 'deleted'})
		else:
			sorted_Results[i].update({'Action': 'delete failed'})

display_dict = {'AccountId': {'DisplayOrder': 2, 'Heading': 'Account Number'},
                'MgmtAcct' : {'DisplayOrder': 1, 'Heading': 'Parent Acct'},
                'RoleName' : {'DisplayOrder': 3, 'Heading': 'Role Name'},
                'Action'   : {'DisplayOrder': 4, 'Heading': 'Action Taken'}}

display_results(sorted_Results, display_dict, "No Action", pFilename)

print()
if pRole is None:
	print(f"Found {len(DisplayList)} roles across {len(AllCredentials)} accounts")
else:
	print(f"Found {len(DisplayList)} instances where role containing '{pRole}' was found across {len(AllCredentials)} accounts")

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
print()
print("Thanks for using this script...")
print()
