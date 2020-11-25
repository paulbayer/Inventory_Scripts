#!/usr/local/bin/python3

import os, sys, pprint, boto3, re, datetime
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

import logging

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all SSM parameters within the master profile, and optionally delete some of them.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-r","--region",
	dest="pRegion",
	metavar="region name string",
	default="us-east-1",
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
	'--ALZ',
	help="Identify left-over parameters created by the ALZ solution",
	action="store_const",
	dest="ALZParam",
	const=True,
	default=False)
parser.add_argument(
	'-b', '--daysback',
	help="Only keep the last x days of Parameters (default 90)",
	dest="DaysBack",
	default=90)
parser.add_argument(
	'+d','--delete',
	help="Delete left-over parameters created by the ALZ solution",
	action="store_const",
	dest="DeletionRun",
	const=True,
	default=False)
parser.add_argument(
	'-v', '--verbose',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR, # args.loglevel = 40
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vv',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING, # args.loglevel = 30
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-d', '--debug',
	help="Print debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 10
	default=logging.CRITICAL) # args.loglevel = 50
args = parser.parse_args()

pProfile=args.pProfile
pRegion=args.pRegion
ALZParam=args.ALZParam
DeletionRun=args.DeletionRun
dtDaysBack=datetime.timedelta(days=int(args.DaysBack))
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'
ALZRegex='/\w{8,8}-\w{4,4}-\w{4,4}-\w{4,4}-\w{12,12}/\w{3,3}'
print()
fmt='%-15s %-20s'
print(fmt % ("Parameter Name","Last Modified Date"))
print(fmt % ("--------------","------------------"))

session_ssm = boto3.Session(profile_name=pProfile)
client_ssm = session_ssm.client('ssm')
Parameters=[]
ParamsToDelete=[]
ALZParams=0

try:
	# Since there could be 10,000 parameters stored in the Parameter Store - this function COULD take a long time
	Parameters=Inventory_Modules.find_ssm_parameters(pProfile,pRegion)
	logging.error("Profile: %s found a total of %s parameters",pProfile, len(Parameters))
	# print(ERASE_LINE,"Account:",account['AccountId'],"Found",len(Users),"users",end='\r')
except ClientError as my_Error:
	if str(my_Error).find("AuthFailure") > 0:
		print("{}: Authorization Failure".format(pProfile))

if ALZParam:
	today=datetime.datetime.now(tz=datetime.timezone.utc)
	for y in range(len(Parameters)):
		# If the parameter matches the string regex of "/2ac07efd-153d-4069-b7ad-0d18cc398b11/105" - then it should be a candidate for deletion
		# With Regex - I'm looking for "/\w{8,8}-\w{4,4}-\w{4,4}-\w{4,4}-\w{12,12}/\w{3,3}"
		ParameterDate=Parameters[y]['LastModifiedDate']
		mydelta=today-ParameterDate	# this is a "timedelta" object
		p=re.compile(ALZRegex)	# Sets the regex to look for
		logging.info("Parameter %s: %s with date %s",y,Parameters[y]['Name'], Parameters[y]['LastModifiedDate'])
		if p.match(Parameters[y]['Name']) and mydelta > dtDaysBack:
			logging.error("Parameter %s with date of %s matched",Parameters[y]['Name'],Parameters[y]['LastModifiedDate'])
			ALZParams+=1
			if DeletionRun:
				ParamsToDelete.append(Parameters[y]['Name'])
if DeletionRun:
	print("Deleting {} ALZ-related Parameters now, further back than {} days".format(len(ParamsToDelete),dtDaysBack.days))
	# for i in range(len(ParamsToDelete)):
	mark=0
	i=0
	while i < len(ParamsToDelete)+1:
		i+=1
		if i % 10 == 0:
			response=client_ssm.delete_parameters(
				Names=ParamsToDelete[mark:i]
			)
			mark=i
			print(ERASE_LINE,"{} parameters deleted and {} more to go...".format(i,len(ParamsToDelete)-i),end='\r')
		elif i == len(ParamsToDelete):
			response=client_ssm.delete_parameters(
				Names=ParamsToDelete[mark:i]
			)
			logging.warning("Deleted the last %s parameters.",i%10)
print()
print(ERASE_LINE)
print("Found {} total parameters".format(len(Parameters)))
if ALZParam:
	print("And {} of them were from buggy ALZ runs more than {} days back".format(ALZParams,dtDaysBack.days))
if DeletionRun:
	print("And we deleted {} of them".format(len(ParamsToDelete)))
print()
print("Thanks for using this script.")
print()