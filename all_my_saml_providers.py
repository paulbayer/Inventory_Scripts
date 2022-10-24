#!/usr/bin/env python3

import boto3
import Inventory_Modules
import logging
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

init()

parser = CommonArguments()
parser.singleprofile()
parser.singleregion()
parser.verbosity()
parser.my_parser.add_argument(
	"+delete", "+forreal",
	dest="DeletionRun",
	const=True,
	default=False,
	action="store_const",
	help="This will delete the identity providers found - without any opportunity to confirm. Be careful!!")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Region
verbose = args.loglevel
DeletionRun = args.DeletionRun
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'

print()

aws_acct = aws_acct_access(pProfile)
fmt = '%-20s %-15s %-15s'
print(fmt % ("Account", "pRegion", "IDP Name"))
print(fmt % ("-------", "------", "--------"))
ChildAccounts = aws_acct.ChildAccounts

NumofAccounts = len(ChildAccounts)
IdpsFound = []
for account in ChildAccounts:
	try:
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, account['AccountId'])
		account_credentials['AccountNumber'] = account['AccountId']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{pProfile}: Authorization Failure for account {account['AccountId']}")
		else:
			print(f"{pProfile}: Other kind of failure for account {account['AccountId']}")
			print(my_Error)
		break
	try:
		Idps = Inventory_Modules.find_saml_components_in_acct2(account_credentials, pRegion)
		idpNum = len(Idps)
		logging.warning(f"Account: {account['AccountId']} | Region: {pRegion} | Found {idpNum} Idps")
		logging.warning(f"{ERASE_LINE}{Fore.RED}Account: {account['AccountId']} pRegion: {pRegion} Found {idpNum} Idps. Only {NumofAccounts} accounts left to go{Fore.RESET}")
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{account['AccountId']}: Authorization Failure")
		idpNum = 0
	if idpNum > 0:
		for y in range(len(Idps)):
			logging.warning(f"Arn: {Idps[y]['Arn']}")
			NameStart = Idps[y]['Arn'].find('/')+1
			logging.debug(f"Name starts at character: {NameStart}")
			IdpName = Idps[y]['Arn'][NameStart:]
			print(fmt % (account['AccountId'], pRegion, IdpName))
			IdpsFound.append({
				'AccountId': account['AccountId'],
				'pRegion': pRegion,
				'IdpName': IdpName,
				'Arn': Idps[y]['Arn']})
	NumofAccounts -= 1

print(ERASE_LINE)
print(Fore.RED+f"Found {len(IdpsFound)} Idps across {len(ChildAccounts)} accounts in region {pRegion}"+Fore.RESET)
print()

if DeletionRun:
	logging.warning(f"Deleting {len(IdpsFound)} Idps")
	for y in range(len(IdpsFound)):
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, IdpsFound[y]['AccountId'])
		session_aws = boto3.Session(region_name=IdpsFound[y]['pRegion'],
									aws_access_key_id=account_credentials['AccessKeyId'],
									aws_secret_access_key=account_credentials['SecretAccessKey'],
									aws_session_token=account_credentials['SessionToken'])
		iam_client = session_aws.client('iam')
		print(f"Deleting Idp {IdpsFound[y]['IdpName']} from account {IdpsFound[y]['AccountId']} in pRegion {IdpsFound[y]['pRegion']}")
		response = iam_client.delete_saml_provider(SAMLProviderArn=IdpsFound[y]['Arn'])

print()
print("Thanks for using this script...")
print()
