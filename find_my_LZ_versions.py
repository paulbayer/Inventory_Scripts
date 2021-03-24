#!/user/bin/env python3

import os, sys, pprint, datetime
import Inventory_Modules
import argparse, boto3
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, CredentialRetrievalError, InvalidConfigError, NoCredentialsError

import logging

init()

parser = argparse.ArgumentParser(
	description="This script finds the version of your ALZ.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="Must specify a root profile. Default will be the default profile. You can specify 'all' ")
parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 10
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
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
verbose=args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)30s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'
SkipProfiles=['default']

if pProfile in ['all', 'All', 'ALL']:
	logging.info("%s was provided as the profile, so we're going to check ALL of their profiles to find all of the management accounts, and list out all of their ALZ versions.", pProfile)
	print("You've specified multiple profiles, so we've got to find them, determine which profiles represent Management Accounts, and then parse through those. This will take a few moments.")
	AllProfiles=Inventory_Modules.get_profiles2()
else:
	AllProfiles=[pProfile]

ALZProfiles=[]
for profile in AllProfiles:
	print(ERASE_LINE,"Checking profile: {}".format(profile),end="\r")
	try:
		ALZMgmntAcct=Inventory_Modules.find_if_alz(profile)
		if ALZMgmntAcct['ALZ']:
			accountnum = Inventory_Modules.find_account_number(profile)
			ALZProfiles.append({
				'Profile': profile,
				'Acctnum': accountnum,
				'Region': ALZMgmntAcct['Region']
			})
	except ClientError as my_Error:
		if str(my_Error).find("UnrecognizedClientException") > 0:
			logging.error("%s: Security Issue", fProfile)
		elif str(my_Error).find("InvalidClientTokenId") > 0:
			logging.error("%s: Security Token is bad - probably a bad entry in config", fProfile)
			pass
	except CredentialRetrievalError as my_Error:
		if str(my_Error).find("CredentialRetrievalError") > 0:
			logging.error("%s: Some custom process isn't working", fProfile)
			pass
	except InvalidConfigError as my_Error:
		if str(my_Error).find("InvalidConfigError") > 0:
			logging.error("%s: profile is invalid. Probably due to a config profile based on a credential that doesn't work", fProfile)
			pass

print(ERASE_LINE)
fmt='%-20s %-13s %-15s %-35s %-21s'
print(fmt % ("Profile","Account","Region","ALZ Stack Name","ALZ Version"))
print(fmt % ("-------","-------","------","--------------","-----------"))

for item in ALZProfiles:
	aws_session=boto3.Session(profile_name=item['Profile'], region_name=item['Region'])
	aws_client=aws_session.client('cloudformation')
	stack_list=aws_client.describe_stacks()['Stacks']
	for i in range(len(stack_list)):
		logging.warning("Checking stack %s to see if it is the ALZ initiation stack" % (stack_list[i]['StackName']))
		if 'Description' in stack_list[i].keys() and stack_list[i]['Description'].find("SO0044") > 0:
			for j in range(len(stack_list[i]['Outputs'])):
				if stack_list[i]['Outputs'][j]['OutputKey'] == 'LandingZoneSolutionVersion':
					ALZVersion=stack_list[i]['Outputs'][j]['OutputValue']
					print(fmt % (item['Profile'], item['Acctnum'], item['Region'], stack_list[i]['StackName'],ALZVersion))

print(ERASE_LINE)
print("Checked {} accounts. Found {} ALZs".format(len(AllProfiles), len(ALZProfiles)))
print()
print("Thank you for using this script.")
