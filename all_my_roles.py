#!/usr/local/bin/python3

import os, sys, pprint
import Inventory_Modules, boto3
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from urllib3.exceptions import NewConnectionError

import logging

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	help="You need to specify a profile that represents the ROOT account.")
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR, # args.loglevel = 40
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING, # args.loglevel = 30
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-d',
	help="Print debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-dd', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 10
	default=logging.CRITICAL) # args.loglevel = 50
args = parser.parse_args()

pProfile=args.pProfile
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'

ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)

print()
fmt='%-15s %-42s'
print(fmt % ("Account Number","Role Name"))
print(fmt % ("--------------","---------"))
RoleNum=0
for account in ChildAccounts:
	try:
		account_credentials,role_arn=Inventory_Modules.get_child_access2(pProfile, account['AccountId'])
		logging.info("Connecting to %s with %s role",account['AccountId'],role_arn)
		logging.info("Role ARN: %s" % role_arn)
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(profile+": Authorization Failure for account {}".format(account['AccountId']))
	iam_session=boto3.Session(
		aws_access_key_id=account_credentials['AccessKeyId'],
		aws_secret_access_key=account_credentials['SecretAccessKey'],
		aws_session_token=account_credentials['SessionToken'],
		region_name='us-east-1')
	iam_client=iam_session.client('iam')
	try:
		Roles=[]
		response=iam_client.list_roles()
		Roles=response['Roles']
		while response['IsTruncated']==True:
			response=iam_client.list_roles(Marker=response['Marker'])
			Roles.append(response['Roles'])
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(pProfile+": Authorization Failure for account {}".format(account['AccountId']))
	print()
	for i in range(len(Roles)):
		print(fmt % (account['AccountId'],Roles[i]['RoleName']))
		RoleNum+=1


print("Found {} roles across {} accounts".format(RoleNum,len(ChildAccounts)))
print()
print("Thanks for using this script...")
print()
