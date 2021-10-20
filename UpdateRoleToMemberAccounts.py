#!/usr/bin/env python3

"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sys, boto3
import Inventory_Modules
import argparse
# from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError

import logging

# init()

parser = argparse.ArgumentParser(
	description="We\'re going to update the member accounts to include a specific role.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	required = True,
	default='default',
	metavar="profile to use",
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-a", "--account",
	dest="pAccount",
	default=None,
	metavar="Single account to check/ update",
	help="To specify a specific account to check/ update, use this parameter. Default is to update all accounts within an Org.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument(
	"-r", "--RoleToAdd", "+r", "+role",
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
	"-R", "--RoleToRemove",
	dest="pRoleNameToRemove",
	metavar="role to remove",
	default=None,
	help="Rolename to be removed from a number of accounts")
parser.add_argument(
	'-u', '--RoleFragmentToUse',
	metavar="Role Fragment to Use",
	help="Role to look for to use",
	dest="pAccessRole")
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	default=logging.CRITICAL, # args.loglevel = 50
	dest="loglevel",
	const=logging.ERROR) # args.loglevel = 40
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	default=logging.CRITICAL, # args.loglevel = 50
	dest="loglevel",
	const=logging.WARNING) # args.loglevel = 30
parser.add_argument(
	'-vvv',
	help="Print INFO statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-d', '--debug',
	help="Print debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
args = parser.parse_args()

pProfile=args.pProfile
pAccount=args.pAccount
pRoleNameToAdd=args.pRoleNameToAdd
pRoleNameToRemove=args.pRoleNameToRemove
pRoleNameToCheck=args.pRoleNameToCheck
pAccessRole=args.pAccessRole
verbose=args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")

if pAccount is None:
	ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
	if len(ChildAccounts) == 0:
		print()
		print("The profile {} does not represent an Org".format(pProfile))
		print("This script only works with org accounts. Sorry.")
		print()
		sys.exit(1)
elif not len(pAccount) == 12:
	print("The provided Account number must be 12 digits")
	sys.exit(2)
else:
	ChildAccounts=[{'ParentProfile': pProfile,
	               'AccountId':pAccount,
	               'AccountEmail': 'Not Provided',
	               'AccountStatus': 'Unknown'
	               }]
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
		- ['Account'] holds the account number you're connecting to
	"""
	Trust_Policy = {"Version": "2012-10-17",
	                "Statement": [
		                {
			                "Effect": "Allow",
			                "Principal": {
				                "AWS": [
					                "arn:aws:iam::"+fRootAccount+":root"
					                # "arn:aws:sts::"+fRootAccount+":assumed-role/Admin/*"
				                ]
			                },
			                "Action": "sts:AssumeRole"
		                }
	                ]}

	AdminPolicy='arn:aws:iam::aws:policy/AdministratorAccess'

	Trust_Policy_json = json.dumps(Trust_Policy)

	session_iam=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)

	client_iam = session_iam.client('iam')
	try:
		response = client_iam.create_role(
			RoleName=frole,
			AssumeRolePolicyDocument=Trust_Policy_json
		)
		logging.info("Successfully created the blank role %s in account %s", frole, ocredentials['Account'])
		response1 = client_iam.attach_role_policy(
			RoleName=frole,
			PolicyArn=AdminPolicy
		)
		print(ERASE_LINE+"We've successfully added the role"+Fore.GREEN+" {} ".format(frole)+Fore.RESET+"to account"+Fore.GREEN+" {} ".format(ocredentials['Account'])+Fore.RESET+"with admin rights, trusting the Management Account"+Fore.GREEN+" {}.".format(fRootAccount)+Fore.RESET)
	except ClientError as my_Error:
		if my_Error.response['Error']['Code'] == 'EntityAlreadyExists':
			print("Role {} already exists in account {}. Skipping.".format(frole, ocredentials['Account']))
		print(my_Error)
		pass

def removerole(ocredentials, frole):
	import boto3
	from colorama import init, Fore
	init()

	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['Account'] holds the account number you're connecting to
	"""
	session_iam=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)

	client_iam = session_iam.client('iam')
	AdminPolicy='arn:aws:iam::aws:policy/AdministratorAccess'

	try:
		response1 = client_iam.detach_role_policy(
			RoleName=frole,
			PolicyArn=AdminPolicy
		)
		logging.info("Successfully removed the admin policy from role %s", frole)
		response = client_iam.delete_role(
			RoleName=frole
		)
		print(ERASE_LINE+"We've successfully removed the role"+Fore.GREEN+" {} ".format(frole)+Fore.RESET+"from account"+Fore.GREEN+" {} ".format(ocredentials['Account'])+Fore.RESET)
	except ClientError as my_Error:
		# if my_Error.response['Error']['Code'] == 'EntityAlreadyExists':
		# 	print("Role {} already exists in account {}. Skipping.".format(frole, pAccount))
		print(my_Error)
		pass

def roleexists(ocredentials, frole):
	import boto3

	session_iam=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)

	client_iam = session_iam.client('iam')
	try:
		logging.info("Checking Account %s for Role %s",ocredentials['Account'], frole)
		response = client_iam.get_role(
			RoleName=frole
		)
		return(True)
	except ClientError as my_Error:
		if (my_Error.response['Error']['Code']) == 'NoSuchEntity':
			logging.warning("Role %s doesn't exist in account %s", frole,ocredentials['Account'])
	return(False)


##########################
print()
RootAccountNumber = Inventory_Modules.find_account_number(pProfile)
aws_session = boto3.Session(profile_name=pProfile)
sts_client = aws_session.client('sts')
UpdatedAccounts=0
Results=[]
for account in ChildAccounts:
	ConnectionSuccess = False
	Check_account_credentials = sts_client.assume_role(
			RoleArn=f"arn:aws:iam::{account['AccountId']}:role/account_roles",
			RoleSessionName="RegistrationScript")['Credentials']
	Check_account_credentials['Account'] = account['AccountId']
	iam_session = boto3.Session(aws_access_key_id=Check_account_credentials['AccessKeyId'],
	                            aws_secret_access_key=Check_account_credentials['SecretAccessKey'],
	                            aws_session_token=Check_account_credentials['SessionToken'])
	iam_client = iam_session.client('iam')
	AvailableRoles = iam_client.list_roles()['Roles']
	for role in AvailableRoles:
		if role['RoleName'].find(pAccessRole) >= 0:
			RoleToUse = role
	rolenames = [RoleToUse]
	# rolenames=['AWSCloudFormationStackSetExecutionRole', 'OrganizationalFullAccess', 'OrganizationAccountAccessRole', 'AWSControlTowerExecution', 'Owner', 'admin-crossAccount','AdministratorAccess']
	'''
	The comment below exists just to show the structure of the ARN that we build via code.
	'''
	# role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(account['AccountId'])
	for rolename in rolenames:
		if ConnectionSuccess:   # Indicating that the previous run of this loop was successful and we can skip trying
			break
		print(ERASE_LINE,"Trying to access account {} using role {}".format(account['AccountId'], rolename),end="\r")
		role_arn = "arn:aws:iam::{}:role/{}".format(account['AccountId'], rolename)
		logging.info("Role ARN: %s" % role_arn)
		try:
			account_credentials = sts_client.assume_role(
				RoleArn=role_arn,
				RoleSessionName="RegistrationScript")['Credentials']
			account_credentials['Account'] = account['AccountId']
			logging.warning("Successfully accessed account %s using rolename %s" % (account['AccountId'], rolename))
			ConnectionSuccess = True
			if not pRoleNameToCheck==None:
				logging.warning("Checking to see if role %s exists in account %s", pRoleNameToCheck, account['AccountId'])
				if roleexists(account_credentials, pRoleNameToCheck):
					Results.append({
						'AccountId': account['AccountId'],
						'Role': pRoleNameToCheck,
						'Result': 'Role Exists'
					})
					UpdatedAccounts += 1
				else:
					Results.append({
						'AccountId': account['AccountId'],
						'Role': pRoleNameToCheck,
						'Result': 'Nonexistent Role'
					})
			elif pRoleNameToRemove==None and roleexists(account_credentials, pRoleNameToAdd):
				logging.warning("Role %s already exists", pRoleNameToAdd)
				break
			elif not (pRoleNameToRemove==None) and roleexists(account_credentials, pRoleNameToRemove):
				logging.warning("Removing role %s from account %s", pRoleNameToRemove, account['AccountId'])
				removerole(account_credentials, pRoleNameToRemove)
				Results.append({
					'AccountId': account['AccountId'],
					'Role': pRoleNameToRemove,
					'Result': 'Role Removed'
				})
				UpdatedAccounts += 1
			elif not (pRoleNameToAdd == None) and not (rolename == pRoleNameToAdd):
				createrole(account_credentials, RootAccountNumber, pRoleNameToAdd)
				Results.append({
					'AccountId': account['AccountId'],
					'Role': pRoleNameToRemove,
					'Result': 'Role Created'
				})
				UpdatedAccounts += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.warning("%s: Authorization Failure to account %s using %s" % (pProfile, account['AccountId'], role_arn))
				ConnectionSuccess = False
				continue	# Try the next rolename
			elif str(my_Error).find("AccessDenied") > 0:
				logging.warning("%s: Authentication Denied to account %s using %s" % (pProfile, account['AccountId'], role_arn))
				ConnectionSuccess = False
				continue	# Try the next rolename


print()
print()
print("Thanks for using the tool.")
if not pAccount is None:
	print("You asked me to check account {} under your organization".format(ChildAccounts[0]['AccountId']))
else:
	print("We found {} accounts under your organization".format(len(ChildAccounts)))
	print("Of these, we checked {} accounts".format(len(Results)))
if verbose < 40:    # Warning, Info and Debug - skips ERROR
	AccountList=[]
	for i in Results:
		AccountList.append(i['AccountId'])
	logging.warning("We checked the following accounts: %s", str(AccountList))

if not (pRoleNameToCheck == None):
	print("We found {} accounts that included the {} role".format(UpdatedAccounts, pRoleNameToCheck))
elif not (pRoleNameToAdd == None):
	print("We updated {} accounts to include the {} role".format(UpdatedAccounts, pRoleNameToAdd))
elif not (pRoleNameToRemove == None):
	print("We updated {} accounts to remove the {} role".format(UpdatedAccounts, pRoleNameToRemove))
