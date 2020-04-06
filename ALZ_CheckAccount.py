#!/usr/local/bin/python3

import os, sys, pprint, boto3, json
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
	"-p", "--profile",
	dest="pProfile",
	metavar="profile of Master Organization",
	default="default",
	help="To specify a specific profile, use this parameter. Default will be your default profile.")
parser.add_argument(
	"-a", "--account",
	dest="pChildAccountId",
	metavar="New Account to be adopted into LZ",
	default="723919836827",
	help="This is the account number of the account you're checking, to see if it can be adopted into the ALZ.")
parser.add_argument(
	"+delete","+forreal",
	dest="DeletionRun",
	const=True,
	default=False,
	action="store_const",
	help="This will delete the stacks found - without any opportunity to confirm. Be careful!!")
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
pChildAccountId=args.pChildAccountId
verbose=args.loglevel
DeletionRun=args.DeletionRun
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")

##########################
def sort_by_email(elem):
	return(elem('AccountEmail'))
##########################
ERASE_LINE = '\x1b[2K'

"""
Steps of this script ceom from here: https://w.amazon.com/bin/view/AWS/Teams/SA/AWS_Solutions_Builder/Working_Backwards/AWS_Solutions-Foundations-Landing-Zone/Landing_Zone_FAQs/#HWhatifmycustomerdoesn27twanttotakenoforananswer3F

1. The account must not contain any resources/config associated with the Default VPCs in ANY region e.g. security groups cannot exist associated with the Default VPC. Default VPCs will be deleted in the account in all regions, if they contain some dependency (usually a Security Group or an EIP) then deleting the VPC fails and the deployment rolls back. You can either manually delete them all or verify there are no dependencies, in some cases manually deleting them all is faster than roll back.

2. There must be no active config channel and recorder in the account as “there can be only one” of each. This must also be deleted via CLI, not console, switching config off in the console is NOT good enough and just disables it. To Delete the delivery channel and the configuration recorder (can be done via CLI and Python script only):
aws configservice describe-delivery-channels
aws configservice describe-delivery-channel-status
aws configservice describe-configuration-recorders
aws configservice stop-configuration-recorder --configuration-recorder-name <NAME-FROM-DESCRIBE-OUTPUT>
aws configservice delete-delivery-channel --delivery-channel-name <NAME-FROM-DESCRIBE-OUTPUT>
aws configservice delete-configuration-recorder --configuration-recorder-name <NAME-FROM-DESCRIBE-OUTPUT

It's also possible to run a shell script to automate the deletion of all recorders, here is an example (make sure you and the customer understand what you are deleting): delete_config_channels.sh

3. The account must not have a Cloudtrail Trail name the same name as the LZ Trail ("AWS-Landing-Zone-BaselineCloudTrail")

4. There must be an AWSCloudFormationStackSetExecution role present in the account so that StackSets can assume it and deploy stack instances. This role must trust the Organizations Master account. In LZ the account is created with that role name so stacksets just works. You can add this role manually via CloudFormation in the existing account.

5. The account must not have a pending guard duty invite. You can check from the Guard Duty Console

6. STS must be active in all regions. You can check from the Account Settings page in IAM.

7. The account must be part of the Organization and the email address being entered into the LZ parameters must match the account. If 	you try to add an email from an account which is not part of the Org, you will get an error that you are not using a unique email address. If it’s part of the Org, LZ just finds the account and uses the CFN roles.
- If the existing account is to be imported as a Core Account, modify the manifest.yaml file to use it.
- If the existing account will be a child account in the Organization, use the AVM launch template through Service Catalog and enter the appropriate configuration parameters.
​​​​​​​
8. The existing account can not be in any of the LZ-managed Organizations OUs. By default, these OUs are Core and Applications, but the customer may have chosen different or additional OUs to manage by LZ.

"""

print()
fmt='%-15s %-50s %-35s %-10s %-18s %-20s'
print(fmt % ("Account Number","SC Product Name","CFN Stack Name","SC Status","CFN Stack Status","AccountEmail"))
print(fmt % ("--------------","---------------","--------------","---------","----------------","------------"))

Trust_Policy='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"arn:aws:iam::<acct number>:root"}, "Action":"sts:AssumeRole"}]}'
json_object_TP=json.loads(Trust_Policy)
json_formatted_str_TP=json.dumps(json_object_TP,indent=2)

session_sts = boto3.Session(profile_name=pProfile)
client_sts = session_sts.client('sts')
role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(pChildAccountId)
logging.info("Role ARN: %s" % role_arn)
# Step 1 -
	# This will verify the first (and most important) criteria, that we have access to the child account with the properly named role.
try:
	account_credentials = client_sts.assume_role(
		RoleArn=role_arn,
		DurationSeconds=3600,
		RoleSessionName="ALZ_CheckAccount")['Credentials']
	account_credentials['AccountNumber']=pChildAccountId
	logging.error("Was able to successfully get credentials")
	pprint.pprint(account_credentials)
except ClientError as my_Error:
	if str(my_Error).find("AuthFailure") > 0:
		print("{}: Authorization Failure for account {}".format(pProfile,pChildAccountId))
		print("The child account MUST allow access into the IAM role 'AWSCloudFormationStackSetExecutionRole' from the Organization's Master Account for the rest of this script (and the overall migration) to run.")
		print("You must add the following lines to the Trust Policy of that role in the child account")
		print(json_formatted_str_TP)
		print(my_Error)
	elif str(my_Error).find("AccessDenied") > 0:
		print("{}: Access Denied Failure for account {}".format(pProfile,pChildAccountId))
		print("The child account MUST allow access into the IAM role 'AWSCloudFormationStackSetExecutionRole' from the Organization's Master Account for the rest of this script (and the overall migration) to run.")
		print("You must add the following lines to the Trust Policy of that role in the child account")
		print(json_formatted_str_TP)
		print(my_Error)
	else:
		print("{}: Other kind of failure for account {}".format(pProfile,pChildAccountId))
		print (my_Error)

logging.error("Was able to successfully connect using the credentials... ")
# Step 2
	# This part will check the Config Recorder and  Delivery Channel. If they have one, we need to delete it, so we can create another. We'll ask whether this is ok before we delete.
try:
	RegionList=Inventory_Modules.get_service_regions('config','all')
	ConfigList=[]
	DeliveryChanList=[]
	for region in RegionList:
		ConfigRecorder=Inventory_Modules.find_config_recorders(account_credentials, region)
		if 'ConfigurationRecorders' in ConfigRecorder.keys():
			ConfigList.append({
				'Name':ConfigRecorder['ConfigurationRecorders'][0]['name'],
				'roleARN':ConfigRecorder['ConfigurationRecorders'][0]['roleARN'],
				'AccountID':pChildAccountId,
				'Region':region
			})
		DeliveryChannel=Inventory_Modules.find_delivery_channels(account_credentials, region)
		if 'DeliveryChannels' in DeliveryChannel.keys():
			DeliveryChanList.append({
				'Name':DeliveryChannel['DeliveryChannels'][0]['name'],
				'AccountID':pChildAccountId,
				'Region':region
			})
except ClientError as my_Error:
	print(my_Error)

for i in range(len(ConfigList)):
	print("I found a config recorder for account {} in region {}".format(ConfigList[i]['AccountID'],ConfigList[i]['Region']))
for i in range(len(DeliveryChanList)):
	print("I found a delivery channel for account {} in region {}".format(DeliveryChanList[i]['AccountID'],DeliveryChanList[i]['Region']))

print()
print("Thanks for using this script...")
