#!/usr/local/bin/python3

import os, sys, pprint, boto3, json
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

parser = argparse.ArgumentParser(
	description="A script to ensure the 'AWSCloudFormationStackSetExecutionRole' is available within the child accounts.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	help="Specify a Root profile")
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const",
	dest="loglevel",
	const=logging.INFO,
    default=logging.CRITICAL)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.WARNING)
args = parser.parse_args()

pProfile=args.pProfile
verbose=args.loglevel
logging.basicConfig(level=args.loglevel)

ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)

##########################
ERASE_LINE = '\x1b[2K'

sts_session = boto3.Session(profile_name=pProfile)
sts_client = sts_session.client('sts')
AcctNum=sts_client.get_caller_identity()['Account']
Std_Trust_Policy={
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "StandardAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::"+AcctNum+":root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
AccountsToConfigure=[]

for account in ChildAccounts:
	# RoleName="AWSCloudFormationStackSetExecutionRole"
	# RoleName="OrganizationalFullAccess"
	# RoleName="OrganizationAccountAccessRole"
	# RoleName="Owner"
	RoleName="admin-crossAccount"
	role_arn = "arn:aws:iam::{}:role/{}".format(account['AccountId'],RoleName)
	logging.info("Role ARN: %s" % role_arn)
	try:
		AccountErrored=False
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="RegistrationScript")['Credentials']
		account_credentials["ParentAccountNumber"]=AcctNum
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(pProfile+": Authorization Failure to account {} using {} from account {}".format(account['AccountId'],RoleName,AcctNum))
			AccountErrored=True
			continue
		elif str(my_Error).find("AccessDenied") > 0:
			print(pProfile+": Authentication Denied to account {} using {} from account {}".format(account['AccountId'],RoleName,AcctNum))
			AccountErrored=True
			continue
		else:
			print(my_Error)
			AccountErrored=True
	AccountIsLZAcct=Inventory_Modules.find_if_LZ_Acct(account_credentials) if not AccountErrored else None
	if not AccountIsLZAcct and not AccountErrored:
		AccountsToConfigure.append({
		'AccountId':account['AccountId'],
		'AccountEmail':account['AccountEmail'],
		'AccountCredentials':account_credentials
	})
logging.info("There are %s accounts to configure",len(AccountsToConfigure))
for account in AccountsToConfigure:
	print(ERASE_LINE,Fore.RED+"Setting up Account with credentials for Landing Zone: ",account['AccountId'],"Email: ",account['AccountEmail']+Fore.RESET,end="\r")
	aws_session=boto3.Session(
		aws_access_key_id = account['AccountCredentials']['AccessKeyId'],
		aws_secret_access_key = account['AccountCredentials']['SecretAccessKey'],
		aws_session_token = account['AccountCredentials']['SessionToken']
	)
	iam_client=aws_session.client('iam')
	print()
	CreateRole=False
	DeleteRole=False
	try:
		# See if role already exists
		response = iam_client.get_role(
			RoleName='AWSCloudFormationStackSetExecutionRole'
		)
		print("LZ role already exists!!")
		CreateRole=False
	except ClientError as my_Error:
		if str(my_Error).find("EntityAlreadyExists") > 0:
			print("Role wasn't found in this account - so it needs to be created")
			CreateRole=True
		elif str(my_Error).find("AccessDenied") > 0:
			print("Access Denied for this account")
			CreateRole=True

	if CreateRole:
		try:
			# Create Role
			response = iam_client.create_role(
				RoleName='TestRole',
				AssumeRolePolicyDocument=json.dumps(Std_Trust_Policy),
				Description="Landing Zone Standard Role"
			)
			# Attach Admin User Policy
			response = iam_client.attach_role_policy(
				RoleName='TestRole',
				PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
			)
			# Echo info to the screen
			print('AccountEmail:',account['AccountEmail'])
			print('RoleName: TestRole')
			# Wait for user input that they're registered the account
			# DeleteRole=True
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(pProfile+": Authorization Failure for account {}".format(account['AccountId']))
			elif str(my_Error).find("NoSuchEntity") > 0:
				print("Role wasn't found in this account - ")
			else:
				print(my_Error)
	else:
		print("Role exists... Onto the next account... ")
	# input("Press Return to continue:")
	if DeleteRole:
		try:
		# Delete the temp user
			response = iam_client.delete_role(
				RoleName='TestRole'
			)
			print("TestRole has been deleted. On to the next account...")
		except ClientError as my_Error:
			if str(my_Error).find("DeleteConflict") > 0:
				print(my_Error)
