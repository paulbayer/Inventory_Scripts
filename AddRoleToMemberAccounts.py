#!/usr/local/bin/python3

import os, sys, pprint, boto3
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find the necessary information to register this account within Isengard.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	default='default',
	metavar="profile to use",
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-r", "--role",
	dest="pRoleNameToAdd",
	default="",
	metavar="role to create",
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	'-f', '--force',
	const=True,
	default=False,
	dest="pForcedReg",
	action="store_const",
	help="Force a registration with Isengard")
parser.add_argument(
	'-vvv',
	help="Print debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-d', '--debug',
	help="Print lots of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-v', '--verbose',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR) # args.loglevel = 40
parser.add_argument(
	'-vv',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING) # args.loglevel = 30
args = parser.parse_args()

pProfile=args.pProfile
pRoleNameToAdd=args.pRoleNameToAdd
pForcedReg=args.pForcedReg
verbose=args.loglevel
logging.basicConfig(level=args.loglevel)

ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
if len(ChildAccounts) == 0:
	print()
	print("The profile {} seems to not represent an Org".format(pProfile))
	print("This script only works with org accounts. Sorry.")
	print()
	sys.exit(1)
##########################
ERASE_LINE = '\x1b[2K'
##########################


def createrole(ocredentials, pRootAccount, pAccount, prole):
	import simplejson as json
	from pprint import pprint
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
	"""
	Trust_Policy = {"Version": "2012-10-17",
	                "Statement": [
		                {
			                "Effect": "Allow",
			                "Principal": {
				                "AWS": [
					                "arn:aws:iam::"+pRootAccount+":root"
					                # "arn:aws:sts::"+pRootAccount+":assumed-role/Admin/*"
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
			RoleName=prole,
			AssumeRolePolicyDocument=Trust_Policy_json
		)
		response1 = client_iam.attach_role_policy(
			RoleName=prole,
			PolicyArn=AdminPolicy
		)
		print("We've successfully added the role {} to account {} with admin rights, trusting the Management Account {}.".format(prole, pAccount, pRootAccount))
	except ClientError as my_Error:
		if my_Error.response['Error']['Code'] == 'EntityAlreadyExists':
			print("Role {} already exists in account {}. Skipping.".format(prole, pAccount))
		print(my_Error)
		pass


def roleexists(ocredentials, prole):

	session_iam=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)

	client_iam = session_iam.client('iam')
	try:
		response = client_iam.get_role(
			RoleName=prole
		)
		return(True)
	except ClientError as my_Error:
		if (my_Error.response['Error']['Code']) == 'NoSuchEntity':
			print("Role {} doesn't exist in account {}".format(prole,ocredentials['Account']))
	return(False)


print()
RootAccountNumber = Inventory_Modules.find_account_number(pProfile)
sts_session = boto3.Session(profile_name=pProfile)
sts_client = sts_session.client('sts')
UpdatedAccounts=0
for account in ChildAccounts:
	ConnectionSuccess = False
	rolenames=['AWSCloudFormationStackSetExecutionRole', 'OrganizationalFullAccess', 'OrganizationAccountAccessRole', 'AWSControlTowerExecution', 'Owner', 'admin-crossAccount','AdministratorAccess']
	# role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(account['AccountId'])
	# role_arn = "arn:aws:iam::{}:role/OrganizationalFullAccess".format(account['AccountId'])
	# role_arn = "arn:aws:iam::{}:role/AWSControlTowerExecution".format(account['AccountId'])
	# role_arn = "arn:aws:iam::{}:role/OrganizationAccountAccessRole".format(account['AccountId'])
	# role_arn = "arn:aws:iam::{}:role/Owner".format(account['AccountId'])
	# role_arn = "arn:aws:iam::{}:role/admin-crossAccount".format(account['AccountId'])
	for rolename in rolenames:
		if ConnectionSuccess:
			break
		# print(ERASE_LINE, "Trying to access account {} using role {}".format(account['AccountId'], rolename), end="\r")
		print("Trying to access account {} using role {}".format(account['AccountId'], rolename))
		role_arn = "arn:aws:iam::{}:role/{}".format(account['AccountId'], rolename)
		logging.info("Role ARN: %s" % role_arn)
		try:
			account_credentials = sts_client.assume_role(
				RoleArn=role_arn,
				RoleSessionName="RegistrationScript")['Credentials']
			account_credentials['Account'] = account['AccountId']
			logging.warning("Accessed Account %s using rolename %s" % (account['AccountId'], rolename))
			ConnectionSuccess = True
			if roleexists(account_credentials, pRoleNameToAdd):
				break
			if not (rolename == pRoleNameToAdd) and not (pRoleNameToAdd == ""):
				createrole(account_credentials, RootAccountNumber, account['AccountId'], pRoleNameToAdd)
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
print("Thanks for using the tool.")
print("We found {} accounts under your organization".format(len(ChildAccounts)))
print("We updated {} accounts to include the {} role".format(UpdatedAccounts, pRoleNameToAdd))