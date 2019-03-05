#!/usr/local/bin/python3

import sys, pprint, argparse
# from sty import
import Inventory_Modules
import boto3, logging
from botocore.exceptions import ClientError, NoCredentialsError

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="Single Master profile to use",
	default="all",
	help="To specify a specific profile, use this parameter. There is no default for this")
parser.add_argument(
	"-r","--region",
	dest="pRegion",
	metavar="region name string",
	default="us-east-1",
	help="Region you're enabling.")
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const",
	dest="loglevel",
	const=logging.DEBUG,
    default=logging.CRITICAL)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.INFO)

args = parser.parse_args()

pProfile=args.pProfile
pRegion=args.pRegion
pService=args.pService
pCommand=args.pCommand
logging.basicConfig(level=args.loglevel)

##########################
ERASE_LINE = '\x1b[2K'

ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)

sts_session = boto3.Session(profile_name=pProfile)
sts_client = sts_session.client('sts',region_name=pRegion)

for account in ChildAccounts:
	# for region in RegionList:
	role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(account['AccountId'])
	account_credentials = sts_client.assume_role(
		RoleArn=role_arn,
		RoleSessionName="IAMTestScript")['Credentials']
	session_sh=boto3.Session(
		aws_access_key_id=account_credentials['AccessKeyId'],	aws_secret_access_key=account_credentials['SecretAccessKey'], aws_session_token=account_credentials['SessionToken'],
		region_name=pRegion)
	client_sh=session_sh.client('securityhub',region_name=pRegion)

	Invitations=client_sh.list_invitations()['Invitations']
	for invite in Invitations:
		try:
			Acceptance=client_sh.accept_invitation(
				MasterId=invite['AccountId'],
				InvitationId=invite['InvitationId'][0]
			)
			print("Accepted invitation to child account {} from Parent account {}".format(account['AccountId'],invite['AccountId']))

		except ClientError as e:
			print("Child Account {} had a problem with invitation".format(account['AccountId']))
			if e.response['Error']['Code'] == 'BadRequestException':
				logging.warning("Caught exception 'BadRequestException', handling the exception...")
				pass

print("There were {} Child Accounts".format(len(ChildAccounts)))
# print("There were {} roles in the all_responses list".format(ExecutionRoleCount))
