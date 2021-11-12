#!/usr/bin/env python3

import logging
import Inventory_Modules
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

init()
parser = CommonArguments()
parser.version()
parser.singleprofile()
parser.verbosity()          # Allows for the verbosity to be handled.
parser.my_parser.add_argument(
	"-f", "--file",
	dest="pAccountFile",
	metavar="Account File",
	# default="accountfile.txt",
	help="List of account numbers, one per line.")
parser.my_parser.add_argument(
	"-r", "--Role",
	dest="pAccessRole",
	metavar="Access Role",
	default="Admin",
	help="Role used to gain access to the list of accounts.")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pAccountFile = args.pAccountFile
pAccessRole = args.pAccessRole
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

aws_acct = aws_acct_access(pProfile)

#####################


def check_account_access(faws_acct, faccount_num, fAccessRole=None):

	if fAccessRole is None:
		logging.error(f"Role must be provided")
		return_response = {'Success': False, 'ErrorMessage': "Role wasn't provided"}
		return(return_response)
	sts_client = faws_acct.session.client('sts')
	try:
		role_arn = "arn:aws:iam::{}:role/{}".format(faccount_num, fAccessRole)
		credentials = sts_client.assume_role(RoleArn=role_arn,
		                                  RoleSessionName='TheOtherGuy')['Credentials']
		return_response = {'Credentials': credentials, 'Success': True, 'ErrorMessage': ""}
		return(return_response)
	except ClientError as my_Error:
		print(f"Client Error: {my_Error}")
		return_response = {'Success': False, 'ErrorMessage': "Client Error"}
		return(return_response)
	except sts_client.exceptions.MalformedPolicyDocumentException as my_Error:
		print(f"MalformedPolicy: {my_Error}")
		return_response = {'Success': False, 'ErrorMessage': "Malformed Policy"}
		return(return_response)
	except sts_client.exceptions.PackedPolicyTooLargeException as my_Error:
		print(f"Policy is too large: {my_Error}")
		return_response = {'Success': False, 'ErrorMessage': "Policy is too large"}
		return(return_response)
	except sts_client.exceptions.RegionDisabledException as my_Error:
		print(f"Region is disabled: {my_Error}")
		return_response = {'Success': False, 'ErrorMessage': "Region Disabled"}
		return(return_response)
	except sts_client.exceptions.ExpiredTokenException as my_Error:
		print(f"Expired Token: {my_Error}")
		return_response = {'Success': False, 'ErrorMessage': "Expired Token"}
		return(return_response)

#####################


Accounts = []
with open(pAccountFile, 'r') as infile:
	for line in infile:
		Accounts.append(line.rstrip('\r\n,'))
infile.close()

for account_num in Accounts:
	logging.info(f"Accessing account #{account_num} as {pAccessRole} using account's {aws_acct.acct_number}'s credentials")
	response = check_account_access(aws_acct, account_num, pAccessRole)
	if response['Success']:
		print(f"Account {account_num} was successfully connected via role {pAccessRole} from {aws_acct.acct_number}")
		"""
		Put more commands here... Or you can write functions that represent your commands and call them from here.
		"""
	else:
		print(f"Access Role {pAccessRole} failed to connect to {account_num} from {aws_acct.acct_number} with error: {response['ErrorMessage']}")

print()
print("Thanks for using this script...")
print()
