#!/usr/bin/env python3

from pprint import pprint
import sys
import Inventory_Modules
from time import time
from colorama import init, Fore
from queue import Queue
from threading import Thread
from botocore.exceptions import ClientError
from prettytable import PrettyTable
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access

import logging

init()

parser = CommonArguments()
parser.verbosity()
parser.singleprofile()
parser.multiregion()
parser.extendedargs()
parser.my_parser.add_argument(
	"--explain",
	dest="pExplain",
	const=True,
	default=False,
	action="store_const",
	help="This flag prints out the explanation of what this script would do.")
parser.my_parser.add_argument(
	"-a", "--account",
	dest="pChildAccountId",
	metavar="New Account to be adopted into Control Tower",
	default=None,
	help="This is the account number of the account you're checking, to see if it can be adopted into AWS Control Tower.")
parser.my_parser.add_argument(
	"-q", "--quick",
	dest="Quick",
	metavar="Shortcut the checking to only a single region",
	const=True,
	default=False,
	action="store_const",
	help="This flag only checks 'us-east-1', so makes the whole script run really fast.")
parser.my_parser.add_argument(
	"+fix", "+delete",
	dest="FixRun",
	const=True,
	default=False,
	action="store_const",
	help="This will fix the issues found. If default VPCs must be deleted, you'll be asked to confirm.")
# TODO: There should be an additional parameter here that would take a role name for access into the account,
#  since it's likely that users won't be able to use the AWSControlTowerExecution role
# parser.my_parser.add_argument(
# 	"+force",
# 	dest="pVPCConfirm",
# 	const=True,
# 	default=False,
# 	action="store_const",
# 	help="This will remediate issues found with NO confirmation. You still have to specify the +fix too")
args = parser.my_parser.parse_args()

Quick = args.Quick
pProfile = args.Profile
pRegions = args.Regions
pSkipAccounts = args.SkipAccounts
pTiming = args.Time
verbose = args.loglevel
pChildAccountId = args.pChildAccountId
FixRun = args.FixRun
pExplain = args.pExplain
pVPCConfirm = args.Force
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")
# This is hard-coded, because this is the listing of regions that are supported by AWS Control Tower.
if Quick:
	RegionList = ['us-east-1']
else:
	# RegionList=Inventory_Modules.get_ec2_regions('all', pProfile)
	# ap-northeast-3 doesn't support Config (and therefore doesn't support Control Tower),
	# but is a region that is normally included within EC2. Therefore - this is easier.
	# Updated as of November 24, 2021 to the regions supported by AWS Control Tower.
	# So - the enroll OU feature doesn't only limit its checks to the regions supported by Control Tower,
	# which is why this script failed to prepare accounts before.
	# I've updated the list here, but we do need to replace this list with a dynamically generated one.
	RegionList = ['us-east-1', 'us-east-2', 'us-west-2', 'us-west-1',
				  'eu-central-1', 'eu-north-1', 'eu-west-1', 'eu-west-2', 'eu-west-3',
				  'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3', 'ap-south-1', 'ap-southeast-1', 'ap-southeast-2',
				  'ca-central-1', 'sa-east-1']
# TODO: 'ap-east-1' isn't included here, because it's an opt-in region, which we can't include if we haven't opted-in.
# TODO: This is a larger problem of Control Tower not publishing its regions via an API like other services do.

ERASE_LINE = '\x1b[2K'

ExplainMessage = """
Objective: This script aims to identify issues and make it easier to "adopt" an existing account into a Control Tower environment.

0. The targeted account MUST allow the Management account access into the Child IAM role called "AWSControlTowerExecution" or another coded role, so that we have access to do read-only operations (by default).
0a. There must be an "AWSControlTowerExecution" role present in the account so that StackSets can assume it and deploy stack instances. This role must trust the Organizations Management account or at least the necessary Lambda functions.
** TODO ** - update the JSON to be able to update the role to ensure it trusts the least privileged roles from management account, instead of the whole account.
0b. STS must be active in all regions checked. You can check from the Account Settings page in IAM. Since we're using STS to connect to the account from the Management, this requirement is checked by successfully completing step 0.

1. Previously - this was a default VPC check, but this is no longer needed.

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
** TODO ** - If the existing account will be a child account in the Organization, use the Account Factory and enter the appropriate email address.

6. The existing account can not be in any of the CT-managed Organizations OUs. By default, these OUs are Core and Applications, but the customer may have chosen different or additional OUs to manage by CT.
-- not yet implemented --

7. SNS topics name containing "ControlTower"
8. Lambda Functions name containing "ControlTower"
9. Role name containing "ControlTower"
Bucket created for AWS Config -- not yet implemented
SNS topic created for AWS Config -- not yet implemented
10. CloudWatch Log group containing "aws-controltower/CloudTrailLogs" -- not yet implemented --
"""

if pExplain:
	print(ExplainMessage)
	sys.exit("Exiting after Script Explanation...")

if pTiming:
	begin_time = time()

aws_acct = aws_acct_access(pProfile)

logging.info(f"Confirming that this profile {pProfile} represents a Management Account")

if aws_acct.AccountType.lower() == 'root' and pChildAccountId is None:
	# Creates a list of the account numbers in the Org.
	ChildAccountList = [d['AccountId'] for d in aws_acct.ChildAccounts]
	print(f"Since you didn't specify a specific account, we'll check all {len(aws_acct.ChildAccounts)} accounts in the Org.")
elif aws_acct.AccountType.lower() == 'root' and pChildAccountId is not None:
	print(f"Account {aws_acct.acct_number} is a {aws_acct.AccountType} account.\n"
		  f"We're specifically checking to validate that account {pChildAccountId} can be adopted into the Landing Zone")
	ChildAccountList = [pChildAccountId]
else:
	sys.exit(f"Account {aws_acct.acct_number} is a {aws_acct.AccountType} account.\n"
			 f" This script should be run with Management Account credentials.")

if not pSkipAccounts == []:
	for account_to_skip in pSkipAccounts:
		ChildAccountList.remove(account_to_skip)

print()

# Step 0 -
# 0. The Child account MUST allow the Management account access into the Child IAM role called "AWSControlTowerExecution"

if verbose < 50:
	print("This script does the following... ")
	print(f"{Fore.BLUE}  0.{Fore.RESET} Checks to ensure you have the necessary cross-account role access to the child account.")
	print(f"{Fore.BLUE}  1.{Fore.RESET} This check previously checked for default VPCs, but has since been removed.")
	print(f"{Fore.BLUE}  2.{Fore.RESET} Checks the child account in each of the regions")
	print(f"     to see if there's already a {Fore.RED}Config Recorder and Delivery Channel {Fore.RESET}enabled...")
	print(f"{Fore.BLUE}  3.{Fore.RESET} Checks that there isn't a duplicate {Fore.RED}CloudTrail{Fore.RESET} trail in the account.")
	print(f"{Fore.BLUE}  4.{Fore.RESET} This check previously checked for the presence of GuardDuty within this account, but has since been removed.")
	# print(Fore.BLUE+"  4."+Fore.RESET+" Checks to see if "+Fore.RED+"GuardDuty"+Fore.RESET+" has been enabled for this child account.")
	# print("     If it has been, it needs to be deleted before we can adopt this new account into the Control Tower Organization.")
	print(f"{Fore.BLUE}  5.{Fore.RESET} This child account {Fore.RED}must exist{Fore.RESET} within the Parent Organization.")
	print("     If it doesn't - then you must move it into this Org - this script can't do that for you.")
	print(f"{Fore.BLUE}  6.{Fore.RESET} The target account {Fore.RED}can't exist{Fore.RESET} within an already managed OU.")
	print("     If it does - then you're already managing this account with Control Tower and just don't know it.")
	print(f"{Fore.BLUE}  7.{Fore.RESET} Looking for {Fore.RED}SNS Topics{Fore.RESET} with duplicate names.")
	print("     If found, we can delete them, but you probably want to do that manually - to be sure.")
	print(f"{Fore.BLUE}  8.{Fore.RESET} Looking for {Fore.RED}Lambda Functions{Fore.RESET} with duplicate names.")
	print("     If found, we can delete them, but you probably want to do that manually - to be sure.")
	print(f"{Fore.BLUE}  9.{Fore.RESET} Looking for {Fore.RED}IAM Roles{Fore.RESET} with duplicate names.")
	print("     If found, we can delete them, but you probably want to do that manually - to be sure.")
	print(f"{Fore.BLUE}  10.{Fore.RESET} Looking for duplicate {Fore.RED}CloudWatch Log Groups.{Fore.RESET}")
	print("     If found, we can delete them, but you probably want to do that manually - to be sure.")
	print()
	print("Since this script is fairly new - All comments or suggestions are enthusiastically encouraged")
	print()


def DoAccountSteps(fChildAccountId, aws_account, fFixRun, fRegionList):
	def InitDict(StepCount):
		fProcessStatus = {}
		# fProcessStatus['ChildAccountIsReady']=True
		# fProcessStatus['IssuesFound']=0
		# fProcessStatus['IssuesFixed']=0
		for item in range(StepCount):
			Step = f"Step{str(item)}"
			fProcessStatus[Step] = {}
			fProcessStatus[Step]['Success'] = True
			fProcessStatus[Step]['IssuesFound'] = 0
			fProcessStatus[Step]['IssuesFixed'] = 0
			fProcessStatus[Step]['ProblemsFound'] = []
		return (fProcessStatus)

	NumOfSteps = 11

	# Step 0
	ProcessStatus = InitDict(NumOfSteps)
	Step = 'Step0'
	CTRoles = ['AWSControlTowerExecution', 'AWSCloudFormationStackSetExecutionRole', 'Owner']
	# TODO: I don't use this next variable, but eventually I intend to supply the JSON code needed to update a role with.
	json_formatted_str_TP = ""
	print(f"{Fore.BLUE}{Step}:{Fore.RESET}")
	print(f"Confirming we have the necessary cross-account access to account {fChildAccountId}")
	try:
		account_credentials = Inventory_Modules.get_child_access3(aws_account, fChildAccountId, 'us-east-1', CTRoles)
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			# TODO: This whole section is waiting on an enhancement. Until then, we have to assume that ProServe or someone familiar with Control Tower is running this script
			print(f"{aws_account.acct_number}: Authorization Failure for account {fChildAccountId}")
			print("The child account MUST allow access into the proper IAM role from the Organization's Management Account for the rest of this script (and the overall migration) to run.")
			print("You must add the following lines to the Trust Policy of that role in the child account")
			print(json_formatted_str_TP)
			print(my_Error)
			ProcessStatus[Step]['Success'] = False
			sys.exit("Exiting due to Authorization Failure...")
		elif str(my_Error).find("AccessDenied") > 0:
			# TODO: This whole section is waiting on an enhancement. Until then, we have to assume that ProServe or someone familiar with Control Tower is running this script
			print(f"{aws_account.acct_number}: Access Denied Failure for account {fChildAccountId}")
			print("The child account MUST allow access into the proper IAM role from the Organization's Management Account for the rest of this script (and the overall migration) to run.")
			print("You must add the following lines to the Trust Policy of that role in the child account")
			print(json_formatted_str_TP)
			print(my_Error)
			ProcessStatus[Step]['Success'] = False
			sys.exit("Exiting due to Access Denied Failure...")
		else:
			print(f"{aws_account.acct_number}: Other kind of failure for account {fChildAccountId}")
			print(my_Error)
			ProcessStatus[Step]['Success'] = False
			sys.exit("Exiting for other failure...")
	finally:
		if account_credentials['AccessError']:
			print(f"{Fore.RED}We weren't able to connect to the Child Account from this Management Account. Please check the role Trust Policy and re-run this script.{Fore.RESET}")
			print(f"The following list of roles were tried, but none were allowed access to account {fChildAccountId} using the {aws_account.acct_number} profile")
			print(Fore.RED, CTRoles, Fore.RESET)
			logging.debug(account_credentials)
			ProcessStatus[Step]['Success'] = False
			sys.exit("Exiting due to cross-account access failure")

	logging.info("Was able to successfully connect using the credentials... ")
	print()
	print(f"Confirmed the role {Fore.GREEN}{account_credentials['Role']}{Fore.RESET}"
		  f" exists in account {Fore.GREEN}{fChildAccountId}{Fore.RESET}"
		  f" and trusts {Fore.GREEN}our role{Fore.RESET} within the Management Account")
	print(f"{Fore.GREEN}** Step 0 completed without issues{Fore.RESET}")
	print()

	"""
	# Step 1 -- Obsoleted due to Control Tower no longer checking this --
	# This part will find and delete the Default VPCs in each region for the child account. We only delete if you provided that in the parameters list.
	
	If you're really interested in the code that used to be here - check out the "ALZ_CheckAccount.py" script; the code is still in there.
	
	"""

	# Step 2
	# This part will check the Config Recorder and  Delivery Channel. If they have one, we need to delete it, so we can create another. We'll ask whether this is ok before we delete.
	Step = 'Step2'
	try:
		# fRegionList=Inventory_Modules.get_service_regions('config', 'all')
		print(f"{Fore.BLUE}{Step}:{Fore.RESET}")
		print(f" Checking account {fChildAccountId} for a Config Recorders and Delivery Channels in any region")
		ConfigList = []
		DeliveryChanList = []
		"""
		TODO: Need to find a way to gracefully handle the error processing of opt-in regions.
			Until then - we're using a hard-coded listing of regions, instead of dynamically finding those.
		"""
		# fRegionList.remove('me-south-1')	# Opt-in region, which causes a failure if we check and it's not opted-in
		# fRegionList.remove('ap-east-1')	# Opt-in region, which causes a failure if we check and it's not opted-in
		for region in fRegionList:
			print(ERASE_LINE, f"Checking account {fChildAccountId} in region {region} for Config Recorder", end='\r')
			logging.info("Looking for Config Recorders in account %s from Region %s", fChildAccountId, region)
			ConfigRecorder = Inventory_Modules.find_config_recorders2(account_credentials, region)
			logging.debug("Tried to capture Config Recorder")
			if len(ConfigRecorder['ConfigurationRecorders']) > 0:
				ConfigList.append({
					'Name'     : ConfigRecorder['ConfigurationRecorders'][0]['name'],
					'roleARN'  : ConfigRecorder['ConfigurationRecorders'][0]['roleARN'],
					'AccountID': fChildAccountId,
					'Region'   : region
				})
			print(f"{ERASE_LINE}Checking account {fChildAccountId} in region {region} for Delivery Channel", end='\r')
			DeliveryChannel = Inventory_Modules.find_delivery_channels2(account_credentials, region)
			logging.debug("Tried to capture Delivery Channel")
			if len(DeliveryChannel['DeliveryChannels']) > 0:
				DeliveryChanList.append({
					'Name'     : DeliveryChannel['DeliveryChannels'][0]['name'],
					'AccountID': fChildAccountId,
					'Region'   : region
				})
		logging.warning(f"Checked account {fChildAccountId} in {len(fRegionList)} regions. Found {len(ConfigList) + len(DeliveryChanList)} issues with Config Recorders and Delivery Channels")
	except ClientError as my_Error:
		logging.warning("Failed to capture Config Recorder and Delivery Channels")
		ProcessStatus[Step]['Success'] = False
		print(my_Error)

	for _ in range(len(ConfigList)):
		logging.warning(f"{Fore.RED}Found a config recorder for account %s in region %s", ConfigList[_]['AccountID'], ConfigList[_]['Region'] + Fore.RESET)
		ProcessStatus[Step]['Success'] = False
		ProcessStatus[Step]['IssuesFound'] += 1
		ProcessStatus[Step]['ProblemsFound'].extend(ConfigList)
		if fFixRun:
			logging.warning("Deleting %s in account %s in region %s", ConfigList[_]['Name'], ConfigList[_]['AccountID'], ConfigList[_]['Region'])
			DelConfigRecorder = Inventory_Modules.del_config_recorder2(account_credentials, ConfigList[_]['Region'], ConfigList[_]['Name'])
			# We assume the process worked. We should probably NOT assume this.
			ProcessStatus[Step]['IssuesFixed'] += 1
	for _ in range(len(DeliveryChanList)):
		logging.warning(f"{Fore.RED}Found a delivery channel for account {DeliveryChanList[_]['AccountID']} in region {DeliveryChanList[_]['Region']}{Fore.RESET}")
		ProcessStatus[Step]['Success'] = False
		ProcessStatus[Step]['IssuesFound'] += 1
		ProcessStatus[Step]['ProblemsFound'].extend(DeliveryChanList)
		if fFixRun:
			logging.warning("Deleting %s in account %s in region %s", DeliveryChanList[_]['Name'], DeliveryChanList[_]['AccountID'], DeliveryChanList[_]['Region'])
			DelDeliveryChannel = Inventory_Modules.del_delivery_channel2(account_credentials, DeliveryChanList[_]['Region'], DeliveryChanList[_]['Name'])
			# We assume the process worked. We should probably NOT assume this.
			ProcessStatus[Step]['IssuesFixed'] += 1

	if ProcessStatus[Step]['Success']:
		print(f"{ERASE_LINE + Fore.GREEN}** Step 2 completed with no issues{Fore.RESET}")
	elif ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed'] == 0:
		print(f"{ERASE_LINE + Fore.GREEN}** Step 2 found {ProcessStatus[Step]['IssuesFound']} issues, but they were fixed by deleting the existing Config Recorders and Delivery Channels{Fore.RESET}")
		ProcessStatus[Step]['Success'] = True
	elif ProcessStatus[Step]['IssuesFound'] > ProcessStatus[Step]['IssuesFixed']:
		print(f"{ERASE_LINE + Fore.RED}** Step 2 completed, but there were {ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed']} items found that weren't deleted{Fore.RESET}")
	else:
		print(f"{ERASE_LINE + Fore.RED}** Step 2 completed with blockers found{Fore.RESET}")
	print()

	# Step 3
	# 3. The account must not have a Cloudtrail Trail name the same name as the CT Trail ("AWS-Landing-Zone-BaselineCloudTrail")
	Step = 'Step3'
	try:
		print(f"{Fore.BLUE}{Step}:{Fore.RESET}")
		print(f" Checking account {fChildAccountId} for a specially named CloudTrail in all regions")
		CTtrails2 = []
		for region in fRegionList:
			print(ERASE_LINE, f"Checking account {fChildAccountId} in region {region} for CloudTrail trails", end='\r')
			CTtrails = Inventory_Modules.find_cloudtrails2(account_credentials, region, ['aws-controltower-BaselineCloudTrail'])
			if len(CTtrails) > 0:
				logging.warning(f"Unfortunately, we've found a CloudTrail log named {CTtrails[0]['Name']} in account {fChildAccountId} "
								f"in the {region} region, which means we'll have to delete it before this account can be adopted.")
				CTtrails2.append(CTtrails[0])
				ProcessStatus[Step]['Success'] = False
	except ClientError as my_Error:
		print(my_Error)
		ProcessStatus[Step]['Success'] = False

	for _ in range(len(CTtrails2)):
		logging.warning(f"{Fore.RED}Found a CloudTrail trail for account {fChildAccountId} in region {CTtrails2[_]['HomeRegion']} named {CTtrails2[_]['Name']}{Fore.RESET}")
		ProcessStatus[Step]['IssuesFound'] += 1
		ProcessStatus[Step]['ProblemsFound'].extend(CTtrails2)
		if fFixRun:
			try:
				logging.warning("CloudTrail trail deletion commencing...")
				delresponse = Inventory_Modules.del_cloudtrails2(account_credentials, region, CTtrails2[_]['TrailARN'])
				ProcessStatus[Step]['IssuesFixed'] += 1
			except ClientError as my_Error:
				print(my_Error)

	if ProcessStatus[Step]['Success']:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} completed with no issues{Fore.RESET}")
	elif ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed'] == 0:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} found {ProcessStatus[Step]['IssuesFound']} issues, but they were fixed by deleting the existing CloudTrail trail names{Fore.RESET}")
		ProcessStatus[Step]['Success'] = True
	elif ProcessStatus[Step]['IssuesFound'] > ProcessStatus[Step]['IssuesFixed']:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed, but there were {ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed']} trail names found that wasn't deleted{Fore.RESET}")
	else:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed with blockers found{Fore.RESET}")
	print()

	""" Step 4
	# Step 4 -- The lack of or use of GuardDuty isn't a pre-requisite for Control Tower --
	# 4. This section checks for a pending guard duty invite. You can also check from the Guard Duty Console
	Step='Step4'
	try:
		print(Fore.BLUE + "{}:".format(Step) + Fore.RESET)
		print(" Checking account {} for any GuardDuty invites".format(fChildAccountId))
		GDinvites2=[]
		for region in fRegionList:
			logging.warning("Checking account %s in region %s for", fChildAccountId, region+Fore.RED+" GuardDuty"+Fore.RESET+" invitations")
			logging.warning("Checking account %s in region %s for GuardDuty invites", fChildAccountId, region)
			GDinvites=Inventory_Modules.find_gd_invites(account_credentials, region)
			if len(GDinvites) > 0:
				for x in range(len(GDinvites['Invitations'])):
					logging.warning("GD Invite: %s", str(GDinvites['Invitations'][x]))
					logging.warning("Unfortunately, we've found a GuardDuty invitation for account %s in the %s region from account %s, which means we'll have to delete it before this account can be adopted.", fChildAccountId, region, GDinvites['Invitations'][x]['AccountId'])
					ProcessStatus[Step]['IssuesFound']+=1
					GDinvites2.append({
						'AccountId': GDinvites['Invitations'][x]['AccountId'],
						'InvitationId': GDinvites['Invitations'][x]['InvitationId'],
						'Region': region
					})
	except ClientError as my_Error:
		print(my_Error)
		ProcessStatus[Step]['Success']=False
	
	for i in range(len(GDinvites2)):
		logging.warning(Fore.RED+"I found a GuardDuty invitation for account %s in region %s from account %s ", fChildAccountId, GDinvites2[i]['Region'], GDinvites2[i]['AccountId']+Fore.RESET)
		ProcessStatus[Step]['IssuesFound']+=1
		ProcessStatus[Step]['Success']=False
		if fFixRun:
			for x in range(len(GDinvites2)):
				try:
					logging.warning("GuardDuty invite deletion commencing...")
					delresponse=Inventory_Modules.delete_gd_invites(account_credentials, region, GDinvites2[x]['AccountId'])
					ProcessStatus[Step]['IssuesFixed']+=1
					# We assume the process worked. We should probably NOT assume this.
				except ClientError as my_Error:
					print(my_Error)
	
	if ProcessStatus[Step]['Success']:
		print(ERASE_LINE+Fore.GREEN+"** {} completed with no issues".format(Step)+Fore.RESET)
	elif ProcessStatus[Step]['IssuesFound']-ProcessStatus[Step]['IssuesFixed']==0:
		print(ERASE_LINE+Fore.GREEN+"** {} found {} guardduty invites, but they were deleted".format(Step,ProcessStatus[Step]['IssuesFound'])+Fore.RESET)
		ProcessStatus[Step]['Success']=True
	elif (ProcessStatus[Step]['IssuesFound']>ProcessStatus[Step]['IssuesFixed']):
		print(ERASE_LINE+Fore.RED+"** {} completed, but there were {} guardduty invites found that couldn't be deleted".format(Step,ProcessStatus[Step]['IssuesFound']-ProcessStatus[Step]['IssuesFixed'])+Fore.RESET)
	else:
		print(ERASE_LINE+Fore.RED+"** {} completed with blockers found".format(Step)+Fore.RESET)
	print()
	"""

	# Step 4a
	# 4a. STS must be active in all regions. You can check from the Account Settings page in IAM.
	"""
	TODO
	
	We would have already verified this - since we've used STS to connect to each region already for the previous steps.
	- Except for the "quick" shortcut - which means we probably need to point that out in this section. 
	"""

	# Step 5
	'''
	5. The account must be part of the Organization and the email address being entered into the CT parameters must match the account. If 	you try to add an email from an account which is not part of the Org, you will get an error that you are not using a unique email address. If it’s part of the Org, CT just finds the account and uses the CFN roles.
	- If the existing account is to be imported as a Core Account, modify the manifest.yaml file to use it.
	- If the existing account will be a child account in the Organization, use the AVM launch template through Service Catalog and enter the appropriate configuration parameters.
	'''
	# try:
	Step = 'Step5'
	print(f"{Fore.BLUE}{Step}:{Fore.RESET}")
	print(" Checking that the account is part of the AWS Organization.")
	OrgAccountList = [d['AccountId'] for d in aws_account.ChildAccounts]
	if not (fChildAccountId in OrgAccountList):
		print()
		print(f"Account # {fChildAccountId} is not a part of the Organization. This account needs to be moved into the Organization to be adopted into the Landing Zone tool")
		print("This is easiest done manually right now.")
		ProcessStatus[Step]['Success'] = False
		ProcessStatus[Step]['IssuesFound'] += 1

	if ProcessStatus[Step]['Success']:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} completed with no issues{Fore.RESET}")
	elif ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed'] == 0:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} found {ProcessStatus[Step]['IssuesFound']} issue, but we were able to fix it{Fore.RESET}")
		ProcessStatus[Step]['Success'] = True
	elif ProcessStatus[Step]['IssuesFound'] > ProcessStatus[Step]['IssuesFixed']:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed, but there was {ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed']} blocker found that wasn't fixed{Fore.RESET}")
	else:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed with blockers found{Fore.RESET}")
	print()

	# Step 6
	# 6. The existing account can not be in any of the CT-managed Organizations OUs. By default, these OUs are Core and Applications, but the customer may have chosen different or additional OUs to manage by CT.
	"""
	So we'll need to verify that the parent OU of the account is the root of the organization.
	
	TODO Here
	"""
	Step = 'Step6'
	try:
		print(f"{Fore.BLUE}{Step}:{Fore.RESET}")
		print(f" Checking account {fChildAccountId} to make sure it's not already in a Control-Tower managed OU")
		print(" -- Not yet implemented -- ")
	except ClientError as my_Error:
		print(my_Error)
		ProcessStatus[Step]['Success'] = False
	print()

	# Step 7 - Check for other resources which have 'controltower' in the name
	# Checking for SNS Topics
	Step = 'Step7'
	try:
		print(f"{Fore.BLUE}{Step}:{Fore.RESET}")
		print(f" Checking account {fChildAccountId} for any SNS topics containing the 'controltower' string")
		SNSTopics2 = []
		for region in fRegionList:
			logging.warning("Checking account %s in region %s for", fChildAccountId, f"{region + Fore.RED} SNS Topics{Fore.RESET}")
			print(ERASE_LINE, f"Checking account {fChildAccountId} in region {region} for SNS Topics", end='\r')
			SNSTopics = Inventory_Modules.find_sns_topics2(account_credentials, region, ['controltower', 'ControlTower'])
			if len(SNSTopics) > 0:
				for x in range(len(SNSTopics)):
					logging.warning("SNS Topic: %s", str(SNSTopics[x]))
					logging.info("Unfortunately, we've found an SNS Topic  for account %s in the %s region, which means we'll have to delete it before this account can be adopted.", fChildAccountId, region)
					ProcessStatus[Step]['Success'] = False
					ProcessStatus[Step]['IssuesFound'] += 1
					SNSTopics2.append({
						'AccountId': fChildAccountId,
						'TopicArn' : SNSTopics[x],
						'Region'   : region
					})
					ProcessStatus[Step]['ProblemsFound'].extend(SNSTopics2)
	except ClientError as my_Error:
		print(my_Error)
		ProcessStatus[Step]['Success'] = False

	if ProcessStatus[Step]['Success']:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} completed with no issues{Fore.RESET}")
	elif ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed'] == 0:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} found {ProcessStatus[Step]['IssuesFound']} issues, but we were able to remove the offending SNS Topics{Fore.RESET}")
		ProcessStatus[Step]['Success'] = True
	elif ProcessStatus[Step]['IssuesFound'] > ProcessStatus[Step]['IssuesFixed']:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed, but there were {ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed']} blockers found that wasn't fixed{Fore.RESET}")
	else:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed with blockers found{Fore.RESET}")
	print()

	# Step 8
	# Checking for Lambda functions
	Step = 'Step8'
	try:
		print(f"{Fore.BLUE}{Step}:{Fore.RESET}")
		print(f" Checking account {fChildAccountId} for any Lambda functions containing the 'controltower' string")
		LambdaFunctions2 = []
		for region in fRegionList:
			logging.warning(f"Checking account %s in region %s for {Fore.RED}Lambda functions{Fore.RESET}", fChildAccountId, region)
			print(ERASE_LINE, f"Checking account {fChildAccountId} in region {region} for Lambda Functions", end='\r')
			LambdaFunctions = Inventory_Modules.find_lambda_functions2(account_credentials, region, ['controltower', 'CpntrolTower'])
			if len(LambdaFunctions) > 0:
				logging.info(
					"Unfortunately, account %s contains %s functions with reserved names, which means we'll have to delete them before this account can be adopted.", fChildAccountId, len(LambdaFunctions))
				for x in range(len(LambdaFunctions)):
					logging.warning("Found Lambda function %s in region %s", LambdaFunctions[x]['FunctionName'], region)
					ProcessStatus[Step]['Success'] = False
					ProcessStatus[Step]['IssuesFound'] += 1
					LambdaFunctions2.append({
						'AccountId'   : fChildAccountId,
						'FunctionName': LambdaFunctions[x]['FunctionName'],
						'FunctionArn' : LambdaFunctions[x]['FunctionArn'],
						'Role'        : LambdaFunctions[x]['Role'],
						'Region'      : region
					})
					ProcessStatus[Step]['ProblemsFound'].extend(LambdaFunctions2)
	except ClientError as my_Error:
		print(my_Error)
		ProcessStatus[Step]['Success'] = False

	if ProcessStatus[Step]['Success']:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} completed with no issues{Fore.RESET}")
	elif ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed'] == 0:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} found {ProcessStatus[Step]['IssuesFound']} issues, but we were able to remove the offending Lambda Functions{Fore.RESET}")
		ProcessStatus[Step]['Success'] = True
	elif ProcessStatus[Step]['IssuesFound'] > ProcessStatus[Step]['IssuesFixed']:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed, but there were {ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed']} blockers found that wasn't fixed{Fore.RESET}")
	else:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed with blockers found{Fore.RESET}")
	print()

	# Step 9
	# Checking for Role names
	Step = 'Step9'
	try:
		print(f"{Fore.BLUE}{Step}:{Fore.RESET}")
		print(f" Checking account {fChildAccountId} for any Role names containing the 'controltower' string")
		RoleNames2 = []
		logging.warning("Checking account %s for", f"{fChildAccountId + Fore.RED} Role names{Fore.RESET}")
		RoleNames = Inventory_Modules.find_role_names2(account_credentials, 'us-east-1', ['controltower', 'ControlTower'])
		if len(RoleNames) > 0:
			logging.info(f"Unfortunately, account {fChildAccountId} contains {len(RoleNames)} roles with reserved names,"
						 f" which means we'll have to delete them before this account can be adopted.")
			for x in range(len(RoleNames)):
				logging.warning(f"Role Name: {str(RoleNames[x])}")
				ProcessStatus[Step]['Success'] = False
				ProcessStatus[Step]['IssuesFound'] += 1
				RoleNames2.append({
					'AccountId': fChildAccountId,
					'RoleName' : RoleNames[x]
				})
			ProcessStatus[Step]['ProblemsFound'].extend(RoleNames2)
	except ClientError as my_Error:
		print(my_Error)
		ProcessStatus[Step]['Success'] = False

	if ProcessStatus[Step]['Success']:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} completed with no issues{Fore.RESET}")
	elif ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed'] == 0:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} found {ProcessStatus[Step]['IssuesFound']} issues, but we were able to remove the offending IAM roles{Fore.RESET}")
		ProcessStatus[Step]['Success'] = True
	elif ProcessStatus[Step]['IssuesFound'] > ProcessStatus[Step]['IssuesFixed']:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed, but there were {ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed']} blockers found that remain to be fixed{Fore.RESET}")
	else:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed with blockers found{Fore.RESET}")
	print()

	# Step 10
	# 10. The existing account can not have any CloudWatch Log Groups named "controltower"
	"""
	So we'll need to find and remove the CloudWatch Log Groups - if there are any.

	TODO Here
	"""
	Step = 'Step10'
	try:
		print(f"{Fore.BLUE}{Step}:{Fore.RESET}")
		print(f"Checking account {fChildAccountId} to make sure there are no duplicate CloudWatch Log Groups")
		LogGroupNames2 = []
		for region in fRegionList:
			logging.warning(f"Checking account {fChildAccountId} for {Fore.RED}duplicate CloudWatch Log Group names{Fore.RESET}")
			LogGroupNames = Inventory_Modules.find_cw_log_group_names2(account_credentials, region, ['controltower', 'ControlTower'])
			if len(LogGroupNames) > 0:
				logging.info(f"Unfortunately, account {fChildAccountId} contains {len(LogGroupNames)} log groups with reserved names,"
							 f" which means we'll have to delete them before this account can be adopted.")
				for _ in range(len(LogGroupNames)):
					logging.warning(f"Log Group Name: {str(LogGroupNames[_])}")
					ProcessStatus[Step]['Success'] = False
					ProcessStatus[Step]['IssuesFound'] += 1
					LogGroupNames2.append({
						'AccountId'   : fChildAccountId,
						'LogGroupName': LogGroupNames[_]
					})
				ProcessStatus[Step]['ProblemsFound'].extend(LogGroupNames2)
	except ClientError as my_Error:
		print(my_Error)
		ProcessStatus[Step]['Success'] = False

	if ProcessStatus[Step]['Success']:
		print(f"{ERASE_LINE + Fore.GREEN}** {Step} completed with no issues{Fore.RESET}")
	elif ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed'] == 0:
		print(f"{ERASE_LINE}{Fore.GREEN}** {Step} found {ProcessStatus[Step]['IssuesFound']} issues, but we were able to remove the offending CW Log groups{Fore.RESET}")
		ProcessStatus[Step]['Success'] = True
	elif ProcessStatus[Step]['IssuesFound'] > ProcessStatus[Step]['IssuesFixed']:
		print(f"{ERASE_LINE}{Fore.RED}** {Step} completed, but there were {ProcessStatus[Step]['IssuesFound'] - ProcessStatus[Step]['IssuesFixed']} blockers found that remain to be fixed {Fore.RESET}")
	else:
		print(f"{ERASE_LINE + Fore.RED}** {Step} completed with blockers found{Fore.RESET}")
	print()

	""" Function Summary """
	TotalIssuesFound = 0
	TotalIssuesFixed = 0
	MemberReady = True
	for item in ProcessStatus:
		TotalIssuesFound = TotalIssuesFound + ProcessStatus[item]['IssuesFound']
		TotalIssuesFixed = TotalIssuesFixed + ProcessStatus[item]['IssuesFixed']
		MemberReady = MemberReady and ProcessStatus[item]['Success']

	ProcessStatus['AccountId'] = fChildAccountId
	ProcessStatus['Ready'] = MemberReady
	ProcessStatus['IssuesFound'] = TotalIssuesFound
	ProcessStatus['IssuesFixed'] = TotalIssuesFixed
	return (ProcessStatus)


####
# Summary at the end
####


Results = []
OrgResults = []
for MemberAccount in ChildAccountList:
	Results = DoAccountSteps(MemberAccount, aws_acct, FixRun, RegionList)
	OrgResults.append(Results.copy())

for MemberAccount in pSkipAccounts:
	OrgResults.append({'AccountId'  : MemberAccount, 'IssuesFound': 'N/A',
					   'IssuesFixed': 'N/A', 'Ready': 'Skipped'})

print()
x = PrettyTable()
y = PrettyTable()

x.field_names = ['Account', 'Issues Found', 'Issues Fixed', 'Ready?']
# The following headers represent Step0, Step2,
y.field_names = ['Account', 'Account Access', 'Config', 'CloudTrail', 'GuardDuty', 'Org Member', 'CT OU', 'SNS Topics', 'Lambda', 'Roles', 'CW Log Groups', 'Ready?']
for i in OrgResults:
	if i['AccountId'] in pSkipAccounts:
		x.add_row([i['AccountId'], i['IssuesFound'], i['IssuesFixed'], i['Ready']])
		y.add_row([i['AccountId'],
				   'N/A', 'N/A', 'N/A', 'N/A',
				   'N/A', 'N/A', 'N/A', 'N/A',
				   'N/A', 'N/A', 'Skipped'])
	else:
		x.add_row([i['AccountId'], i['IssuesFound'], i['IssuesFixed'], i['Ready']])
		y.add_row([
			i['AccountId'],
			i['Step0']['IssuesFound'] - i['Step0']['IssuesFixed'],
			i['Step2']['IssuesFound'] - i['Step2']['IssuesFixed'],
			i['Step3']['IssuesFound'] - i['Step3']['IssuesFixed'],
			i['Step4']['IssuesFound'] - i['Step4']['IssuesFixed'],
			i['Step5']['IssuesFound'] - i['Step5']['IssuesFixed'],
			i['Step6']['IssuesFound'] - i['Step6']['IssuesFixed'],
			i['Step7']['IssuesFound'] - i['Step7']['IssuesFixed'],
			i['Step8']['IssuesFound'] - i['Step8']['IssuesFixed'],
			i['Step9']['IssuesFound'] - i['Step9']['IssuesFixed'],
			i['Step10']['IssuesFound'] - i['Step10']['IssuesFixed'],
			i['Step0']['Success'] and i['Step2']['Success'] and i['Step3']['Success'] and i['Step4']['Success'] and i['Step5']['Success'] and i['Step6']['Success'] and i['Step7']['Success'] and i['Step8']['Success'] and i['Step9']['Success'] and i['Step10']['Success']
		])
print("The following table represents the accounts looked at, and whether they are ready to be incorporated into a Control Tower environment.")
print(x)
print()
print("The following table represents the accounts looked at, and gives details under each type of issue as to what might prevent a successful migration of this account into a Control Tower environment.")
print(y)

if verbose < 50:
	for account in OrgResults:
		print()
		FixesWorked = (account['IssuesFound'] - account['IssuesFixed'] == 0)
		if account['Ready'] and account['IssuesFound'] == 0:
			print(f"{Fore.GREEN}**** We've found NO issues that would hinder the adoption of account {account['AccountId']} ****{Fore.RESET}")
		elif account['Ready'] and FixesWorked:
			print(f"{Fore.GREEN}We've found and fixed{Fore.RED}", f"{account['IssuesFixed']}{Fore.RESET}", f"{Fore.GREEN}issues that would have otherwise blocked the adoption of account {account['AccountId']}{Fore.RESET}")
		else:
			print(f"{Fore.RED}Account # {account['AccountId']} has {account['IssuesFound'] - account['IssuesFixed']} issues that would hinder the adoption of this account{Fore.RESET}")
		for step in account:
			if step[:4] == 'Step' and len(account[step]['ProblemsFound']) > 0:
				print(f"{Fore.LIGHTRED_EX}Issues Found for {step} in account {account['AccountId']}:{Fore.RESET}")
				pprint(account[step]['ProblemsFound'])

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time} seconds{Fore.RESET}")
print("Thanks for using this script...")
print()
