#!/usr/bin/env python3


# import boto3
import Inventory_Modules
from account_class import aws_acct_access
from ArgumentsClass import CommonArguments
from colorama import init
from botocore.exceptions import ClientError

import logging

init()

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = CommonArguments()
parser.singleprofile()
parser.verbosity()
args = parser.my_parser.parse_args()

pProfile = args.Profile
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")


##########################
ERASE_LINE = '\x1b[2K'

aws_acct = aws_acct_access(pProfile)

ChildAccounts = aws_acct.ChildAccounts

NumUsersFound = 0
print()
fmt = '%-15s %-20s'
print(fmt % ("Account Number", "User Name"))
print(fmt % ("--------------", "---------"))

sts_client = aws_acct.session.client('sts')
Users = []
for account in ChildAccounts:
	role_arn = (f"arn:aws:iam::{account['AccountId']}:role/AWSCloudFormationStackSetExecutionRole")
	logging.info(f"Role ARN: {role_arn}")
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-Users")['Credentials']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{account}: Authorization Failure for account {account['AccountId']}")
		break
	try:
		Users = Inventory_Modules.find_users2(account_credentials)
		NumUsersFound += len(Users)
		logging.info(f"{ERASE_LINE}Account: {account['AccountId']} Found {len(Users)} users")
		print(f"{ERASE_LINE}Account: {account['AccountId']} Found {len(Users)} users", end='\r')
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{ERASE_LINE}{account}: Authorization Failure")
	except TypeError as my_Error:
		# print(my_Error)
		pass
	for y in range(len(Users)):
		print(fmt % (account['AccountId'], Users[y]['UserName']))
print(ERASE_LINE)
print(f"Found {NumUsersFound} users across {len(ChildAccounts)} accounts")
print()
