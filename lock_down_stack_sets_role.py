#!/user/bin/env python3

import sys
import boto3
import Inventory_Modules
import argparse
from botocore.exceptions import ClientError

import logging

parser = argparse.ArgumentParser(
	description="We\'re going to ensure the 'AWSCloudFormationStackSetExecutionRole' is locked down properly.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	required = True,
	default='default',
	metavar="profile to use",
	help="This profile should be for the Management Account - with access into the children.")
parser.add_argument(
	"-r", "--region",
	dest="pRegion",
	required = True,
	default='us-east-1',
	metavar="region to use",
	help="This profile should be for the Management Account - with access into the children.")
parser.add_argument(
	"-R", "--access_rolename",
	dest="pAccessRole",
	default='AWSCloudFormationStackSetExecutionRole',
	metavar="role to use for access to child accounts",
	help="This parameter specifies the role that will allow this script to have access to the children accounts.")
parser.add_argument(
	"-t", "--target_rolename",
	dest="pTargetRole",
	default='AWSCloudFormationStackSetExecutionRole',
	metavar="role to change",
	help="This parameter specifies the role to have its Trust Policy changed.")
parser.add_argument(
	"-l", "--lock",
	dest="pLock",
	action="store_const",
	const=True,
	default=False,
	help="This parameter determines whether to lock the Trust Policy.")
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
	default=logging.CRITICAL, # args.loglevel = 50
	dest="loglevel",
	const=logging.INFO)	# args.loglevel = 20
parser.add_argument(
	'-d', '--debug',
	help="Print debugging statements",
	action="store_const",
	default=logging.CRITICAL, # args.loglevel = 50
	dest="loglevel",
	const=logging.DEBUG)	# args.loglevel = 20
args = parser.parse_args()

pProfile=args.pProfile
pRegion=args.pRegion
pTargetRole=args.pTargetRole
pAccessRole=args.pAccessRole
pLock=args.pLock
verbose=args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")

ParentAcctNum=Inventory_Modules.find_account_number(pProfile)
ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
if len(ChildAccounts) == 0:
	print()
	print("The profile {} does not represent an Org".format(pProfile))
	print("This script only works with org accounts.")
	print()
	sys.exit(1)
##########################
ERASE_LINE = '\x1b[2K'
##########################

print("We're using the {} role to gain access to the child accounts".format(pAccessRole))
print("We're targeting the {} role to change its Trust Policy".format(pTargetRole))

'''
1. Collect SSM parameters with the ARNs that should be in the permission
2. Create the TrustPolicy in JSON
3. Get a listing of all accounts that need to be updated
4. Connect to each account, and update the existing trust policy with the new policy
'''
# 1. Collect parameters with the ARNs that should be in the permission
# lock_down_arns_list=[]
allowed_arns=[]
aws_session=boto3.Session(profile_name=pProfile, region_name=pRegion)
ssm_client=aws_session.client('ssm')
param_list=ssm_client.describe_parameters(ParameterFilters=[{'Key':'Name', 'Option':'Contains', 'Values':['lock_down_role_arns_list']}])['Parameters']
if len(param_list) == 0:
	print("You need to set the region (-r|--region) to the default region where the SSM parameters are stored.")
	print("Otherwise, with no *allowed* arns, we would lock everything out from this role.")
	print("Exiting...")
	sys.exit(2)
for i in param_list:
	response=param=ssm_client.get_parameter(Name=i['Name'])
	allowed_arns.append(response['Parameter']['Value'])

# 2. Create the Trust Policy in JSON
import simplejson as json

if pLock:
	Trust_Policy = {
		"Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "LambdaAccess",
                "Effect": "Allow",
                "Principal": {
	                "AWS": allowed_arns
                },
                "Action": "sts:AssumeRole"
            }
        ]}
else:
	Trust_Policy = {
		"Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "LambdaAccess",
                "Effect": "Allow",
                "Principal": {
	                "AWS": allowed_arns
                },
                "Action": "sts:AssumeRole"
            },
            {
                "Sid": "DevAccess",
                "Effect": "Allow",
                "Principal": {
	                "AWS": ["arn:aws:iam::{}:root".format(ParentAcctNum)]
                },
                "Action": "sts:AssumeRole"
            }
        ]}
Trust_Policy_json = json.dumps(Trust_Policy)
# 3. Get a listing of all accounts that need to be updated
child_accounts=Inventory_Modules.find_child_accounts2(pProfile)

# 4. Connect to each account, and detach the existing policy, and apply the new policy
sts_client = aws_session.client('sts')
TrustPoliciesChanged=0
for acct in child_accounts:
	ConnectionSuccess = False
	try:
		role_arn = "arn:aws:iam::{}:role/{}".format(acct['AccountId'], pAccessRole)
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="RegistrationScript")['Credentials']
		account_credentials['Account'] = acct['AccountId']
		logging.warning("Accessed Account %s using rolename %s" % (acct['AccountId'], pAccessRole))
		ConnectionSuccess = True
	except ClientError as my_Error:
		logging.error("Account %s is already locked down, so we couldn't change the role's Trust Policy", acct['AccountId'])
		logging.warning(my_Error)
		pass
	if ConnectionSuccess:
		try:
			# detach policy from the role and attach the new policy
			iam_session = boto3.Session(
				aws_access_key_id=account_credentials['AccessKeyId'],
				aws_secret_access_key=account_credentials['SecretAccessKey'],
				aws_session_token=account_credentials['SessionToken']
			)
			iam_client = iam_session.client('iam')
			trustpolicyupdate=iam_client.update_assume_role_policy(RoleName=pTargetRole, PolicyDocument=Trust_Policy_json)
			TrustPoliciesChanged+=1
		except ClientError as my_Error:
			logging.warning(my_Error)
			pass

print(ERASE_LINE)
print("We found {} accounts under your organization".format(len(ChildAccounts)))
print("We changed {} Trust Policies".format(TrustPoliciesChanged))
print("Thanks for using the tool.")
