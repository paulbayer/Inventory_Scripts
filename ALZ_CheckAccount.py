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
	required=True,
	help="To specify a specific profile, use this parameter. Default will be your default profile.")
parser.add_argument(
	"-a", "--account",
	dest="pChildAccountId",
	metavar="New Account to be adopted into LZ",
	default="123456789012",
	required=True,
	help="This is the account number of the account you're checking, to see if it can be adopted into the ALZ.")
parser.add_argument(
	"+delete","+forreal",
	dest="DeletionRun",
	const=True,
	default=False,
	action="store_const",
	help="This will delete the stacks found - without any opportunity to confirm. Be careful!!")
parser.add_argument(
	'-dd', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 10
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-d',
	help="Print debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING, # args.loglevel = 30
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR, # args.loglevel = 40
	default=logging.CRITICAL) # args.loglevel = 50
args = parser.parse_args()

pProfile=args.pProfile
pChildAccountId=args.pChildAccountId
verbose=args.loglevel
DeletionRun=args.DeletionRun
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")
# This is hard-coded, because this is the listing of regions that are supported by Automated Landing Zone.
RegionList=['ap-northeast-1', 'ap-northeast-2', 'ap-south-1', 'ap-southeast-1', 'ap-southeast-2', 'ca-central-1', 'eu-central-1', 'eu-north-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'sa-east-1', 'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']

ERASE_LINE = '\x1b[2K'

"""
Steps of this script ceom from here: https://w.amazon.com/bin/view/AWS/Teams/SA/AWS_Solutions_Builder/Working_Backwards/AWS_Solutions-Foundations-Landing-Zone/Landing_Zone_FAQs/#HWhatifmycustomerdoesn27twanttotakenoforananswer3F

0. The Child account MUST allow the Master account access into the Child IAM role called "AWSCloudFormationStackSetExecutionRole"

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

4. There must be an AWSCloudFormationStackSetExecution role present in the account so that StackSets can assume it and deploy stack instances. This role must trust the Organizations Master account. In LZ the account is created with that role name so stacksets just works. You can add this role manually via CloudFormation in the existing account. [I did this as a step 0]

5. The account must not have a pending guard duty invite. You can check from the Guard Duty Console

6. STS must be active in all regions. You can check from the Account Settings page in IAM.

7. The account must be part of the Organization and the email address being entered into the LZ parameters must match the account. If 	you try to add an email from an account which is not part of the Org, you will get an error that you are not using a unique email address. If it’s part of the Org, LZ just finds the account and uses the CFN roles.
- If the existing account is to be imported as a Core Account, modify the manifest.yaml file to use it.
- If the existing account will be a child account in the Organization, use the AVM launch template through Service Catalog and enter the appropriate configuration parameters.
​​​​​​​
8. The existing account can not be in any of the LZ-managed Organizations OUs. By default, these OUs are Core and Applications, but the customer may have chosen different or additional OUs to manage by LZ.

"""
print()
session_aws = boto3.Session(profile_name=pProfile)
client_sts = session_aws.client('sts')
role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(pChildAccountId)
logging.info("Role ARN: %s" % role_arn)
# Step 0 -
# 0. The Child account MUST allow the Master account access into the Child IAM role called "AWSCloudFormationStackSetExecutionRole"

print("This script does 5 things... ")
print("	1. Checks to ensure the 'AWSCloudFormationStackSetExecutionRole' exists in the child account and trusts the Master Org account")
print("	2. Checks the child account in each of the regions that support ALZ to see if there's already a Config Recorder and Delivery Channel enabled...")
print("	3. Checks that there isn't a CloudTrail trail called 'AWS-Landing-Zone-BaselineCloudTrail' in the account. ")
print(" 4. Checks to see if GuardDuty has been enabled for this child account. If it has been, it needs to be deleted before we can adopt this new account into the Org's Automated Landing Zone.")
print("	5. This child account must exist within the Parent Organization. If it doesn't - then you must move it into this Org (this script can't do that for you).")
print()
print("Since this script is fairly new - All comments or suggestions are enthusiastically encouraged")
print()

try:
	account_credentials = client_sts.assume_role(
		RoleArn=role_arn,
		DurationSeconds=3600,
		RoleSessionName="ALZ_CheckAccount")['Credentials']
	account_credentials['AccountNumber']=pChildAccountId
	logging.error("Was able to successfully get credentials")
	# pprint.pprint(account_credentials)
except ClientError as my_Error:
	if str(my_Error).find("AuthFailure") > 0:
		print("{}: Authorization Failure for account {}".format(pProfile,pChildAccountId))
		print("The child account MUST allow access into the IAM role 'AWSCloudFormationStackSetExecutionRole' from the Organization's Master Account for the rest of this script (and the overall migration) to run.")
		print("You must add the following lines to the Trust Policy of that role in the child account")
		print(json_formatted_str_TP)
		print(my_Error)
		sys.exit("Exiting due to Authorization Failure...")
	elif str(my_Error).find("AccessDenied") > 0:
		print("{}: Access Denied Failure for account {}".format(pProfile,pChildAccountId))
		print("The child account MUST allow access into the IAM role 'AWSCloudFormationStackSetExecutionRole' from the Organization's Master Account for the rest of this script (and the overall migration) to run.")
		print("You must add the following lines to the Trust Policy of that role in the child account")
		print(json_formatted_str_TP)
		print(my_Error)
		sys.exit("Exiting due to Access Denied Failure...")
	else:
		print("{}: Other kind of failure for account {}".format(pProfile,pChildAccountId))
		print (my_Error)
		sys.exit("Exiting...")

logging.error("Was able to successfully connect using the credentials... ")

print()
# Step 2
	# This part will check the Config Recorder and  Delivery Channel. If they have one, we need to delete it, so we can create another. We'll ask whether this is ok before we delete.
try:
	# RegionList=Inventory_Modules.get_service_regions('config','all')
	ConfigList=[]
	DeliveryChanList=[]
	"""
	TO-DO: Need to find a way to gracefully handle the error processing of opt-in regions.
	"""
	# RegionList.remove('me-south-1')	# Opt-in region, which causes a failure if we check and it's not opted-in
	# RegionList.remove('ap-east-1')	# Opt-in region, which causes a failure if we check and it's not opted-in
	for region in RegionList:
		print(ERASE_LINE,"Checking account {} in region {} for Config Recorder".format(account_credentials['AccountNumber'],region),end='\r')
		logging.info("Looking for Config Recorders in account %s from Region %s",account_credentials['AccountNumber'],region)
		# ConfigRecorder=client_cfg.describe_configuration_recorders()
		ConfigRecorder=Inventory_Modules.find_config_recorders(account_credentials, region)
		logging.debug("Tried to capture Config Recorder")
		if len(ConfigRecorder['ConfigurationRecorders']) > 0:
			ConfigList.append({
				'Name':ConfigRecorder['ConfigurationRecorders'][0]['name'],
				'roleARN':ConfigRecorder['ConfigurationRecorders'][0]['roleARN'],
				'AccountID':pChildAccountId,
				'Region':region
			})
		print(ERASE_LINE,"Checking account {} in region {} for Delivery Channel".format(account_credentials['AccountNumber'],region),end='\r')
		DeliveryChannel=Inventory_Modules.find_delivery_channels(account_credentials, region)
		logging.debug("Tried to capture Delivery Channel")
		if len(DeliveryChannel['DeliveryChannels']) > 0:
			DeliveryChanList.append({
				'Name':DeliveryChannel['DeliveryChannels'][0]['name'],
				'AccountID':pChildAccountId,
				'Region':region
			})
except ClientError as my_Error:
	logging.critical("Failed to capture Config Recorder and Delivery Channels")
	print(my_Error)

for i in range(len(ConfigList)):
	print("I found a config recorder for account {} in region {}".format(ConfigList[i]['AccountID'],ConfigList[i]['Region']))
	if DeletionRun:
		logging.warning("Deleting %s in account %s in region %s",ConfigList[i]['Name'],ConfigList[i]['AccountID'],ConfigList[i]['Region'])
		DelConfigRecorder=Inventory_Modules.del_config_recorder(account_credentials, region, ConfigList[i]['Name'])
for i in range(len(DeliveryChanList)):
	print("I found a delivery channel for account {} in region {}".format(DeliveryChanList[i]['AccountID'],DeliveryChanList[i]['Region']))
	if DeletionRun:
		logging.warning("Deleting %s in account %s in region %s",DeliveryChanList[i]['Name'],DeliveryChanList[i]['AccountID'],DeliveryChanList[i]['Region'])
		DelDeliveryChannel=Inventory_Modules.del_delivery_channel(account_credentials, region, DeliveryChanList[i]['Name'])

print()
# Step 3
# 3. The account must not have a Cloudtrail Trail name the same name as the LZ Trail ("AWS-Landing-Zone-BaselineCloudTrail")
try:
	# RegionList=Inventory_Modules.get_service_regions('cloudtrail','all')
	# RegionList.remove('me-south-1')	# Opt-in region, which causes a failure if we check and it's not opted-in
	# RegionList.remove('ap-east-1')	# Opt-in region, which causes a failure if we check and it's not opted-in
	CTtrails2=[]
	for region in RegionList:
		print(ERASE_LINE,"Checking account {} in region {} for CloudTrail named 'AWS-Landing-Zone-BaselineCloudTrail'".format(account_credentials['AccountNumber'],region),end='\r')
		logging.warning("Checking region %s for Cloud Trails",region)
		ctrail='arn:aws:cloudtrail:'+region+':'+account_credentials['AccountNumber']+':trail/AWS-Landing-Zone-BaselineCloudTrail'
		CTtrails=Inventory_Modules.find_cloudtrails(account_credentials,region,ctrail)
		if len(CTtrails) > 0:
			logging.error("Unfortunately, we've found a CloudTrail log named 'AWS-LandingZone-BaselineCloudTrail' in account %s in the %s region, which means we'll have to delete it before this account can be adopted.",account_credentials['AccountNumber'],region)
			CTtrails2.append(CTtrails[0])
except ClientError as my_Error:
	print(my_Error)

# pprint.pprint(CTtrails2)
# sys.exit(99)
for i in range(len(CTtrails2)):
	print("I found a CloudTrail trail for account {} in region {} named 'AWS-LandingZone-BaselineCloudTrail' ".format(account_credentials['AccountNumber'],CTtrails2[i]['HomeRegion']))
	if DeletionRun:
		try:
			delresponse=Inventory_Modules.del_cloudtrails(account_credentials,region,CTtrails2[i]['TrailARN'])
			logging.error("CloudTrail trail deletion commencing...")
		except ClientError as my_Error:
			print(my_Error)

print()
# Step 4 - handled by Step 0
# 4. There must be an AWSCloudFormationStackSetExecution role present in the account so that StackSets can assume it and deploy stack instances. This role must trust the Organizations Master account. In LZ the account is created with that role name so stacksets just works. You can add this role manually via CloudFormation in the existing account.

print()
# Step 5
# 5. The account must not have a pending guard duty invite. You can check from the Guard Duty Console
try:
	# RegionList=Inventory_Modules.get_service_regions('guardduty','all')
	# RegionList.remove('me-south-1')	# Opt-in region, which causes a failure if we check and it's not opted-in
	# RegionList.remove('ap-east-1')	# Opt-in region, which causes a failure if we check and it's not opted-in
	GDinvites2=[]
	for region in RegionList:
		print(ERASE_LINE,"Checking account {} in region {} for GuardDuty invitations".format(account_credentials['AccountNumber'],region),end='\r')
		logging.error("Checking account %s in region %s for GuardDuty invites",account_credentials['AccountNumber'],region)
		GDinvites=Inventory_Modules.find_gd_invites(account_credentials,region)
		if len(GDinvites) > 0:
			for x in range(len(GDinvites['Invitations'])):
				logging.warning("GD Invite: %s",str(GDinvites['Invitations'][x]))
				logging.error("Unfortunately, we've found a GuardDuty invitation for account %s in the %s region from account %s, which means we'll have to delete it before this account can be adopted.",account_credentials['AccountNumber'],region,GDinvites['Invitations'][x]['AccountId'])
				GDinvites2.append({
					'AccountId':GDinvites['Invitations'][x]['AccountId'],
					'InvitationId':GDinvites['Invitations'][x]['InvitationId'],
					'Region':region
				})
except ClientError as my_Error:
	print(my_Error)

for i in range(len(GDinvites2)):
	print("I found a GuardDuty invitation for account {} in region {} from account {} ".format(account_credentials['AccountNumber'],GDinvites2[i]['Region'],GDinvites2[i]['AccountId']))
	if DeletionRun:
		for x in range(len(GDinvites2)):
			try:
				logging.warning("GuardDuty invite deletion commencing...")
				delresponse=Inventory_Modules.delete_gd_invites(account_credentials, region, GDinvites2[x]['AccountId'])
			except ClientError as my_Error:
				print(my_Error)

# Step 6
# 6. STS must be active in all regions. You can check from the Account Settings page in IAM.
"""
We would have already verified this - since we've used STS to connect to each region already for the previous steps.
"""
# Step 7

'''
7. The account must be part of the Organization and the email address being entered into the LZ parameters must match the account. If 	you try to add an email from an account which is not part of the Org, you will get an error that you are not using a unique email address. If it’s part of the Org, LZ just finds the account and uses the CFN roles.
- If the existing account is to be imported as a Core Account, modify the manifest.yaml file to use it.
- If the existing account will be a child account in the Organization, use the AVM launch template through Service Catalog and enter the appropriate configuration parameters.
'''
# Step 8
# 8. The existing account can not be in any of the LZ-managed Organizations OUs. By default, these OUs are Core and Applications, but the customer may have chosen different or additional OUs to manage by LZ.
"""
So we'll need to verify that the parent OU of the account is the root of the organization.
"""

print()
print("Thanks for using this script...")
