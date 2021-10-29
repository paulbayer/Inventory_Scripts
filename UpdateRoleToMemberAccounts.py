#!/usr/bin/env python3

import sys
import boto3
import Inventory_Modules
import argparse
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore, Back, Style
from botocore.exceptions import ClientError

import logging

init()

parser = CommonArguments()
parser.singleprofile()
parser.verbosity()
parser.my_parser.add_argument(
		"-a", "--account",
		dest="pAccount",
		default=None,
		metavar="Single account to check/ update",
		help="To specify a specific account to check/ update, use this parameter. Default is to update all accounts within an Org.")
group = parser.my_parser.add_mutually_exclusive_group(required=True)
group.add_argument(
		"+r", "--RoleToAdd",
		dest="pRoleNameToAdd",
		metavar="role to create",
		default=None,
		help="Rolename to be added to a number of accounts")
group.add_argument(
		"-c", "--rolecheck",
		dest="pRoleNameToCheck",
		metavar="role to check to see if it exists",
		default=None,
		help="Rolename to be checked for existence")
group.add_argument(
		"+R", "--RoleToRemove",
		dest="pRoleNameToRemove",
		metavar="role to remove",
		default=None,
		help="Rolename to be removed from a number of accounts")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pAccount = args.pAccount
pRoleNameToAdd = args.pRoleNameToAdd
pRoleNameToRemove = args.pRoleNameToRemove
pRoleNameToCheck = args.pRoleNameToCheck
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

aws_acct = aws_acct_access(pProfile)
if pAccount is None:
	ChildAccounts = aws_acct.ChildAccounts
else:
	ChildAccounts = [{'AccountId': pAccount}]
# [{'ParentProfile': pProfile,
# 	                  'AccountId'    : pAccount,
# 	                  'AccountEmail' : 'Not Provided',
# 	                  'AccountStatus': 'Unknown'
# 	                  }]
##########################
ERASE_LINE = '\x1b[2K'


##########################


def createrole(ocredentials, fRootAccount, frole):
	import simplejson as json
	import boto3
	from colorama import init, Fore
	init()
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountId'] holds the account number you're connecting to
	"""
	Trust_Policy = {"Version"  : "2012-10-17",
	                "Statement": [
		                {
			                "Effect"   : "Allow",
			                "Principal": {
				                "AWS": [
					                f"arn:aws:iam::{fRootAccount}:root"
					                # "arn:aws:sts::"+fRootAccount+":assumed-role/Admin/*"
					                ]
				                },
			                "Action"   : "sts:AssumeRole"
			                }
		                ]
	                }

	AdminPolicy = 'arn:aws:iam::aws:policy/AdministratorAccess'

	Trust_Policy_json = json.dumps(Trust_Policy)

	session_iam = boto3.Session(
			aws_access_key_id=ocredentials['AccessKeyId'],
			aws_secret_access_key=ocredentials['SecretAccessKey'],
			aws_session_token=ocredentials['SessionToken']
			)

	client_iam = session_iam.client('iam')
	try:
		response = client_iam.create_role(RoleName=frole, AssumeRolePolicyDocument=Trust_Policy_json)
		logging.info("Successfully created the blank role %s in account %s", frole, ocredentials['AccountId'])
	except client_iam.exceptions.LimitExceededException as my_Error:
		ErrorMessage = f"Limit Exceeded: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except client_iam.exceptions.InvalidInputException as my_Error:
		ErrorMessage = f"Invalid Input: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except client_iam.exceptions.EntityAlreadyExistsException as my_Error:
		ErrorMessage = f"Role already exists: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except client_iam.exceptions.MalformedPolicyDocumentException as my_Error:
		ErrorMessage = f"Malformed role policy: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except client_iam.exceptions.ConcurrentModificationException as my_Error:
		ErrorMessage = f"Concurrent operations: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except client_iam.exceptions.ServiceFailureException as my_Error:
		ErrorMessage = f"Service Failure: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}

	try:
		response1 = client_iam.attach_role_policy(RoleName=frole, PolicyArn=AdminPolicy)
		print(f"{ERASE_LINE}We've successfully added the role{Fore.GREEN} {frole} {Fore.RESET}to account"
		      f"{Fore.GREEN} {ocredentials['AccountId']} {Fore.RESET}with admin rights, "
		      f"trusting the Management Account{Fore.GREEN} {fRootAccount}.{Fore.RESET}")
	except client_iam.exceptions.NoSuchEntityException as my_Error:
		ErrorMessage = f"No such policy: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except client_iam.exceptions.LimitExceededException as my_Error:
		ErrorMessage = f"No such policy: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except client_iam.exceptions.InvalidInputException as my_Error:
		ErrorMessage = f"No such policy: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except client_iam.exceptions.UnmodifiableEntityException as my_Error:
		ErrorMessage = f"No such policy: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except client_iam.exceptions.PolicyNotAttachableException as my_Error:
		ErrorMessage = f"No such policy: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except client_iam.exceptions.ServiceFailureException as my_Error:
		ErrorMessage = f"No such policy: {my_Error}"
		logging.error(ErrorMessage)
		return_response = {'Success': False, 'ErrorMessage': ErrorMessage}
	except ClientError as my_Error:
		if my_Error.response['Error']['Code'] == 'EntityAlreadyExists':
			print(f"Role {frole} already exists in account {ocredentials['AccountId']}. Skipping.")
		print(my_Error)
		pass


def removerole(ocredentials, frole):
	import boto3

	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountId'] holds the account number you're connecting to
	"""
	session_iam = boto3.Session(
			aws_access_key_id=ocredentials['AccessKeyId'],
			aws_secret_access_key=ocredentials['SecretAccessKey'],
			aws_session_token=ocredentials['SessionToken']
			)

	client_iam = session_iam.client('iam')
	AdminPolicy = 'arn:aws:iam::aws:policy/AdministratorAccess'

	try:
		response1 = client_iam.detach_role_policy(
				RoleName=frole,
				PolicyArn=AdminPolicy
				)
		logging.info("Successfully removed the admin policy from role %s", frole)
		response = client_iam.delete_role(
				RoleName=frole
				)
		print(f"{ERASE_LINE}We've successfully removed the role{Fore.GREEN} {frole} {Fore.RESET}"
		      f"from account{Fore.GREEN} {ocredentials['AccountId']} {Fore.RESET}")
	except ClientError as my_Error:
		# if my_Error.response['Error']['Code'] == 'EntityAlreadyExists':
		# 	print("Role {} already exists in account {}. Skipping.".format(frole, pAccount))
		print(my_Error)
		pass


def roleexists(ocredentials, frole):
	import boto3

	session_iam = boto3.Session(
			aws_access_key_id=ocredentials['AccessKeyId'],
			aws_secret_access_key=ocredentials['SecretAccessKey'],
			aws_session_token=ocredentials['SessionToken']
			)

	client_iam = session_iam.client('iam')
	try:
		logging.info(f"Checking Account {ocredentials['AccountId']} for Role {frole}")
		response = client_iam.get_role(RoleName=frole)
		return (True)
	except ClientError as my_Error:
		if (my_Error.response['Error']['Code']) == 'NoSuchEntity':
			logging.warning("Role %s doesn't exist in account %s", frole, ocredentials['AccountId'])
	return (False)


##########################
print()
RootAccountNumber = aws_acct.acct_number
sts_client = aws_acct.session.client('sts')
UpdatedAccounts = 0
Results = []
for account in ChildAccounts:
	# ConnectionSuccess = False
	# rolenames = ['AWSCloudFormationStackSetExecutionRole', 'OrganizationalFullAccess', 'OrganizationAccountAccessRole',
	#              'AWSControlTowerExecution', 'Owner', 'admin-crossAccount', 'AdministratorAccess']
	'''
	The comment below exists just to show the structure of the ARN that we build via code.
	'''
	# role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(account['AccountId'])
	account_credentials = Inventory_Modules.get_child_access3(aws_acct, account['AccountId'])
	if not account_credentials['Success']:
		logging.error(f"Something failed in getting credentials for account {account['AccountId']}\n"
		              f"Error Message: {account_credentials['ErrorMessage']}")
		continue
	print(f"Checking account {account_credentials['AccountId']} using role {account_credentials['Role']}", end='\r')
	if account_credentials['Role'] == pRoleNameToRemove:
		logging.error(f"{Fore.RED}We gained access to this account using the role you specified to remove.\n"
		              f"Is this definitely what you want to do?{Fore.RESET}")
	# Checking to see if the role already exists
	if pRoleNameToCheck is not None:
		logging.info(f"Checking to see if role {pRoleNameToCheck} exists in account {account['AccountId']}")
		if roleexists(account_credentials, pRoleNameToCheck):
			Results.append({'AccountId': account['AccountId'], 'Role': pRoleNameToCheck, 'Result': 'Role Exists'})
			UpdatedAccounts += 1
		else:
			Results.append({'AccountId': account['AccountId'], 'Role': pRoleNameToCheck, 'Result': 'Nonexistent Role'})
	# If we're supposed to add the role and it already exists
	elif pRoleNameToAdd is not None and roleexists(account_credentials, pRoleNameToAdd):
		logging.warning(f"Role {pRoleNameToAdd} already exists")
		continue
	# If we're supposed to remove the role and the role exists AND it's not the role we used to access the account
	elif pRoleNameToRemove is not None and roleexists(account_credentials, pRoleNameToRemove) and not (account_credentials['Role'] == pRoleNameToAdd):
		logging.warning(f"Removing role {pRoleNameToRemove} from account {account['AccountId']}")
		removerole(account_credentials, pRoleNameToRemove)
		Results.append({'AccountId': account['AccountId'], 'Role': pRoleNameToRemove, 'Result': 'Role Removed'})
		UpdatedAccounts += 1
	# If we're supposed to add the role
	elif pRoleNameToAdd is not None:
		createrole(account_credentials, RootAccountNumber, pRoleNameToAdd)
		Results.append({'AccountId': account['AccountId'], 'Role': pRoleNameToRemove, 'Result': 'Role Created'})
		UpdatedAccounts += 1

print()
print()
if pAccount is not None:
	print(f"You asked me to check account {pAccount} under your organization")
else:
	print(f"We found {len(ChildAccounts)} accounts under your organization")
	print(f"Of these, we checked {len(Results)} accounts")
if verbose < 40:  # Warning, Info and Debug - skips ERROR
	AccountList = [item['AccountId'] for item in Results]
	logging.warning(f"We checked the following accounts: {AccountList}")

if pRoleNameToCheck is not None:
	print(f"We found {UpdatedAccounts} accounts that included the {pRoleNameToCheck} role")
elif pRoleNameToAdd is not None:
	print(f"We updated {UpdatedAccounts} accounts to include the {pRoleNameToAdd} role")
elif pRoleNameToRemove is not None:
	print(f"We updated {UpdatedAccounts} accounts to remove the {pRoleNameToRemove} role")

print()
print()
print("Thanks for using the tool.")
