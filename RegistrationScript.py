#!/usr/local/bin/python3

import os, sys, pprint, boto3
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
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

print()
fmt='%-15s %-25s %-15s %-24s'
print(fmt % ("Account","Email","AccessKey","Secret Access Key"))
print(fmt % ("-------","------","------","-------------"))

sts_session = boto3.Session(profile_name=pProfile)
sts_client = sts_session.client('sts')
AccountsToRegister=[]
for account in ChildAccounts:
	role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(account['AccountId'])
	logging.info("Role ARN: %s" % role_arn)
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="RegistrationScript")['Credentials']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(pProfile+": Authorization Failure for account {}".format(account['AccountId']))
	AccountIsRegistered=Inventory_Modules.find_if_Isengard_registered(account_credentials)
	if not AccountIsRegistered:
		AccountsToRegister.append({
		'AccountId':account['AccountId'],
		'AccountEmail':account['AccountEmail'],
		'AccountCredentials':account_credentials
	})
logging.info("There are %s accounts to register",len(AccountsToRegister))
for account in AccountsToRegister:
	print(ERASE_LINE,Fore.RED+"Setting up Account with credentials for Isengard registration: ",account['AccountId'],"Email: ",account['AccountEmail']+Fore.RESET,end="\r")
	aws_session=boto3.Session(
		aws_access_key_id = account['AccountCredentials']['AccessKeyId'],
		aws_secret_access_key = account['AccountCredentials']['SecretAccessKey'],
		aws_session_token = account['AccountCredentials']['SessionToken']
	)
	iam_client=aws_session.client('iam')
	print()
	CreateUser=False
	DeleteUser=False
	try:
		response = iam_client.get_user(
			UserName='Alice'
		)
		print("Alice already exists!!")
		AccessKeyMetadata=iam_client.list_access_keys(
    		UserName='Alice'
		)
		DeleteUser=True
	except ClientError as my_Error:
		if str(my_Error).find("NoSuchEntity") > 0:
			print("User wasn't found in this account - so they need to be created")
			CreateUser=True
	if CreateUser:
		try:
			# Seeif user already exists
			# Create User
			response = iam_client.create_user(
				UserName='Alice'
			)
			# Create Access Key
			response = iam_client.create_access_key(
				UserName='Alice'
			)['AccessKey']
			AccessKeyId=response['AccessKeyId']
			SecretAccessKey=response['SecretAccessKey']
			# Attach Admin User Policy
			response = iam_client.attach_user_policy(
				UserName='Alice',
				PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
			)
			# Echo info to the screen
			print('AccountEmail:',account['AccountEmail'])
			print('AccountAccessKey',AccessKeyId)
			print('SecretKey:',SecretAccessKey)
			# Wait for user input that they're registered the account
			DeleteUser=True
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(pProfile+": Authorization Failure for account {}".format(account['AccountId']))
			elif str(my_Error).find("NoSuchEntity") > 0:
				print("User wasn't found in this account - ")
			else:
				print(my_Error)
	input("Press Return after you've registered the account in Isengard:")
	if DeleteUser:
		try:
		# Detach admin policy from the user
			response = iam_client.detach_user_policy(
				UserName='Alice',
				PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
			)
		# Delete the access key
			if not CreateUser:	#The scenario where the user already existed
				print("AccessKeyMetadata")
				pprint.pprint(AccessKeyMetadata)
				for y in range(len(AccessKeyMetadata['AccessKeyMetadata'])):
					response = iam_client.delete_access_key(
						UserName='Alice',
						AccessKeyId=AccessKeyMetadata['AccessKeyMetadata'][y]['AccessKeyId']
					)
			else:	# The scenario where the user was created by this script
				response = iam_client.delete_access_key(
					UserName='Alice',
					AccessKeyId=AccessKeyId
				)
		# Delete the temp user
			response = iam_client.delete_user(
				UserName='Alice'
			)
			print("Alice has been deleted. On to the next account...")
		except ClientError as my_Error:
			if str(my_Error).find("DeleteConflict") > 0:
				response = iam_client.detach_user_policy(
					UserName='Alice',
					PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
				)
				response = iam_client.delete_access_key(
					UserName='Alice',
					AccessKeyId=AccessKeyId
				)
			print(my_Error)
# print(ERASE_LINE)
# print(Fore.RED+"Found",NumStacksFound,"Stacksets across",len(ChildAccounts),"accounts across",len(RegionList),"regions"+Fore.RESET)
# print()
