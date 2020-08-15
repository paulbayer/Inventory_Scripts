#!/usr/local/bin/python3

import sys, pprint
import Inventory_Modules, vpc_modules
import argparse
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()

parser = argparse.ArgumentParser(
	description="We\'re going to determine whether this new account satisfies all the pre-reqs to be adopted by AWS Control Tower.",
	prefix_chars='-+/')
parser.add_argument(
	"--explain",
	dest="pExplain",
	metavar="profile of Master Organization",
	const=True,
	default=False,
	action="store_const",
	help="This flag prints out the explanation of what this script would do.")
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
	metavar="New Account to be adopted into Control Tower",
	default="123456789012",
	required=True,
	help="This is the account number of the account you're checking, to see if it can be adopted into AWS Control Tower.")
parser.add_argument(
	"-q", "--quick",
	dest="Quick",
	metavar="Shortcut the checking to only a single region",
	const=True,
	default=False,
	action="store_const",
	help="This flag only checks 'us-east-1', so makes the whole script run really fast.")
parser.add_argument(
	"+fix", "+delete",
	dest="FixRun",
	const=True,
	default=False,
	action="store_const",
	help="This will fix the issues found. If default VPCs must be deleted, you'll be asked to confirm.")
parser.add_argument(
	"+force",
	dest="pVPCConfirm",
	const=True,
	default=False,
	action="store_const",
	help="This will delete the default VPCs found with NO confirmation. You still have to specify the +fix too")
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
	'-vvv',
	help="Print debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO, 	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG, 	# args.loglevel = 10
	default=logging.CRITICAL) # args.loglevel = 50
args = parser.parse_args()

Quick=args.Quick
pProfile=args.pProfile
pChildAccountId=args.pChildAccountId
verbose=args.loglevel
FixRun=args.FixRun
pExplain=args.pExplain
pVPCConfirm=args.pVPCConfirm
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")
# This is hard-coded, because this is the listing of regions that are supported by Automated Landing Zone.
if Quick:
	RegionList=['us-east-1']
else:
	# RegionList=Inventory_Modules.get_ec2_regions('all', pProfile)
	# ap-northeast-3 doesn't support Config (and therefore doesn't support Control Tower), but is a region that is normally included within EC2. Therefore - this is easier.
	RegionList=['us-east-1', 'us-east-2', 'us-west-2', 'eu-west-1', 'ap-southeast-2']
	# RegionList.append('ap-northeast-1', 'ap-northeast-2', 'ap-south-1', 'ap-southeast-1',  'ca-central-1', 'eu-central-1', 'eu-north-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'sa-east-1')

ERASE_LINE = '\x1b[2K'
NumOfSteps=8

ExplainMessage="""
Objective: This script aims to make it easier to "adopt" an existing account into a Control Tower environment.

0. The Child account MUST allow the Master account access into the Child IAM role called "AWSControlTowerExecutionRole"
0a. There must be an "AWSControlTowerExecutionRole" role present in the account so that StackSets can assume it and deploy stack instances. This role must trust the Organizations Master account. In Control Tower, accounts are created with that role name so stacksets just work. You can add this role manually via CloudFormation in the existing account.
0b. STS must be active in all regions checked. You can check from the Account Settings page in IAM. Since we're using STS to connect to the account from the Master, this requirement is checked by successfully completing step 0.

2. There must be no active config channel and recorder in the account as “there can be only one” of each. This must also be deleted via CLI, not console, switching config off in the console is NOT good enough and just disables it. To Delete the delivery channel and the configuration recorder (can be done via CLI and Python script only):
aws configservice describe-delivery-channels
aws configservice describe-delivery-channel-status
aws configservice describe-configuration-recorders
aws configservice stop-configuration-recorder --configuration-recorder-name <NAME-FROM-DESCRIBE-OUTPUT>
aws configservice delete-delivery-channel --delivery-channel-name <NAME-FROM-DESCRIBE-OUTPUT>
aws configservice delete-configuration-recorder --configuration-recorder-name <NAME-FROM-DESCRIBE-OUTPUT

3. The account must not have a Cloudtrail Trail name with 'ControlTower' in the name ("aws-controltower-BaselineCloudTrail")

4. The account must not have a pending guard duty invite. You can check from the Guard Duty Console

5. The account must be part of the Organization and the email address being entered into the CT parameters must match the account. If you try to add an email from an account which is not part of the Org, you will get an error that you are not using a unique email address. If it’s part of the Org, CT just finds the account and uses the CFN roles.
- If the existing account is to be imported as a Core Account, modify the manifest.yaml file to use it.
- If the existing account will be a child account in the Organization, use the AVM launch template through Service Catalog and enter the appropriate configuration parameters.
​​​​​​​
6. The existing account can not be in any of the CT-managed Organizations OUs. By default, these OUs are Core and Applications, but the customer may have chosen different or additional OUs to manage by CT.


SNS topics name containing "ControlTower"
Lambda Functions name containing "ControlTower"
Role name containing "ControlTower"
Bucket created for AWS Config
SNS topic created for AWS Config
CloudWatch Log group containing "aws-controltower/CloudTrailLogs"
"""
print()
if pExplain:
	print(ExplainMessage)
	sys.exit("Exiting after Script Explanation...")

json_formatted_str_TP=""


def InitDict(StepCount):
	fProcessStatus={}
	fProcessStatus['ChildIsReady']=True
	fProcessStatus['IssuesFound']=0
	fProcessStatus['IssuesFixed']=0
	for i in range(StepCount):
		Step='Step'+str(i)
		fProcessStatus[Step]={}
		fProcessStatus[Step]['Success']=True
		fProcessStatus[Step]['IssuesFound']=0
		fProcessStatus[Step]['IssuesFixed']=0
	return(fProcessStatus)

ProcessStatus=InitDict(NumOfSteps)
# Step 0 -
# 0. The Child account MUST allow the Master account access into the Child IAM role called "AWSCloudFormationStackSetExecutionRole"

print("This script does {} things... ".format(NumOfSteps))
print(Fore.BLUE+"  0."+Fore.RESET+" Checks to ensure you have the necessary cross-account role access to the child account.")
print(Fore.BLUE+"  2."+Fore.RESET+" Checks the child account in each of the regions")
print("     to see if there's already a "+Fore.RED+"Config Recorder and Delivery Channel "+Fore.RESET+"enabled...")
print(Fore.BLUE+"  3."+Fore.RESET+" Checks that there isn't a duplicate "+Fore.RED+"CloudTrail"+Fore.RESET+" trail in the account.")
print(Fore.BLUE+"  4."+Fore.RESET+" Checks to see if "+Fore.RED+"GuardDuty"+Fore.RESET+" has been enabled for this child account.")
print("     If it has been, it needs to be deleted before we can adopt this new account")
print("     into the Org's Automated Landing Zone.")
print(Fore.BLUE+"  5."+Fore.RESET+" This child account "+Fore.RED+"must exist"+Fore.RESET+" within the Parent Organization.")
print("     If it doesn't - then you must move it into this Org")
print("     (this script can't do that for you).")
print()
print("Since this script is fairly new - All comments or suggestions are enthusiastically encouraged")
print()

try:
	account_credentials, role = Inventory_Modules.get_child_access2(pProfile, pChildAccountId)
	if role.find("failed") > 0:
		print(Fore.RED, "We weren't able to connect to the Child Account from this Master Account. Please check the role Trust Policy and re-run this script.", Fore.RESET)
		print("The following list of roles were tried, but none were allowed access to account {} using the {} profile".format(pChildAccountId, pProfile))
		print(Fore.RED, account_credentials, Fore.RESET)
		ProcessStatus['Step0']['Success']=False
		sys.exit("Exiting due to cross-account Auth Failure")
except ClientError as my_Error:
	if str(my_Error).find("AuthFailure") > 0:
		print("{}: Authorization Failure for account {}".format(pProfile, pChildAccountId))
		print("The child account MUST allow access into the IAM role {} from the Organization's Master Account for the rest of this script (and the overall migration) to run.".format(role))
		print("You must add the following lines to the Trust Policy of that role in the child account")
		print(json_formatted_str_TP)
		print(my_Error)
		ProcessStatus['Step0']['Success']=False
		sys.exit("Exiting due to Authorization Failure...")
	elif str(my_Error).find("AccessDenied") > 0:
		print("{}: Access Denied Failure for account {}".format(pProfile, pChildAccountId))
		print("The child account MUST allow access into the IAM role {} from the Organization's Master Account for the rest of this script (and the overall migration) to run.".format(role))
		print("You must add the following lines to the Trust Policy of that role in the child account")
		print(json_formatted_str_TP)
		print(my_Error)
		ProcessStatus['Step0']['Success']=False
		sys.exit("Exiting due to Access Denied Failure...")
	else:
		print("{}: Other kind of failure for account {}".format(pProfile, pChildAccountId))
		print(my_Error)
		ProcessStatus['Step0']['Success']=False
		sys.exit("Exiting...")

account_credentials['AccountNumber']=pChildAccountId
logging.error("Was able to successfully connect using the credentials... ")
print()
calling_creds=Inventory_Modules.find_calling_identity(pProfile)
print("Confirmed the role"+Fore.GREEN, role, Fore.RESET+"exists in account"+Fore.GREEN, pChildAccountId, Fore.RESET+"and trusts"+Fore.GREEN, "{}".format(calling_creds)+Fore.RESET, "within the Master Account")
print(Fore.GREEN+"** Step 0 completed without issues"+Fore.RESET)
print()

# Step 1
# This part will find and delete the Default VPCs in each region for the child account. We only delete if you provided that in the parameters list.
try:
	DefaultVPCs=[]
	for region in RegionList:
		print(ERASE_LINE, "Checking account {} in region {}".format(pChildAccountId, region), "for", Fore.RED+"default VPCs"+Fore.RESET, end='\r')
		logging.info("Looking for Default VPCs in account %s from Region %s", pChildAccountId, region)
		DefaultVPC=Inventory_Modules.find_account_vpcs(account_credentials, region, True)
		if len(DefaultVPC['Vpcs']) > 0:
			DefaultVPCs.append({
				'VPCId': DefaultVPC['Vpcs'][0]['VpcId'],
				'AccountID': pChildAccountId,
				'Region': region
			})
			ProcessStatus['Step1']['IssuesFound']+=1
			ProcessStatus['Step1']['Success']=False
except ClientError as my_Error:
	logging.warning("Failed to identify the Default VPCs in the region properly")
	ProcessStatus['Step1']['Success']=False
	print(my_Error)

print(ERASE_LINE, end='\r')
for i in range(len(DefaultVPCs)):
	# print("I found a default VPC for account {} in region {}".format(DefaultVPCs[i]['AccountID'], DefaultVPCs[i]['Region']), end='\n')
	if FixRun:
		logging.warning("Deleting VpcId %s in account %s in region %s", DefaultVPCs[i]['VPCId'], DefaultVPCs[i]['AccountID'], DefaultVPCs[i]['Region'])
		try:	# confirm the user really want to delete the VPC. This is irreversible
			if pVPCConfirm:
				ReallyDelete=True
			else:
				ReallyDelete=(input("Deletion of {} default VPC has been requested. Are you still sure? (y/n): ".format(DefaultVPCs[i]['Region'])) in ['y', 'Y'])
			if ReallyDelete:
				DelVPC_Success=(vpc_modules.del_vpc(account_credentials, DefaultVPCs[i]['VPCId'], DefaultVPCs[i]['Region'])==0)
				if DelVPC_Success:
					ProcessStatus['Step1']['IssuesFixed']+=1
				else:
					print("Something went wrong with the VPC Deletion")
					ProcessStatus['Step1']['Success']=False
					sys.exit(9)
			else:
				logging.warning("User answered False to the 'Are you sure' question")
				print("Skipping VPC ID {} in account {} in region {}".format(DefaultVPCs[i]['VPCId'], DefaultVPCs[i]['AccountID'], DefaultVPCs[i]['Region']))
				ProcessStatus['Step1']['Success']=False
		except ClientError as my_Error:
			logging.error("Failed to delete the Default VPCs in the region properly")
			ProcessStatus['Step1']['Success']=False
			print(my_Error)

print()
if ProcessStatus['Step1']['Success']:
	print(ERASE_LINE+Fore.GREEN+"** Step 1 completed with no issues"+Fore.RESET)
elif ProcessStatus['Step1']['IssuesFound']-ProcessStatus['Step1']['IssuesFixed']==0:
	print(ERASE_LINE+Fore.GREEN+"** Step 1 found {} issues, but they were fixed by deleting the default vpcs".format(ProcessStatus['Step1']['IssuesFound'])+Fore.RESET)
	ProcessStatus['Step1']['Success']=True
elif (ProcessStatus['Step1']['IssuesFound']>ProcessStatus['Step1']['IssuesFixed']):
	print(ERASE_LINE+Fore.RED+"** Step 1 completed, but there were {} vpcs that couldn't be fixed".format(ProcessStatus['Step1']['IssuesFound']-ProcessStatus['Step1']['IssuesFixed'])+Fore.RESET)
else:
	print(ERASE_LINE+Fore.RED+"** Step 1 completed with blockers found"+Fore.RESET)

# Step 2
	# This part will check the Config Recorder and  Delivery Channel. If they have one, we need to delete it, so we can create another. We'll ask whether this is ok before we delete.
try:
	# RegionList=Inventory_Modules.get_service_regions('config', 'all')
	print("Checking account {} for a Config Recorders and Delivery Channels in any region".format(pChildAccountId))
	ConfigList=[]
	DeliveryChanList=[]
	"""
	TO-DO: Need to find a way to gracefully handle the error processing of opt-in regions.
		Until then - we're using a hard-coded listing of regions, instead of dynamically finding those.
	"""
	# RegionList.remove('me-south-1')	# Opt-in region, which causes a failure if we check and it's not opted-in
	# RegionList.remove('ap-east-1')	# Opt-in region, which causes a failure if we check and it's not opted-in
	for region in RegionList:
		print(ERASE_LINE, "Checking account {} in region {} for Config Recorder".format(pChildAccountId, region), end='\r')
		logging.info("Looking for Config Recorders in account %s from Region %s", pChildAccountId, region)
		# ConfigRecorder=client_cfg.describe_configuration_recorders()
		ConfigRecorder=Inventory_Modules.find_config_recorders(account_credentials, region)
		logging.debug("Tried to capture Config Recorder")
		if len(ConfigRecorder['ConfigurationRecorders']) > 0:
			ConfigList.append({
				'Name': ConfigRecorder['ConfigurationRecorders'][0]['name'],
				'roleARN': ConfigRecorder['ConfigurationRecorders'][0]['roleARN'],
				'AccountID': pChildAccountId,
				'Region': region
			})
		print(ERASE_LINE, "Checking account {} in region {} for Delivery Channel".format(pChildAccountId, region), end='\r')
		DeliveryChannel=Inventory_Modules.find_delivery_channels(account_credentials, region)
		logging.debug("Tried to capture Delivery Channel")
		if len(DeliveryChannel['DeliveryChannels']) > 0:
			DeliveryChanList.append({
				'Name': DeliveryChannel['DeliveryChannels'][0]['name'],
				'AccountID': pChildAccountId,
				'Region': region
			})
	logging.error("Checked account %s in %s regions. Found %s issues with Config Recorders and Delivery Channels", pChildAccountId, len(RegionList), len(ConfigList)+len(DeliveryChanList))
except ClientError as my_Error:
	logging.warning("Failed to capture Config Recorder and Delivery Channels")
	ProcessStatus['Step2']['Success']=False
	print(my_Error)

for i in range(len(ConfigList)):
	logging.error(Fore.RED+"Found a config recorder for account %s in region %s", ConfigList[i]['AccountID'], ConfigList[i]['Region']+Fore.RESET)
	ProcessStatus['Step2']['Success']=False
	ProcessStatus['Step2']['IssuesFound']+=1
	if FixRun:
		logging.warning("Deleting %s in account %s in region %s", ConfigList[i]['Name'], ConfigList[i]['AccountID'], ConfigList[i]['Region'])
		DelConfigRecorder=Inventory_Modules.del_config_recorder(account_credentials, ConfigList[i]['Region'], ConfigList[i]['Name'])
		# We assume the process worked. We should probably NOT assume this.
		ProcessStatus['Step2']['IssuesFixed']+=1
for i in range(len(DeliveryChanList)):
	logging.error(Fore.RED+"I found a delivery channel for account %s in region %s", DeliveryChanList[i]['AccountID'], DeliveryChanList[i]['Region']+Fore.RESET)
	ProcessStatus['Step2']['Success']=False
	ProcessStatus['Step2']['IssuesFound']+=1
	if FixRun:
		logging.warning("Deleting %s in account %s in region %s", DeliveryChanList[i]['Name'], DeliveryChanList[i]['AccountID'], DeliveryChanList[i]['Region'])
		DelDeliveryChannel=Inventory_Modules.del_delivery_channel(account_credentials, ConfigList[i]['Region'], DeliveryChanList[i]['Name'])
		# We assume the process worked. We should probably NOT assume this.
		ProcessStatus['Step2']['IssuesFixed']+=1

if ProcessStatus['Step2']['Success']:
	print(ERASE_LINE+Fore.GREEN+"** Step 2 completed with no issues"+Fore.RESET)
elif ProcessStatus['Step2']['IssuesFound']-ProcessStatus['Step2']['IssuesFixed']==0:
	print(ERASE_LINE+Fore.GREEN+"** Step 2 found {} issues, but they were fixed by deleting the existing Config Recorders and Delivery Channels".format(ProcessStatus['Step2']['IssuesFound'])+Fore.RESET)
	ProcessStatus['Step2']['Success']=True
elif (ProcessStatus['Step2']['IssuesFound']>ProcessStatus['Step2']['IssuesFixed']):
	print(ERASE_LINE+Fore.RED+"** Step 2 completed, but there were {} items found that couldn't be deleted".format(ProcessStatus['Step2']['IssuesFound']-ProcessStatus['Step2']['IssuesFixed'])+Fore.RESET)
else:
	print(ERASE_LINE+Fore.RED+"** Step 2 completed with blockers found"+Fore.RESET)
print()
# Step 3
# 3. The account must not have a Cloudtrail Trail name the same name as the CT Trail ("AWS-Landing-Zone-BaselineCloudTrail")
try:
	print("Checking account {} for a specially named CloudTrail in all regions".format(pChildAccountId))
	CTtrails2=[]
	for region in RegionList:
		print(ERASE_LINE, "Checking account {} in region {} for CloudTrail trails".format(pChildAccountId, region), end='\r')
		CTtrails, trailname=Inventory_Modules.find_cloudtrails(account_credentials, region)
		if len(CTtrails['trailList']) > 0:
			logging.error("Unfortunately, we've found a CloudTrail log named %s in account %s in the %s region, which means we'll have to delete it before this account can be adopted.", trailname, pChildAccountId, region)
			CTtrails2.append(CTtrails['trailList'][0])
			ProcessStatus['Step3']['Success']=False
except ClientError as my_Error:
	print(my_Error)
	ProcessStatus['Step3']['Success']=False

# pprint.pprint(CTtrails)
# pprint.pprint(CTtrails2)
for i in range(len(CTtrails2)):
	logging.error(Fore.RED+"Found a CloudTrail trail for account %s in region %s named %s ", pChildAccountId, CTtrails2[i]['HomeRegion'], trailname+Fore.RESET)
	ProcessStatus['Step3']['IssuesFound']+=1
	if FixRun:
		try:
			logging.error("CloudTrail trail deletion commencing...")
			delresponse=Inventory_Modules.del_cloudtrails(account_credentials, region, CTtrails2[i]['TrailARN'])
			ProcessStatus['Step3']['IssuesFixed']+=1
		except ClientError as my_Error:
			print(my_Error)

if ProcessStatus['Step3']['Success']:
	print(ERASE_LINE+Fore.GREEN+"** Step 3 completed with no issues"+Fore.RESET)
elif ProcessStatus['Step3']['IssuesFound']-ProcessStatus['Step3']['IssuesFixed']==0:
	print(ERASE_LINE+Fore.GREEN+"** Step 3 found {} issues, but they were fixed by deleting the existing CloudTrail trail names".format(ProcessStatus['Step3']['IssuesFound'])+Fore.RESET)
	ProcessStatus['Step3']['Success']=True
elif (ProcessStatus['Step3']['IssuesFound']>ProcessStatus['Step3']['IssuesFixed']):
	print(ERASE_LINE+Fore.RED+"** Step 3 completed, but there were {} trail names found that couldn't be deleted".format(ProcessStatus['Step3']['IssuesFound']-ProcessStatus['Step3']['IssuesFixed'])+Fore.RESET)
else:
	print(ERASE_LINE+Fore.RED+"** Step 3 completed with blockers found"+Fore.RESET)
print()
# Step 4 - handled by Step 0
# 4. There must be an AWSCloudFormationStackSetExecution role present in the account so that StackSets can assume it and deploy stack instances. This role must trust the Organizations Master account. In CT the account is created with that role name so stacksets just works. You can add this role manually via CloudFormation in the existing account.

# Step 4
# 4. The account must not have a pending guard duty invite. You can check from the Guard Duty Console
try:
	print("Checking account {} for any GuardDuty invites".format(pChildAccountId))
	GDinvites2=[]
	for region in RegionList:
		logging.error("Checking account %s in region %s for", pChildAccountId, region+Fore.RED+" GuardDuty"+Fore.RESET+" invitations")
		logging.error("Checking account %s in region %s for GuardDuty invites", pChildAccountId, region)
		GDinvites=Inventory_Modules.find_gd_invites(account_credentials, region)
		if len(GDinvites) > 0:
			for x in range(len(GDinvites['Invitations'])):
				logging.warning("GD Invite: %s", str(GDinvites['Invitations'][x]))
				logging.error("Unfortunately, we've found a GuardDuty invitation for account %s in the %s region from account %s, which means we'll have to delete it before this account can be adopted.", pChildAccountId, region, GDinvites['Invitations'][x]['AccountId'])
				ProcessStatus['Step4']['IssuesFound']+=1
				GDinvites2.append({
					'AccountId': GDinvites['Invitations'][x]['AccountId'],
					'InvitationId': GDinvites['Invitations'][x]['InvitationId'],
					'Region': region
				})
except ClientError as my_Error:
	print(my_Error)
	ProcessStatus['Step4']['Success']=False

for i in range(len(GDinvites2)):
	logging.error(Fore.RED+"I found a GuardDuty invitation for account %s in region %s from account %s ", pChildAccountId, GDinvites2[i]['Region'], GDinvites2[i]['AccountId']+Fore.RESET)
	ProcessStatus['Step4']['IssuesFound']+=1
	ProcessStatus['Step4']['Success']=False
	if FixRun:
		for x in range(len(GDinvites2)):
			try:
				logging.warning("GuardDuty invite deletion commencing...")
				delresponse=Inventory_Modules.delete_gd_invites(account_credentials, region, GDinvites2[x]['AccountId'])
				ProcessStatus['Step4']['IssuesFixed']+=1
				# We assume the process worked. We should probably NOT assume this.
			except ClientError as my_Error:
				print(my_Error)

if ProcessStatus['Step4']['Success']:
	print(ERASE_LINE+Fore.GREEN+"** Step 4 completed with no issues"+Fore.RESET)
elif ProcessStatus['Step4']['IssuesFound']-ProcessStatus['Step4']['IssuesFixed']==0:
	print(ERASE_LINE+Fore.GREEN+"** Step 4 found {} guardduty invites, but they were deleted".format(ProcessStatus['Step4']['IssuesFound'])+Fore.RESET)
	ProcessStatus['Step4']['Success']=True
elif (ProcessStatus['Step4']['IssuesFound']>ProcessStatus['Step4']['IssuesFixed']):
	print(ERASE_LINE+Fore.RED+"** Step 4 completed, but there were {} guardduty invites found that couldn't be deleted".format(ProcessStatus['Step4']['IssuesFound']-ProcessStatus['Step4']['IssuesFixed'])+Fore.RESET)
else:
	print(ERASE_LINE+Fore.RED+"** Step 4 completed with blockers found"+Fore.RESET)
print()
# Step 4a
# 4a. STS must be active in all regions. You can check from the Account Settings page in IAM.
"""
We would have already verified this - since we've used STS to connect to each region already for the previous steps.
"""

# Step 5
'''
5. The account must be part of the Organization and the email address being entered into the CT parameters must match the account. If 	you try to add an email from an account which is not part of the Org, you will get an error that you are not using a unique email address. If it’s part of the Org, CT just finds the account and uses the CFN roles.
- If the existing account is to be imported as a Core Account, modify the manifest.yaml file to use it.
- If the existing account will be a child account in the Organization, use the AVM launch template through Service Catalog and enter the appropriate configuration parameters.
'''
# try:
print("Checking that the account is part of the AWS Organization.")
OrgAccounts=Inventory_Modules.find_child_accounts2(pProfile)
OrgAccountList=[]
for y in range(len(OrgAccounts)):
	OrgAccountList.append(OrgAccounts[y]['AccountId'])
if not (pChildAccountId in OrgAccountList):
	print()
	print("Account # {} is not a part of the Organization. This account needs to be moved into the Organization to be adopted into the Landing Zone tool".format(pChildAccountId))
	print("This is easiest done manually right now.")
	ProcessStatus['Step5']['Success']=False
	ProcessStatus['Step5']['IssuesFound']+=1

if ProcessStatus['Step5']['Success']:
	print(ERASE_LINE+Fore.GREEN+"** Step 5 completed with no issues"+Fore.RESET)
elif ProcessStatus['Step5']['IssuesFound']-ProcessStatus['Step5']['IssuesFixed']==0:
	print(ERASE_LINE+Fore.GREEN+"** Step 5 found {} issues, but we were able to move the account into the they were able to be fixed".format(ProcessStatus['Step5']['IssuesFound'])+Fore.RESET)
	ProcessStatus['Step5']['Success']=True
elif (ProcessStatus['Step5']['IssuesFound']>ProcessStatus['Step5']['IssuesFixed']):
	print(ERASE_LINE+Fore.RED+"** Step 5 completed, but there were {} blockers found that couldn't be fixed".format(ProcessStatus['Step5']['IssuesFound']-ProcessStatus['Step5']['IssuesFixed'])+Fore.RESET)
else:
	print(ERASE_LINE+Fore.RED+"** Step 5 completed with blockers found"+Fore.RESET)
print()
# Step 6
# 6. The existing account can not be in any of the CT-managed Organizations OUs. By default, these OUs are Core and Applications, but the customer may have chosen different or additional OUs to manage by CT.
"""
So we'll need to verify that the parent OU of the account is the root of the organization.

TODO Here
"""
# Step 7 - Check for other resources which have 'controltower' in the name
# Checking for SNS Topics
try:
	print("Checking account {} for any SNS topics containing the 'controltower' string".format(pChildAccountId))
	SNSTopics2=[]
	for region in RegionList:
		logging.error("Checking account %s in region %s for", pChildAccountId, region+Fore.RED+" SNS Topics"+Fore.RESET)
		SNSTopics=Inventory_Modules.find_sns_topics(account_credentials, region, ['controltower', 'ControlTower'])
		if len(SNSTopics) > 0:
			for x in range(len(SNSTopics)):
				logging.warning("SNS Topic: %s", str(SNSTopics[x]))
				logging.error("Unfortunately, we've found an SNS Topic  for account %s in the %s region, which means we'll have to delete it before this account can be adopted.", pChildAccountId, region)
				ProcessStatus['Step7']['IssuesFound']+=1
				SNSTopics2.append({
					'AccountId': pChildAccountId,
					'TopicArn': SNSTopics[x],
					'Region': region
				})
except ClientError as my_Error:
	print(my_Error)
	ProcessStatus['Step7']['Success']=False

"""
for i in range(len(GDinvites2)):
	logging.error(Fore.RED+"I found a GuardDuty invitation for account %s in region %s from account %s ", pChildAccountId, GDinvites2[i]['Region'], GDinvites2[i]['AccountId']+Fore.RESET)
	ProcessStatus['Step7']['IssuesFound']+=1
	ProcessStatus['Step7']['Success']=False
	if FixRun:
		for x in range(len(GDinvites2)):
			try:
				logging.warning("SNS Topic deletion commencing...")
				delresponse=Inventory_Modules.delete_gd_invites(account_credentials, region, GDinvites2[x]['AccountId'])
				ProcessStatus['Step7']['IssuesFixed']+=1
				# We assume the process worked. We should probably NOT assume this.
			except ClientError as my_Error:
				print(my_Error)

if ProcessStatus['Step7']['Success']:
	print(ERASE_LINE+Fore.GREEN+"** Step 7 completed with no issues"+Fore.RESET)
elif ProcessStatus['Step7']['IssuesFound']-ProcessStatus['Step7']['IssuesFixed']==0:
	print(ERASE_LINE+Fore.GREEN+"** Step 7 found {} SNS Topics, but they were deleted".format(ProcessStatus['Step7']['IssuesFound'])+Fore.RESET)
	ProcessStatus['Step7']['Success']=True
elif (ProcessStatus['Step7']['IssuesFound']>ProcessStatus['Step7']['IssuesFixed']):
	print(ERASE_LINE+Fore.RED+"** Step 7 completed, but there were {} SNS Topics found that couldn't be deleted".format(ProcessStatus['Step7']['IssuesFound']-ProcessStatus['Step7']['IssuesFixed'])+Fore.RESET)
else:
	print(ERASE_LINE+Fore.RED+"** Step 7 completed with blockers found"+Fore.RESET)
print()
"""
# Step 8
# Checking for Lambda functions

#Step 9
# Checking for Role names
try:
	print("Checking account {} for any Role names containing the 'controltower' string".format(pChildAccountId))
	RoleNames2=[]
	logging.error("Checking account %s in region %s for", pChildAccountId, region+Fore.RED+" Role names"+Fore.RESET)
	RoleNames=Inventory_Modules.find_role_names(account_credentials, 'us-east-1', ['controltower', 'ControlTower'])
	if len(RoleNames) > 0:
		for x in range(len(RoleNames)):
			logging.warning("Role Name: %s", str(RoleNames[x]))
			logging.error("Unfortunately, we've found a Role Name for account %s, which means we'll have to delete it before this account can be adopted.", pChildAccountId)
			ProcessStatus['Step9']['IssuesFound']+=1
			RoleNames2.append({
				'AccountId': pChildAccountId,
				'TopicArn': RoleNames[x]
			})
except ClientError as my_Error:
	print(my_Error)
	ProcessStatus['Step9']['Success']=False

"""
for i in range(len(GDinvites2)):
	logging.error(Fore.RED+"I found a GuardDuty invitation for account %s in region %s from account %s ", pChildAccountId, GDinvites2[i]['Region'], GDinvites2[i]['AccountId']+Fore.RESET)
	ProcessStatus['Step9']['IssuesFound']+=1
	ProcessStatus['Step9']['Success']=False
	if FixRun:
		for x in range(len(GDinvites2)):
			try:
				logging.warning("SNS Topic deletion commencing...")
				delresponse=Inventory_Modules.delete_gd_invites(account_credentials, region, GDinvites2[x]['AccountId'])
				ProcessStatus['Step9']['IssuesFixed']+=1
				# We assume the process worked. We should probably NOT assume this.
			except ClientError as my_Error:
				print(my_Error)

if ProcessStatus['Step9']['Success']:
	print(ERASE_LINE+Fore.GREEN+"** Step 9 completed with no issues"+Fore.RESET)
elif ProcessStatus['Step9']['IssuesFound']-ProcessStatus['Step9']['IssuesFixed']==0:
	print(ERASE_LINE+Fore.GREEN+"** Step 9 found {} SNS Topics, but they were deleted".format(ProcessStatus['Step9']['IssuesFound'])+Fore.RESET)
	ProcessStatus['Step9']['Success']=True
elif (ProcessStatus['Step9']['IssuesFound']>ProcessStatus['Step9']['IssuesFixed']):
	print(ERASE_LINE+Fore.RED+"** Step 9 completed, but there were {} SNS Topics found that couldn't be deleted".format(ProcessStatus['Step9']['IssuesFound']-ProcessStatus['Step9']['IssuesFixed'])+Fore.RESET)
else:
	print(ERASE_LINE+Fore.RED+"** Step 9 completed with blockers found"+Fore.RESET)
print()
"""

ChildIsReady=ProcessStatus['Step1']['Success'] and ProcessStatus['Step2']['Success'] and ProcessStatus['Step3']['Success'] and ProcessStatus['Step4']['Success'] and ProcessStatus['Step5']['Success']
NumberOfIssues=ProcessStatus['Step1']['IssuesFound'] + ProcessStatus['Step2']['IssuesFound'] + ProcessStatus['Step3']['IssuesFound'] + ProcessStatus['Step4']['IssuesFound'] + ProcessStatus['Step5']['IssuesFound']
NumberOfFixes=ProcessStatus['Step1']['IssuesFixed'] + ProcessStatus['Step2']['IssuesFixed'] + ProcessStatus['Step3']['IssuesFixed'] + ProcessStatus['Step4']['IssuesFixed'] + ProcessStatus['Step5']['IssuesFixed']
FixesWorked=(NumberOfIssues-NumberOfFixes==0)
if ChildIsReady and NumberOfIssues==0:
	print(Fore.GREEN+"**** We've found NO issues that would hinder the adoption of this account ****"+Fore.RESET)
elif ChildIsReady and FixesWorked:
	print(Fore.GREEN+"We've found and fixed"+Fore.RED, "{}".format(NumberOfFixes)+Fore.RESET, Fore.GREEN+"issues that would have otherwise blocked the adoption of this account"+Fore.RESET)
else:
	print(Fore.RED+"We've found {} issues that would hinder the adoption of this account".format(NumberOfIssues-NumberOfFixes)+Fore.RESET)

# pprint.pprint(ProcessStatus)
print()
print("Thanks for using this script...")
