#!/usr/bin/env python3

import sys
import pprint
import Inventory_Modules
import boto3
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError

import logging

init()

"""
TODO:
- Enable the deletion of the config recorders / delivery channels from specific accounts (or all?) at the end.
"""
parser = CommonArguments()
parser.singleprofile()
parser.multiregion()
parser.verbosity()
parser.extendedargs()  # This adds additional *optional* arguments to the listing
parser.my_parser.add_argument(
		"+delete", "+forreal",
		dest="flagDelete",
		action="store_true",  # If the parameter is supplied, it will be true, otherwise it's false
		help="Whether to delete the configuration recorders and delivery channels it finds.")
parser.my_parser.add_argument(
		"-a", "--account",
		dest="pAccount",
		default=None,
		nargs="*",
		metavar="Account",
		help="Just the accounts you want to check")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegionList = args.Regions
pAccounts = args.pAccounts
AccountsToSkip = args.SkipAccounts
verbose = args.loglevel
DeletionRun = args.flagDelete
ForceDelete = args.Force
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'

NumObjectsFound = 0
NumAccountsInvestigated = 0
aws_acct = aws_acct_access(pProfile)
if pAccounts is None:
	ChildAccounts = aws_acct.ChildAccounts
else:
	for item in pAccounts:
		ChildAccounts.append({'AccountId': item})

ChildAccounts = Inventory_Modules.RemoveCoreAccounts(ChildAccounts, AccountsToSkip)

cf_regions = Inventory_Modules.get_service_regions('config', pRegionList)
all_config_recorders = []
all_config_delivery_channels = []
print("Searching {} accounts and {} regions".format(len(ChildAccounts), len(cf_regions)))

sts_client = aws_acct.session.client('sts')
for account in ChildAccounts:
	NumProfilesInvestigated = 0  # I only care about the last run - so I don't get profiles * regions.
	try:
		account_credentials = Inventory_Modules.get_child_access3(aws_acct, account['AccountId'])
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"Authorization Failure for account {account['AccountId']}")
		continue
	for region in cf_regions:
		NumAccountsInvestigated += 1
		session_aws = boto3.Session(
				aws_access_key_id=account_credentials['AccessKeyId'],
				aws_secret_access_key=account_credentials['SecretAccessKey'],
				aws_session_token=account_credentials['SessionToken'],
				region_name=region)
		client_aws = session_aws.client('config')
		# List Configuration_Recorders
		try:  # Looking for Configuration Recorders
			print(ERASE_LINE, f"Trying account {account['AccountId']} in region {region}", end='\r')
			response = client_aws.describe_configuration_recorders()
			logging.error("Successfully described config recorders")
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"Authorization Failure for account {account['AccountId']}")
			response = {}
		if 'ConfigurationRecorders' in response.keys():
			for i in range(len(response['ConfigurationRecorders'])):
				NumObjectsFound = NumObjectsFound + len(response['ConfigurationRecorders'])
				all_config_recorders.append({
					'AccountId'            : account['AccountId'],
					'ConfigurationRecorder': response['ConfigurationRecorders'][i]['name'],
					'Region'               : region,
					'AccessKeyId'          : account_credentials['AccessKeyId'],
					'SecretAccessKey'      : account_credentials['SecretAccessKey'],
					'SessionToken'         : account_credentials['SessionToken']
					})
				print(
						"Found another config recorder {} in account {} in region {} bringing the total found to {} ".format(
								str(response['ConfigurationRecorders'][i]['name']), account['AccountId'], region,
								str(NumObjectsFound)))
		try:  # Looking for Delivery Channels
			print(ERASE_LINE, f"Trying account {account['AccountId']} in region {region}", end='\r')
			response = client_aws.describe_delivery_channels()
			if len(response['DeliveryChannels']) > 0 and response['DeliveryChannels'][0]['name'][
			                                             -13:] != "DO-NOT-DELETE":
				NumObjectsFound = NumObjectsFound + len(response['DeliveryChannels'])
				all_config_delivery_channels.append({
					'AccountId'      : account['AccountId'],
					'Region'         : region,
					'DeliveryChannel': response['DeliveryChannels'][0]['name'],
					'AccessKeyId'    : account_credentials['AccessKeyId'],
					'SecretAccessKey': account_credentials['SecretAccessKey'],
					'SessionToken'   : account_credentials['SessionToken']
					})
				print(
						"Found another delivery_channel {} in account {} in region {} bringing the total found to {} ".format(
								str(response['DeliveryChannels'][0]['name']), account['AccountId'], region,
								str(NumObjectsFound)))
			# logging.info("Found another detector ("+str(response['DeliveryChannels'][0])+") in account "+account['AccountId']+" in region "+account['AccountId']+" bringing the total found to "+str(NumObjectsFound))
			else:
				print(ERASE_LINE,
				      f"{Fore.RED}No luck in account: {account['AccountId']} in region {region}{Fore.RESET}", end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(f"Authorization Failure for account {account['AccountId']}")

if args.loglevel < 50:
	print()
	fmt = '%-20s %-15s %-20s'
	print(fmt % ("Account ID", "Region", "Delivery Channel"))
	print(fmt % ("----------", "------", "----------------"))
	for i in range(len(all_config_delivery_channels)):
		print(fmt % (all_config_delivery_channels[i]['AccountId'], all_config_delivery_channels[i]['Region'],
		             all_config_delivery_channels[i]['DeliveryChannel']))

print(ERASE_LINE)
print("We scanned {} accounts and {} regions totalling {} possible areas for resources.".format(len(ChildAccounts),
                                                                                                len(cf_regions),
                                                                                                len(ChildAccounts) * len(
		                                                                                                cf_regions)))
print("Found {} Configuration Recorders across {} accounts across {} regions".format(len(all_config_recorders),
                                                                                     len(ChildAccounts),
                                                                                     len(cf_regions)))
print("Found {} Delivery Channels across {} profiles across {} regions".format(len(all_config_delivery_channels),
                                                                               len(ChildAccounts), len(cf_regions)))
print()

if DeletionRun and not ForceDelete:
	ReallyDelete = (input(
			"Deletion of Config Recorders and Delivery Channels has been requested. Are you still sure? (y/n): ") == 'y')
else:
	ReallyDelete = False

if DeletionRun and (ReallyDelete or ForceDelete):
	MemberList = []
	logging.warning("Deleting all Config Recorders")
	for y in range(len(all_config_recorders)):
		session_cf_child = boto3.Session(
				aws_access_key_id=all_config_recorders[y]['AccessKeyId'],
				aws_secret_access_key=all_config_recorders[y]['SecretAccessKey'],
				aws_session_token=all_config_recorders[y]['SessionToken'],
				region_name=all_config_recorders[y]['Region'])
		client_cf_child = session_cf_child.client('config')
		# Delete ConfigurationRecorders
		try:
			print(ERASE_LINE,
			      f"Deleting recorder from Account {all_config_recorders[y]['AccountId']} in region {all_config_recorders[y]['Region']}",
			      end="\r")
			Output = client_cf_child.delete_configuration_recorder(
					ConfigurationRecorderName=all_config_recorders[y]['ConfigurationRecorder']
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
	print("Removed {} config recorders".format(len(all_config_recorders)))
	for y in range(len(all_config_delivery_channels)):
		logging.info(f"Deleting delivery channel: {all_config_delivery_channels[y]['DeliveryChannel']} from account "
		             f"{all_config_delivery_channels[y]['AccountId']} in region {all_config_delivery_channels[y]['Region']}")
		print(f"Deleting delivery channel in account {all_config_delivery_channels[y]['AccountId']} in "
		      f"region {all_config_delivery_channels[y]['Region']}", end='\r')
		session_cf_child = boto3.Session(
				aws_access_key_id=all_config_delivery_channels[y]['AccessKeyId'],
				aws_secret_access_key=all_config_delivery_channels[y]['SecretAccessKey'],
				aws_session_token=all_config_delivery_channels[y]['SessionToken'],
				region_name=all_config_delivery_channels[y]['Region'])
		client_cf_child = session_cf_child.client('config')
		# List Members
		Output = client_cf_child.delete_delivery_channel(
				DeliveryChannelName=all_config_delivery_channels[y]['DeliveryChannel']
				)
		logging.warning(
				f"Delivery Channel {str(all_config_delivery_channels[y]['DeliveryChannel'][0])} has been deleted from child account {str(all_config_delivery_channels[y]['AccountId'])} in region {str(all_config_delivery_channels[y]['Region'])}")

print()
print("Thank you for using this tool")
