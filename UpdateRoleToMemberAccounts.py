#!/usr/bin/env python3


import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
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
parser.my_parser.add_argument(
		"--RoleToUse",
		dest="pRoleToUse",
		default=None,
		metavar="Role name",
		help="Role that should be used to access child accounts")
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
pRoleToUse = args.pRoleToUse
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
	return_response = {'Success': False, 'ErrorMessage': ''}
	session_iam = boto3.Session(
			aws_access_key_id=ocredentials['AccessKeyId'],
			aws_secret_access_key=ocredentials['SecretAccessKey'],
			aws_session_token=ocredentials['SessionToken']
			)

	client_iam = session_iam.client('iam')
	AdminPolicy = 'arn:aws:iam::aws:policy/AdministratorAccess'

	try:
		# We need to list the policies attached (whether inline or managed)
		# TODO: Both of these calls below should allow for pagination
		attached_managed_policies = client_iam.list_attached_role_policies(RoleName=frole)
		"""
		{
	    'AttachedPolicies': [
	        {
	            'PolicyName': 'string',
	            'PolicyArn': 'string'
	        },
	    ],
	    'IsTruncated': True|False,
	    'Marker': 'string'
		}
		"""

		attached_inline_policies = client_iam.list_role_policies(RoleName=frole)
		"""
		{
	    'PolicyNames': [
	        'string',
	    ],
	    'IsTruncated': True|False,
	    'Marker': 'string'
		}
		"""

		# Then we need to detach/ delete the policy we find
		for managed_policy in attached_managed_policies['AttachedPolicies']:
			try:
				response1 = client_iam.detach_role_policy(
					RoleName=frole,
					PolicyArn=managed_policy['PolicyArn']
					)
				logging.info(f"Successfully removed the managed policy {managed_policy['PolicyName']} from role {frole}")
				return_response['Success'] = True
			except (client_iam.exceptions.NoSuchEntityException,
			        client_iam.exceptions.InvalidInputException,
			        client_iam.exceptions.ServiceFailureException) as my_Error:
				logging.error(f"Error Message: {my_Error}")
				return_response['ErrorMessage'] = str(my_Error)
				return_response['Success'] = False
			if return_response['Success']:
				continue
			else:
				return(return_response)

		for inline_policy in attached_inline_policies['PolicyNames']:
			try:
				inline_role_deletion = client_iam.delete_role_policy(
					RoleName=frole,
					PolicyName=inline_policy
					)
				logging.info(f"Successfully removed the inline policy {inline_policy} from role {frole}")
				return_response['Success'] = True
			except (client_iam.exceptions.NoSuchEntityException,
			        client_iam.exceptions.LimitExceededException,
			        client_iam.exceptions.UnmodifiableEntityException,
			        client_iam.exceptions.ServiceFailureException) as my_Error:
				logging.error(f"Error Message: {my_Error}")
				return_response['ErrorMessage'] = str(my_Error)
				return_response['Success'] = False
			if return_response['Success']:
				continue
			else:
				return(return_response)

		# Only then we can we delete the role
		try:
			response = client_iam.delete_role(RoleName=frole)
			logging.info(f"Successfully removed the role {frole}")
			return_response['Success'] = True
		except (client_iam.exceptions.NoSuchEntityException,
		        client_iam.exceptions.DeleteConflictException,
		        client_iam.exceptions.LimitExceededException,
		        client_iam.exceptions.UnmodifiableEntityException,
		        client_iam.exceptions.ConcurrentModificationException,
		        client_iam.exceptions.ServiceFailureException) as my_Error:
			logging.error(f"Error Message: {my_Error}")
			return_response['ErrorMessage'] = str(my_Error)
			return_response['Success'] = False
			if return_response['Success']:
				pass
			else:
				return(return_response)

		print(f"{ERASE_LINE}We've successfully removed the role{Fore.GREEN} {frole} {Fore.RESET}"
		      f"from account{Fore.GREEN} {ocredentials['AccountId']} {Fore.RESET}")
	except ClientError as my_Error:
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
		logging.info(f"{ERASE_LINE}Checking Account {ocredentials['AccountId']} for Role {frole}")
		response = client_iam.get_role(RoleName=frole)
		return (True)
	except ClientError as my_Error:
		if (my_Error.response['Error']['Code']) == 'NoSuchEntity':
			logging.warning("Role %s doesn't exist in account %s", frole, ocredentials['AccountId'])
	return (False)


##########################
print()
RootAccountNumber = aws_acct.MgmtAccount
sts_client = aws_acct.session.client('sts')
UpdatedAccounts = 0
Results = []
# if the user supplied a role to use, this parameter will cause the Inventory_Modules function to use it.
# If the parameter wasn't supplied, the default value is None, where it will be translated into a number of commonly used role names inside the function
if pRoleToUse is not None:
	RoleList = [pRoleToUse]
for account in ChildAccounts:
	account_credentials = Inventory_Modules.get_child_access3(aws_acct, account['AccountId'], fRoleList=[pRoleToUse])
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
	print(f"You asked to check account {pAccount} under your organization")
else:
	print(f"We found {len(ChildAccounts)} accounts under your organization")
	print(f"Of these, we checked {len(Results)} accounts")

AccountList = [item['AccountId'] for item in Results]
print(f"{Fore.GREEN}We checked the following accounts: {AccountList}{Fore.RESET}")
MissingAccounts = [item['AccountId'] for item in ChildAccounts if item['AccountId'] not in AccountList]
if len(MissingAccounts) > 0:
	print(f"{Fore.RED}We failed to check the following accounts: {MissingAccounts}{Fore.RESET}")

if pRoleNameToCheck is not None:
	print(f"We found {UpdatedAccounts} accounts that included the {pRoleNameToCheck} role")
	if verbose < 41:
		MissingAccounts = [item['AccountId'] for item in Results if not (item['Result'] == 'Role Exists')]
		if len(MissingAccounts) > 0:
			print(f"{Fore.RED}We didn't find {pRoleNameToCheck} in the following accounts: {MissingAccounts}{Fore.RESET}")
elif pRoleNameToAdd is not None:
	print(f"We updated {UpdatedAccounts} accounts to add the {pRoleNameToAdd} role")
elif pRoleNameToRemove is not None:
	print(f"We updated {UpdatedAccounts} accounts to remove the {pRoleNameToRemove} role")


print()
print("Thanks for using the tool.")
print()
