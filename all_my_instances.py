#!/usr/local/bin/python3

import os, sys, pprint
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
	dest="pregion",
	metavar="region name string",
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const",
	dest="loglevel",
	const=logging.DEBUG,
    default=logging.CRITICAL)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.INFO)
args = parser.parse_args()

pProfiles=args.pProfiles
pRegionList=args.pregion
logging.basicConfig(level=args.loglevel)

SkipProfiles=["default","Shared-Fid", "BottomLine", "TsysRoot"]

##########################
ERASE_LINE = '\x1b[2K'
NumInstancesFound = 0
NumRegions = 0
print()
fmt='%-20s %-10s %-15s %-20s %-20s %-42s %-12s'
print(fmt % ("Profile","Region","InstanceType","Name","Instance ID","Public DNS Name","State"))
print(fmt % ("-------","------","------------","----","-----------","---------------","-----"))
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList=Inventory_Modules.get_profiles(SkipProfiles,pProfiles)
# pprint.pprint(RegionList)

for pregion in RegionList:
	NumRegions += 1
	NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for profile in ProfileList:
		NumProfilesInvestigated += 1
		try:
			Instances=Inventory_Modules.find_profile_instances(profile,pregion)
			logging.warning("Profile %s being looked at now" % profile)
			InstanceNum=len(Instances['Reservations'])
			print(ERASE_LINE,"Profile: ",profile,"Region: ",pregion,"Found",InstanceNum,"instances",end='\r')
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
						fmt='%-20s %-10s %-15s %-20s %-20s %-42s '+Fore.RED+'%-12s'+Fore.RESET
					else:
						fmt='%-20s %-10s %-15s %-20s %-20s %-42s %-12s'
					print(fmt % (profile,pregion,InstanceType,Name,InstanceId,PublicDnsName,State))
					NumInstancesFound += 1
print(ERASE_LINE)
print("Found",NumInstancesFound,"instances across",NumProfilesInvestigated,"profiles across",NumRegions,"regions")
print()
