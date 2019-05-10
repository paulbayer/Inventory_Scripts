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
	description="We\'re going to find all saml identity providers within any of the child accounts within the organization.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="To specify a specific profile, use this parameter. Default will be your default profile.")
parser.add_argument(
	"-k","--skip",
	dest="pSkipAccounts",
	nargs="*",
	metavar="Accounts to leave alone",
	default=[],
	help="These are the account numbers you don't want to screw with. Likely the core accounts. Separate them by a space.")
# parser.add_argument(
# 	"-r","--region",
# 	nargs="*",
# 	dest="pregion",
# 	metavar="region name string",
# 	default=["us-east-1"],
# 	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
	"+delete","+forreal",
	dest="DeletionRun",
	const=True,
	default=False,
	action="store_const",
	help="This will delete the identity providers found - without any opportunity to confirm. Be careful!!")
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
# pRegionList=args.pregion
AccountsToSkip=args.pSkipAccounts
verbose=args.loglevel
DeletionRun=args.DeletionRun
logging.basicConfig(level=args.loglevel)

##########################
ERASE_LINE = '\x1b[2K'

print()
fmt='%-20s %-15s %-15s'
print(fmt % ("Account","Region","IDP Name"))
print(fmt % ("-------","------","--------"))
# RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
ChildAccounts=Inventory_Modules.RemoveCoreAccounts(ChildAccounts,AccountsToSkip)
# pprint.pprint(AccountsToSkip)
# pprint.pprint(ChildAccounts)
# sys.exit(1)
NumofAccounts=len(ChildAccounts)
IdpsFound=[]
aws_session = boto3.Session(profile_name=pProfile)
sts_client = aws_session.client('sts')
for account in ChildAccounts:
	role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(account['AccountId'])
	logging.info("Role ARN: %s" % role_arn)
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-Stacks")['Credentials']
		account_credentials['AccountNumber']=account['AccountId']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(pProfile+": Authorization Failure for account {}".format(account['AccountId']))
		else:
			print(pProfile+": Other kind of failure for account {}".format(account['AccountId']))
			print (my_Error)
		break
	# for region in RegionList:
	try:
		idpNum=0
		Idps=Inventory_Modules.find_saml_components_in_acct(account_credentials,region)
		# pprint.pprint(Stacks)
		idpNum=len(Idps)
		logging.warning("Account: %s | Region: %s | Found %s Idps", account['AccountId'], region, idpNum )
		print(ERASE_LINE,Fore.RED+"Account: {} Region: {} Found {} Idps. {} accounts to go".format(account['AccountId'],region,idpNum,NumofAccounts)+Fore.RESET,end='\r')
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(account['AccountId']+": Authorization Failure")
	if idpNum > 0:
		for y in range(len(Idps)):
			logging.warning("Arn: %s",Idps[y]['Arn'])
			NameStart=Idps[y]['Arn'].find('/')+1
			logging.warning("Name starts at character: %s",NameStart)
			IdpName=Idps[y]['Arn'][NameStart:]
			print(fmt % (account['AccountId'],region,IdpName))
			IdpsFound.append({
				'Account':account['AccountId'],
				'Region':region,
				'IdpName':IdpName,
				'Arn':Idps[y]['Arn'] })
	NumofAccounts-=1

print(ERASE_LINE)
print(Fore.RED+"Found {} Idps across {} accounts across {} regions".format(len(IdpsFound),len(ChildAccounts),len(RegionList))+Fore.RESET)
print()
# pprint.pprint(IdpsFound)

if DeletionRun:
	logging.warning("Deleting %s Idps",len(IdpsFound))
	for y in range(len(IdpsFound)):
		role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(IdpsFound[y]['Account'])
		sts_client=aws_session.client('sts')
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-Idps")['Credentials']
		session_aws=boto3.Session(region_name=IdpsFound[y]['Region'],
				aws_access_key_id = account_credentials['AccessKeyId'],
				aws_secret_access_key = account_credentials['SecretAccessKey'],
				aws_session_token = account_credentials['SessionToken']
				)
		iam_client=session_aws.client('iam')
		print("Deleting Idp {} from account {} in region {}".format(IdpsFound[y]['IdpName'],IdpsFound[y]['Account'],IdpsFound[y]['Region']))
		response=iam_client.delete_saml_provider(SAMLProviderArn=IdpsFound[y]['Arn'])

print("Thanks for using this script...")
