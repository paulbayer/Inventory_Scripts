#!/usr/bin/env python3

import Inventory_Modules
import boto3
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init
from botocore.exceptions import ClientError

import logging

init()

parser = CommonArguments()
parser.my_parser.description = ("We're going to find all roles within any of the accounts we have access to, given the profile provided.")
parser.verbosity()
parser.singleprofile()
parser.extendedargs()   # This adds the "DryRun" and "Force" objects
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

# for k, v in args.__dict__.items():
# 	# exec(f"{'p'+k} = {v}")      # Assigns each item within the args namespace to a separate variable
# 	logging.info("Arguments provided")
# 	logging.info(f"{k}: {v}")

pProfile = args.Profile
pRole = args.pRole
pDelete = args.pDelete
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(""message)s")

##########################
ERASE_LINE = '\x1b[2K'
##########################


def my_delete_role(fRoleList):
	iam_session = boto3.Session(
		aws_access_key_id=fRoleList['aws_access_key_id'],
		aws_secret_access_key=fRoleList['aws_secret_access_key'],
		aws_session_token=fRoleList['aws_session_token'],
		region_name='us-east-1'
		)
	iam_client = iam_session.client('iam')
	try:
		attached_role_policies = iam_client.list_attached_role_policies(
			RoleName=fRoleList['RoleName']
			)['AttachedPolicies']
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
		response = iam_client.my_delete_role(
			RoleName=fRoleList['RoleName']
			)
		return (True)
	except ClientError as my_Error:
		print(my_Error)
		return (False)
##########################


aws_acct = aws_acct_access(pProfile)
ChildAccounts = aws_acct.ChildAccounts
# ChildAccounts = Inventory_Modules.find_child_accounts2(pProfile)

print()
if pRole is not None:
	print(f"Looking for a specific role called {pRole}")
	print()
fmt = '%-15s %-42s'
print(fmt % ("Account Number", "Role Name"))
print(fmt % ("--------------", "---------"))
Roles = []
SpecifiedRoleNum = 0
DeletedRoles = 0
for account in ChildAccounts:
	try:
		RoleNum = 0
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, account['AccountId'])
		if "AccessError" in account_credentials.keys():
			logging.error(f"Access to member account {account['AccountId']} failed...")
			continue
		elif account_credentials['Role'] == 'Use Profile':
			logging.error(f"Access to the Root Account {account['AccountId']}")
			logging.info(f"Using Root profile provided")
			iam_session = aws_acct.session
		else:
			logging.info(f"Using child account's creds")
			iam_session = boto3.Session(
				aws_access_key_id=account_credentials['AccessKeyId'],
				aws_secret_access_key=account_credentials['SecretAccessKey'],
				aws_session_token=account_credentials['SessionToken'],
				region_name='us-east-1')
		account_credentials['AccountNumber'] = account['AccountId']
		logging.info(f"Connecting to {account['AccountId']} with {account_credentials['Role']} role")
		print(ERASE_LINE, f"Checking Account {account_credentials['AccountNumber']}", end="")
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{pProfile}: Authorization Failure for account {account['AccountId']}")
		continue
	iam_client = iam_session.client('iam')
	try:
		response = iam_client.list_roles()
		for i in range(len(response['Roles'])):
			Roles.append({
				'aws_access_key_id': account_credentials['AccessKeyId'],
				'aws_secret_access_key': account_credentials['SecretAccessKey'],
				'aws_session_token': account_credentials['SessionToken'],
				'AccountId': account_credentials['AccountNumber'],
				'RoleName': response['Roles'][i]['RoleName']
				})
		RoleNum = len(response['Roles'])
		while response['IsTruncated']:
			response = iam_client.list_roles(Marker=response['Marker'])
			for i in range(len(response['Roles'])):
				Roles.append({
					'AccountId': account_credentials['AccountNumber'],
					'RoleName': response['Roles'][i]['RoleName']
					})
				RoleNum += len(response['Roles'])
		print(f" - Found {RoleNum} roles", end="\r")
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{pProfile}: Authorization Failure for account {account['AccountId']}")
		else:
			print(f"Error: {my_Error}")

RoleNum = 0
if pRole is None:
	for i in range(len(Roles)):
		print(fmt % (Roles[i]['AccountId'], Roles[i]['RoleName']))
		RoleNum += 1
elif pRole is not None:
	if pDelete:
		DeletedRoles = 0
	for i in range(len(Roles)):
		RoleNum += 1
		logging.info(f"In account {Roles[i]['AccountId']}: Found Role {Roles[i]['RoleName']} : Looking for role {pRole}")
		if Roles[i]['RoleName'].find(pRole) >= 0:
			print(fmt % (Roles[i]['AccountId'], Roles[i]['RoleName']), end="")
			SpecifiedRoleNum += 1
			if pDelete:
				my_delete_role(Roles[i])
				print(f" - deleted", end="")
				DeletedRoles += 1
			print()

print()
if pRole is None:
	print(f"Found {RoleNum} roles across {len(ChildAccounts)} accounts")
else:
	print(f"Found {SpecifiedRoleNum} instances where role containing '{pRole}' was found across {len(ChildAccounts)} accounts")
	if pDelete:
		print(f"     And we deleted it {DeletedRoles} times")
print()
print("Thanks for using this script...")
print()
