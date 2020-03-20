#!/usr/local/bin/python3

import os, sys, pprint, boto3, datetime
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, InvalidConfigError, NoCredentialsError

import logging

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfiles",
	nargs="*",
	metavar="profile to use",
	default="[all]",
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-r","--region",
	nargs="*",
	dest="pRegion",
	metavar="region name string",
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
	"-k","--skip",
	dest="pSkipAccounts",
	nargs="*",
	metavar="Accounts to leave alone",
	default=[],
	help="These are the account numbers you don't want to screw with. Likely the core accounts.")
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const",
	dest="loglevel",
	const=logging.INFO,	# args.loglevel = 20
    default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
    '-dd',
    help="Print lots of debugging statements",
    action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 20
    default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.ERROR) # args.loglevel = 40
parser.add_argument(
    '-vv',
    help="Be MORE verbose",
    action="store_const",
	dest="loglevel",
	const=logging.WARNING) # args.loglevel = 30
args = parser.parse_args()

pProfiles=args.pProfiles
pRegionList=args.pRegion
AccountsToSkip=args.pSkipAccounts
# logging.basicConfig(level=args.loglevel, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
logging.basicConfig(level=args.loglevel)

SkipProfiles=["default","Shared-Fid", "BottomLine", "TsysRoot"]

##########################
ERASE_LINE = '\x1b[2K'

NumInstancesFound = 0
print()
fmt='%-12s %-15s %-10s %-15s %-20s %-20s %-42s %-12s'
print(fmt % ("Org Profile","Account","Region","InstanceType","Name","Instance ID","Public DNS Name","State"))
print(fmt % ("-----------","-------","------","------------","----","-----------","---------------","-----"))
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
AllChildAccounts=[]

if "all" in pProfiles:
	print(Fore.RED+"Doesn't yet work to specify 'all' profiles, since it takes a long time to go through and find only those profiles that either Org Masters, or stand-alone accounts",Fore.RESET)
	# sys.exit(1)
	logging.info("Profiles sent to get_profiles3: %s",pProfiles)
	pProfiles=Inventory_Modules.get_profiles3()
	logging.info("Profiles Returned from get_profiles3: %s",pProfiles)

for pProfile in pProfiles:
	logging.info("Parent Profile name: %s",pProfile)
	ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
	ChildAccounts=Inventory_Modules.RemoveCoreAccounts(ChildAccounts,AccountsToSkip)
	AllChildAccounts=AllChildAccounts+ChildAccounts
logging.info("Passed as parameter %s:",pProfiles)
logging.info("Passed to function %s:",pProfile)
logging.info("ChildAccounts %s:",ChildAccounts)
logging.info("AllChildAccounts %s:",AllChildAccounts)
# ProfileList=Inventory_Modules.get_profiles(SkipProfiles,pProfiles)
# pprint.pprint(RegionList)
# aws_session = boto3.Session(profile_name=pProfile)
# sts_client = aws_session.client('sts')
for i in range(len(AllChildAccounts)):
	aws_session = boto3.Session(profile_name=AllChildAccounts[i]['ParentProfile'])
	sts_client = aws_session.client('sts')
	logging.info("Single account record %s:",AllChildAccounts[i])
	role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(AllChildAccounts[i]['AccountId'])
	logging.info("Role ARN: %s" % role_arn)
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-Instances")['Credentials']
		account_credentials['AccountNumber']=AllChildAccounts[i]['AccountId']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(pProfile+": Authorization Failure for account {}".format(AllChildAccounts[i]['AccountId']))
		elif str(my_Error).find("AccessDenied") > 0:
			print(pProfile+": Access Denied Failure for account {}".format(AllChildAccounts[i]['AccountId']))
		else:
			print(pProfile+": Other kind of failure for account {}".format(AllChildAccounts[i]['AccountId']))
			print (my_Error)
		break
	for pRegion in RegionList:
		try:
			Instances=Inventory_Modules.find_account_instances(account_credentials,pRegion)
			logging.warning("Account %s being looked at now" % account_credentials['AccountNumber'])
			InstanceNum=len(Instances['Reservations'])
			print(ERASE_LINE+"Account: {} Region: {} Found {} instances".format(account_credentials['AccountNumber'],pRegion,InstanceNum),end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(ERASE_LINE+profile+": Authorization Failure")
				pass
		except InvalidConfigError as my_Error:
			if str(my_Error).find("does not exist") > 0:
				print(ERASE_LINE+profile+": config profile references profile in credentials file that doesn't exist")
				pass
		if len(Instances['Reservations']) > 0:
			for y in range(len(Instances['Reservations'])):
				for z in range(len(Instances['Reservations'][y]['Instances'])):
					InstanceType=Instances['Reservations'][y]['Instances'][z]['InstanceType']
					InstanceId=Instances['Reservations'][y]['Instances'][z]['InstanceId']
					PublicDnsName=Instances['Reservations'][y]['Instances'][z]['PublicDnsName']
					State=Instances['Reservations'][y]['Instances'][z]['State']['Name']
					# print("Length:",len(Instances['Reservations'][y]['Instances'][z]['Tags']))
					try:
						Name="No Name Tag"
						for x in range(len(Instances['Reservations'][y]['Instances'][z]['Tags'])):
							if Instances['Reservations'][y]['Instances'][z]['Tags'][x]['Key']=="Name":
								Name=Instances['Reservations'][y]['Instances'][z]['Tags'][x]['Value']
					except KeyError as my_Error:	# This is needed for when there is no "Tags" key within the describe-instances output
						logging.info(my_Error)
						pass
					if State == 'running':
						fmt='%-12s %-15s %-10s %-15s %-20s %-20s %-42s '+Fore.RED+'%-12s'+Fore.RESET
					else:
						fmt='%-12s %-15s %-10s %-15s %-20s %-20s %-42s %-12s'
					print(fmt % (AllChildAccounts[i]['ParentProfile'], account_credentials['AccountNumber'], pRegion, InstanceType, Name, InstanceId, PublicDnsName, State))
					NumInstancesFound += 1
print(ERASE_LINE)
print("Found {} instances across {} profiles across {} regions".format(NumInstancesFound,len(AllChildAccounts),len(RegionList)))
print()
