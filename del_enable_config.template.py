#!/usr/local/bin/python3

import os, sys, pprint
import Inventory_Modules, boto3
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from urllib3.exceptions import NewConnectionError

import logging

init()

"""
TODO:
- This script simply finds those resources created by the "enable-config.template" cloudformation stack within Landing Zone and optionally deletes them
"""
# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(
	description="We\'re going to find all relevant resources within your child accounts.",
	prefix_chars='-+/')
parser.add_argument( # Profile
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	help="You need to specify a profile that represents the ROOT account.")
parser.add_argument( # Regions
	"-r","--region",
	dest="pRegions",
	nargs="*",
	metavar="Regions to look in",
	default=['us-east-1'],
	help="These are the regions you want to look through.")
parser.add_argument( # Admin Role Name
	"-a","--adminrolename",
	dest="pAdminRoleName",
	metavar="Admin Role Name",
	default='AWSCloudFormationStackSetExecutionRole',
	help="This is the role in the children that the script assumes.")
parser.add_argument( # Accounts to Skip
	"-k","--skip",
	dest="pSkipAccounts",
	nargs="*",
	metavar="Accounts to leave alone",
	default=[],
	help="These are the account numbers you don't want to screw with. Provide a space delimited list")
parser.add_argument( # Delete
	"+delete", "+forreal",
	dest="flagDelete",
	default=False,
	action="store_const",
	const=True,
	help="Whether to delete the configuration recorders and delivery channels it finds.")
parser.add_argument( # Force
	'-f', '--force',
	help="force deletion without asking first",
	action="store_const",
	dest="ForceDelete",
	const=True,
	default=False)
parser.add_argument( # args.loglevel = 10
	'-dd', '--debug',
	help="Print lots of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,
	default=logging.CRITICAL)
parser.add_argument( # args.loglevel = 20
	'-d',
	help="Print debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,
	default=logging.CRITICAL)
parser.add_argument( # args.loglevel = 30
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,
	default=logging.CRITICAL)
parser.add_argument( # args.loglevel = 40
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,
	default=logging.CRITICAL)
args = parser.parse_args()

pProfile=args.pProfile
adminrolename=args.pAdminRoleName
DeletionRun=args.flagDelete
ForceDelete=args.ForceDelete
AccountsToSkip=args.pSkipAccounts
pRegions=args.pRegions
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'

NumObjectsFound = 0
NumAccountsInvestigated = 0
adminrolename='AWSCloudFormationStackSetExecutionRole'
ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
ChildAccounts=Inventory_Modules.RemoveCoreAccounts(ChildAccounts,AccountsToSkip)

# pprint.pprint(ChildAccounts)
# sys.exit(99)
cfg_regions=Inventory_Modules.get_service_regions('config',pRegions)

all_config_resources=[]
all_config_resources=[]
print("Searching {} accounts and {} regions".format(len(ChildAccounts),len(cfg_regions)))

sts_session = boto3.Session(profile_name=pProfile)
sts_client = sts_session.client('sts')
for account in ChildAccounts:
	role_arn = "arn:aws:iam::{}:role/{}".format(account['AccountId'],adminrolename)
	logging.info("Role ARN: %s" % role_arn)
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-Enable-Config-Resources")['Credentials']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(profile+": Authorization Failure for account {}".format(account['AccountId']))
	for region in cfg_regions:
		NumAccountsInvestigated += 1
		session_aws=boto3.Session(
			aws_access_key_id=account_credentials['AccessKeyId'],
			aws_secret_access_key=account_credentials['SecretAccessKey'],
			aws_session_token=account_credentials['SessionToken'],
			region_name=region)
		client_cfg=session_aws.client('config')
		client_sns=session_aws.client('sns')
		client_lam=session_aws.client('lambda')
		client_cwl=session_aws.client('logs')
		## List Configuration_Recorders
		print(ERASE_LINE,"Trying account {} in region {}".format(account['AccountId'],region),end='\r')
		try: # Looking for Configuration Recorders
			response=client_cfg.describe_configuration_recorders()
			logging.error("Successfully described config recorders")
			if 'ConfigurationRecorders' in response.keys():
				for i in range(len(response['ConfigurationRecorders'])):
					NumObjectsFound=NumObjectsFound + len(response['ConfigurationRecorders'])
					all_config_resources.append({
						'Type': 'Config Recorder',
						'AccountId':account['AccountId'],
						'Region':region,
						'ResourceName':response['ConfigurationRecorders'][i]['name'],
						'AccessKeyId':account_credentials['AccessKeyId'],
						'SecretAccessKey':account_credentials['SecretAccessKey'],
						'SessionToken':account_credentials['SessionToken']
					})
					logging.info("Found another config recorder %s in account %s in region %s bringing the total found to %s ", str(response['ConfigurationRecorders'][i]['name']), account['AccountId'], region, str(NumObjectsFound))
			else:
				print(ERASE_LINE,Fore.RED+"No luck in account: {} in region {}".format(account['AccountId'],region)+Fore.RESET,end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure for account {}".format(account['AccountId']))
			response={}
		try: # Looking for Delivery Channels
			response=client_cfg.describe_delivery_channels()
			if len(response['DeliveryChannels']) > 0 and response['DeliveryChannels'][0]['name'][-13:] != "DO-NOT-DELETE":
				NumObjectsFound=NumObjectsFound + len(response['DeliveryChannels'])
				all_config_resources.append({
					'Type': 'Delivery Channel',
					'AccountId':account['AccountId'],
					'Region':region,
					'ResourceName':response['DeliveryChannels'][0]['name'],
					'AccessKeyId':account_credentials['AccessKeyId'],
					'SecretAccessKey':account_credentials['SecretAccessKey'],
					'SessionToken':account_credentials['SessionToken']
				})
				logging.info("Found another delivery channel %s in account %s in region %s bringing the total found to %s ", str(response['DeliveryChannels'][i]['name']), account['AccountId'], region, str(NumObjectsFound))
			else:
				print(ERASE_LINE,Fore.RED+"No luck in account: {} in region {}".format(account['AccountId'],region)+Fore.RESET,end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure for account {}".format(account['AccountId']))
		try: # Looking for SNS Topics
			response=client_sns.list_topics()
			if len(response['Topics']) > 0:
				for i in range(len(response['Topics'])):
					if "AWS-Landing-Zone-Security-Notification" in response['Topics'][i]['TopicArn']:
						NumObjectsFound+=1
						all_config_resources.append({
							'Type': 'SNS Topic',
							'AccountId':account['AccountId'],
							'Region':region,
							'ResourceName':response['Topics'][i]['TopicArn'],
							'AccessKeyId':account_credentials['AccessKeyId'],
							'SecretAccessKey':account_credentials['SecretAccessKey'],
							'SessionToken':account_credentials['SessionToken']
						})
						logging.info("Found another SNS Topic Arn %s in account %s in region %s bringing the total resources found to %s ", str(response['Topics'][i]['TopicArn']), account['AccountId'], region, str(NumObjectsFound))
			else:
				print(ERASE_LINE,Fore.RED+"No luck in account: {} in region {}".format(account['AccountId'],region)+Fore.RESET,end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure for account {}".format(account['AccountId']))
		try: # Looking for Lambda Function
			response=client_lam.list_functions()
			if len(response['Functions']) > 0:
				for i in range(len(response['Functions'])):
					if "LandingZoneLocalSNSNotificationForwarder" in response['Functions'][i]['FunctionName']:
						NumObjectsFound+=1
						all_config_resources.append({
							'Type': 'Lambda Function',
							'AccountId':account['AccountId'],
							'Region':region,
							'ResourceName':response['Functions'][i]['FunctionName'],
							'AccessKeyId':account_credentials['AccessKeyId'],
							'SecretAccessKey':account_credentials['SecretAccessKey'],
							'SessionToken':account_credentials['SessionToken']
						})
						logging.info("Found another Lambda Function %s in account %s in region %s bringing the total resources found to %s ", str(response['Functions'][i]['FunctionName']), account['AccountId'], region, str(NumObjectsFound))
			else:
				print(ERASE_LINE,Fore.RED+"No luck in account: {} in region {}".format(account['AccountId'],region)+Fore.RESET,end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure for account {}".format(account['AccountId']))
		try: # Looking for CloudWatch Log Group
			response=client_cwl.describe_log_groups()
			if len(response['logGroups']) > 0:
				for i in range(len(response['logGroups'])):
					if "LandingZoneLocalSNSNotificationForwarder" in response['logGroups'][i]['logGroupName']:
						NumObjectsFound+=1
						all_config_resources.append({
							'Type': 'Log Group',
							'AccountId':account['AccountId'],
							'Region':region,
							'ResourceName':response['logGroups'][i]['logGroupName'],
							'AccessKeyId':account_credentials['AccessKeyId'],
							'SecretAccessKey':account_credentials['SecretAccessKey'],
							'SessionToken':account_credentials['SessionToken']
						})
						logging.info("Found another SNS Topic Arn %s in account %s in region %s bringing the total resources found to %s ", str(response['logGroups'][i]['logGroupName']), account['AccountId'], region, str(NumObjectsFound))
			else:
				print(ERASE_LINE,Fore.RED+"No luck in account: {} in region {}".format(account['AccountId'],region)+Fore.RESET,end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure for account {}".format(account['AccountId']))
	NumAccountsInvestigated += 1
	print(ERASE_LINE+Fore.GREEN+"Checked {} Accounts. Only {} left to go...".format(NumAccountsInvestigated,len(ChildAccounts)-NumAccountsInvestigated),Fore.RESET)
print()
fmt='%-20s %-15s %-20s %-20s'
print(fmt % ("Account ID","Region","Type","Resource Name"))
print(fmt % ("----------","------","-----","----------------"))
for i in range(len(all_config_resources)):
	print(fmt % (all_config_resources[i]['AccountId'],all_config_resources[i]['Region'],all_config_resources[i]['Type'],all_config_resources[i]['ResourceName']))

print(ERASE_LINE)
print("We scanned {} accounts and {} regions totalling {} possible areas for resources.".format(len(ChildAccounts),len(cfg_regions),len(ChildAccounts)*len(cfg_regions)))
print()

###############
def delete_resources(fResource):
	session_aws_child=boto3.Session(
		aws_access_key_id=fResource['AccessKeyId'],
		aws_secret_access_key=fResource['SecretAccessKey'],
		aws_session_token=fResource['SessionToken'],
		region_name=fResource['Region'])
	if fResource['Type']=='Config Recorder':
		try:
			client_cfg=session_aws_child.client('config')
			Output=client_cfg.delete_configuration_recorder(
				ConfigurationRecorderName=fResource['ResourceName'])
		except Exception as e:
			logging.error("Problem with account %s in region %s",fResource['AccountId'],fResource['Region'])
			print("Caught unexpected error regarding deleting config recorders. Exiting...")
			pprint.pprint(e)
			sys.exit(9)
	elif fResource['Type']=='Delivery Channel':
		try:
			client_cfg=session_aws_child.client('config')
			Output=client_cfg.delete_delivery_channel(
				DeliveryChannelName=fResource['ResourceName'])
		except Exception as e:
			logging.error("Problem with account %s in region %s",fResource['AccountId'],fResource['Region'])
			print("Caught unexpected error regarding deleting delivery channel. Exiting...")
			pprint.pprint(e)
			sys.exit(9)
	elif fResource['Type']=='SNS Topic':
		try:
			client_sns=session_aws_child.client('sns')
			Output=client_sns.delete_topic(TopicArn=fResource['ResourceName'])
		except Exception as e:
			logging.error("Problem with account %s in region %s",fResource['AccountId'],fResource['Region'])
			print("Caught unexpected error regarding deleting SNS Topic. Exiting...")
			pprint.pprint(e)
			sys.exit(9)
	elif fResource['Type']=='Lambda Function':
		try:
			client_lam=session_aws_child.client('lambda')
			Output=client_lam.delete_function(FunctionName=fResource['ResourceName'])
		except Exception as e:
			logging.error("Problem with account %s in region %s",fResource['AccountId'],fResource['Region'])
			print("Caught unexpected error regarding deleting lambda function. Exiting...")
			pprint.pprint(e)
			sys.exit(9)
	elif fResource['Type']=='Log Group':
		try:
			client_cwl=session_aws_child.client('logs')
			Output=client_cwl.delete_log_group(
				logGroupName=fResource['ResourceName'])
		except Exception as e:
			logging.error("Problem with account %s in region %s",fResource['AccountId'],fResource['Region'])
			print("Caught unexpected error regarding deleting log group. Exiting...")
			pprint.pprint(e)
			sys.exit(9)
	else:
		print("Unrecognized Resource Type -- exiting.")
		sys.exit(10)
###############
if DeletionRun and not ForceDelete:
	ReallyDelete=(input ("Deletion of Config resources has been requested. Are you still sure? (y/n): ") == 'y')
else:
	ReallyDelete=False

if DeletionRun and (ReallyDelete or ForceDelete):
	logging.warning("Deleting all Config Resources")
	for y in range(len(all_config_resources)):
		print(ERASE_LINE+"Removing {} resource from account {}".format(all_config_resources[i]['Type'],all_config_resources[i]['AccountId']))
		try:
			logging.error("Deleting %s named %s",all_config_resources[y]['Type'], all_config_resources[y]['ResourceName'])
			delete_resources(all_config_resources[y])
		except Exception as e:
			pprint.pprint(e)
			sys.exit(9)
		'''
		session_cf_child=boto3.Session(
				aws_access_key_id=all_config_resources[y]['AccessKeyId'],
				aws_secret_access_key=all_config_resources[y]['SecretAccessKey'],
				aws_session_token=all_config_resources[y]['SessionToken'],
				region_name=all_config_resources[y]['Region'])
		client_cf_child=session_cf_child.client('config')
		## Delete ConfigurationRecorders
		try:
			print(ERASE_LINE,"Deleting recorder from Account {} in region {}".format(all_config_resources[y]['AccountId'],all_config_resources[y]['Region']),end="\r")
			Output=client_cf_child.delete_configuration_recorder(
				ConfigurationRecorderName=all_config_resources[y]['ResourceName']
			)
			# pprint.pprint(Output)
		except Exception as e:
			# if e.response['Error']['Code'] == 'BadRequestException':
			# 	logging.warning("Caught exception 'BadRequestException', handling the exception...")
			# 	pass
			# else:
				print("Caught unexpected error regarding deleting config recorders. Exiting...")
				pprint.pprint(e)
				sys.exit(9)
	print("Removed {} config recorders".format(len(all_config_resources)))
	for y in range(len(all_config_resources)):
		logging.info("Deleting delivery channel: %s from account %s in region %s" % (all_config_resources[y]['ResourceName'],all_config_resources[y]['AccountId'],all_config_resources[y]['Region']))
		print("Deleting delivery channel in account {} in region {}".format(all_config_resources[y]['AccountId'],all_config_resources[y]['Region']))
		session_cf_child=boto3.Session(
				aws_access_key_id=all_config_resources[y]['AccessKeyId'],
				aws_secret_access_key=all_config_resources[y]['SecretAccessKey'],
				aws_session_token=all_config_resources[y]['SessionToken'],
				region_name=all_config_resources[y]['Region'])
		client_cf_child=session_cf_child.client('config')
		## List Members
		Output=client_cf_child.delete_delivery_channel(
			DeliveryChannelName=all_config_resources[y]['ResourceName']
		)
		logging.warning("Delivery Channel %s has been deleted from child account %s in region %s" % (str(all_config_resources[y]['ResourceName'][0]),str(all_config_resources[y]['AccountId']),str(all_config_resources[y]['Region'])))
		'''
print()
print("Thank you for using this tool")
