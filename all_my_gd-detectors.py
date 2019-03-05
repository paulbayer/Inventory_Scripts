#!/usr/local/bin/python3

import os, sys, pprint
import Inventory_Modules, boto3
import argparse
from colorama import init,Fore,Back,Style
from boto3.session import Session
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from urllib3.exceptions import NewConnectionError

import logging

init()

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
<<<<<<< HEAD
	default=["all"],
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-r","--region",
	nargs="*",
	dest="pregions",
	metavar="region name string",
	# default=["us-east-1"],
	default=["all"],
	help="String fragment of the region(s) you want to check for resources.")
=======
	help="You need to specify a profile that represents the ROOT account.")
>>>>>>> development
parser.add_argument(
	"+delete", "+forreal",
	dest="flagDelete",
	default=False,
	action="store_const",
	const=True,
	help="Whether to delete the detectors it finds.")
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

# If plevel
	# 1: credentials file only
	# 2: config file only
	# 3: credentials and config files
<<<<<<< HEAD
pProfiles=args.pProfiles
pRegionList=args.pregions
DeletionRun=args.flagDelete
logging.basicConfig(level=args.loglevel)
# RegionList=[]

SkipProfiles=["default","Shared-Fid"]
=======
pProfile=args.pProfile
DeletionRun=args.flagDelete
logging.basicConfig(level=args.loglevel)
>>>>>>> development

##########################
ERASE_LINE = '\x1b[2K'

NumObjectsFound = 0
<<<<<<< HEAD
NumRegions = 0
print()
fmt='%-20s %-15s %-20s'
print(fmt % ("Profile","Region","Detector ID"))
print(fmt % ("-------","------","-----------"))

RegionList=Session(profile_name=pProfiles[0]).get_available_regions('guardduty')

# RegionList=Inventory_Modules.get_gd_regions(pRegionList,pProfiles[0])
ProfileList=Inventory_Modules.get_profiles(pProfiles,SkipProfiles,pProfiles[0])
# sys.exit(1)
DetectorsToDelete=[]
print("Searching {} profiles and {} regions".format(len(ProfileList),len(RegionList)))

for pregion in RegionList:
	NumRegions += 1
=======
NumAccountsInvestigated = 0
ChildAccounts2=[]
# try:
ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
# except:
for i in range(len(ChildAccounts)):
	if not (ChildAccounts[i]['AccountId']=='614019996801'):
		ChildAccounts2.append(ChildAccounts[i])
	else:
		continue
ChildAccounts=ChildAccounts2


session_gd=boto3.Session(profile_name=pProfile)
gd_regions=session_gd.get_available_regions(service_name='guardduty')
# gd_regions=["ap-south-1"]
all_gd_detectors=[]
all_gd_invites=[]
print("Searching {} accounts and {} regions".format(len(ChildAccounts),len(gd_regions)))

sts_session = boto3.Session(profile_name=pProfile)
sts_client = sts_session.client('sts')
for account in ChildAccounts:
>>>>>>> development
	NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(account['AccountId'])
	logging.info("Role ARN: %s" % role_arn)
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-GuardDuty-Detectors")['Credentials']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(profile+": Authorization Failure for account {}".format(account['AccountId']))
	for region in gd_regions:
		NumAccountsInvestigated += 1
		session_aws=boto3.Session(
			aws_access_key_id=account_credentials['AccessKeyId'],
			aws_secret_access_key=account_credentials['SecretAccessKey'],
			aws_session_token=account_credentials['SessionToken'],
			region_name=region)
		client_aws=session_aws.client('guardduty')
		## List Invitations
		try:
			response=client_aws.list_invitations()
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure for account {}".format(account['AccountId']))
		for i in range(len(response['Invitations'])):
			all_gd_invites.append({
				'AccountId':response['Invitations'][i]['AccountId'],
				'InvitationId':response['Invitations'][i]['InvitationId'],
				'Region':region,
				'AccessKeyId':account_credentials['AccessKeyId'],
				'SecretAccessKey':account_credentials['SecretAccessKey'],
				'SessionToken':account_credentials['SessionToken']
			})
		try:
			print(ERASE_LINE,"Trying account {} in region {}".format(account['AccountId'],region),end='\r')
			response=client_aws.list_detectors()
			if len(response['DetectorIds']) > 0:
				NumObjectsFound=NumObjectsFound + len(response['DetectorIds'])
				all_gd_detectors.append({
					'AccountId':account['AccountId'],
					'Region':region,
					'DetectorIds':response['DetectorIds'],
					'AccessKeyId':account_credentials['AccessKeyId'],
					'SecretAccessKey':account_credentials['SecretAccessKey'],
					'SessionToken':account_credentials['SessionToken']
				})
				logging.info("Found another detector ("+str(response['DetectorIds'][0])+") in account "+account['AccountId']+" in region "+account['AccountId']+" bringing the total found to "+str(NumObjectsFound))
			else:
				print(ERASE_LINE,"No luck in account: {}".format(account['AccountId']),end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure for account {}".format(account['AccountId']))
	print()

if args.loglevel < 50:
	print()
	fmt='%-20s %-15s %-20s'
	print(fmt % ("Account ID","Region","Detector ID"))
	print(fmt % ("----------","------","-----------"))
	for i in range(len(all_gd_detectors)):
		print(fmt % (all_gd_detectors[i]['AccountId'],all_gd_detectors[i]['Region'],all_gd_detectors[i]['DetectorIds']))

print(ERASE_LINE)
print("Found {} Invites across {} accounts across {} regions".format(len(all_gd_invites),len(ChildAccounts),len(gd_regions)))
print("Found {} Detectors across {} profiles across {} regions".format(NumObjectsFound,len(ChildAccounts),len(gd_regions)))
print()

<<<<<<< HEAD
if DeletionRun:
	for y in range(len(DetectorsToDelete)):
		logging.info("Deleting detector-id: %s from profile %s in region %s" % (DetectorsToDelete[y][0],DetectorsToDelete[y][1],DetectorsToDelete[y][2]))
		print("Deleting in profile {} in region {}".format(DetectorsToDelete[y][0],DetectorsToDelete[y][1]))
		Response=Inventory_Modules.del_gd_detectors(DetectorsToDelete[y][0],DetectorsToDelete[y][1],DetectorsToDelete[y][2])
=======


if DeletionRun and (input ("Deletion of Guard Duty detectors has been requested. Are you still sure? (y/n): ") == 'y'):
	MemberList=[]
	logging.info("Deleting all invites")
	for y in range(len(all_gd_invites)):
		session_gd_child=boto3.Session(
				aws_access_key_id=all_gd_invites[y]['AccessKeyId'],
				aws_secret_access_key=all_gd_invites[y]['SecretAccessKey'],
				aws_session_token=all_gd_invites[y]['SessionToken'],
				region_name=all_gd_invites[y]['Region'])
		client_gd_child=session_gd_child.client('guardduty')
		## Delete Invitations
		try:
			Output=client_gd_child.delete_invitations(
				AccountIds=[all_gd_invites[y]['AccountId']]
			)
			pprint.pprint(Output)
		except Exception as e:
			if e.response['Error']['Code'] == 'BadRequestException':
				logging.warning("Caught exception 'BadRequestException', handling the exception...")
				pass
			else:
				print("Caught unexpected error regarding deleting invites")
				pprint.pprint(e)
				sys.exit(9)
	for y in range(len(all_gd_detectors)):
		logging.info("Deleting detector-id: %s from account %s in region %s" % (all_gd_detectors[y]['DetectorIds'],all_gd_detectors[y]['AccountId'],all_gd_detectors[y]['Region']))
		print("Deleting detector in account {} in region {}".format(all_gd_detectors[y]['AccountId'],all_gd_detectors[y]['Region']))
		session_gd_child=boto3.Session(
				aws_access_key_id=all_gd_detectors[y]['AccessKeyId'],
				aws_secret_access_key=all_gd_detectors[y]['SecretAccessKey'],
				aws_session_token=all_gd_detectors[y]['SessionToken'],
				region_name=all_gd_detectors[y]['Region'])
		client_gd_child=session_gd_child.client('guardduty')
		## List Members
		Member_Dict=client_gd_child.list_members(
			DetectorId=str(all_gd_detectors[y]['DetectorIds'][0]),
    		OnlyAssociated='FALSE'
		)['Members']
		for i in range(len(Member_Dict)):
			MemberList.append(Member_Dict[i]['AccountId'])
		MemberList.append('704627748197')
		try:
			Output=client_gd_child.disassociate_from_master_account(
				DetectorId=str(all_gd_detectors[y]['DetectorIds'][0])
			)
		except Exception as e:
			if e.response['Error']['Code'] == 'BadRequestException':
				logging.warning("Caught exception 'BadRequestException', handling the exception...")
				pass
		## Disassociate Members
		##
		Output=client_gd_child.disassociate_members(
			AccountIds=MemberList,
    		DetectorId=str(all_gd_detectors[y]['DetectorIds'][0])
		)
		Output=client_gd_child.delete_members(
			AccountIds=[all_gd_detectors[y]['AccountId']],
    		DetectorId=str(all_gd_detectors[y]['DetectorIds'][0])
		)
		Output=client_gd_child.delete_detector(
    		DetectorId=str(all_gd_detectors[y]['DetectorIds'][0])
		)
>>>>>>> development
