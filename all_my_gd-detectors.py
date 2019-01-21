#!/usr/local/bin/python3

import os, sys, pprint
import Inventory_Modules
import argparse
from colorama import init,Fore,Back,Style
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
	dest="pProfiles",
	nargs="*",
	metavar="profile to use",
	default=["all"],
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-r","--region",
	nargs="*",
	dest="pregion",
	metavar="region name string",
	# default=["us-east-1"],
	default=["all"],
	help="String fragment of the region(s) you want to check for resources.")
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
	const=logging.DEBUG,
    default=logging.CRITICAL)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const",
	dest="loglevel",
	const=logging.INFO)
args = parser.parse_args()

# If plevel
	# 1: credentials file only
	# 2: config file only
	# 3: credentials and config files
pProfiles=args.pProfiles
pRegionList=args.pregion
DeletionRun=args.flagDelete
logging.basicConfig(level=args.loglevel)
# RegionList=[]

# SkipProfiles=["default"]
SkipProfiles=["default","Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

NumObjectsFound = 0
NumRegions = 0
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
ProfileList=Inventory_Modules.get_profiles(pProfiles,SkipProfiles)# pprint.pprint(RegionList)
# sys.exit(1)
DetectorsToDelete=[]
print("Searching {} profiles and {} regions".format(len(ProfileList),len(RegionList)))

print()
fmt='%-20s %-15s %-20s'
print(fmt % ("Profile","Region","Detector ID"))
print(fmt % ("-------","------","-----------"))

for pregion in RegionList:
	NumRegions += 1
	NumProfilesInvestigated = 0	# I only care about the last run - so I don't get profiles * regions.
	for profile in ProfileList: #Inventory_Modules.get_profiles(pProfiles,SkipProfiles):
		NumProfilesInvestigated += 1
		try:
			Output=Inventory_Modules.find_gd_detectors(profile,pregion)
			NumObjects=len(Output['DetectorIds'])
			logging.info("Profile: %s | Region: %s | Found %s Items",profile,pregion,NumObjects)
			print(ERASE_LINE,"Profile: {} Region: {} Found {} Items".format(profile,pregion,NumObjects),end='\r')
			if NumObjects > 0:
				DetectorsToDelete.append([profile,pregion,Output['DetectorIds'][0]])

			"""
			Format of DetectorsToDelete List:
				[0] = Profile name
				[1] = Region name
				[2] = Detector id to be deleted
			"""
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(ERASE_LINE+profile+": Authorization Failure")
		except TypeError as my_Error:
			# print(my_Error)
			pass
		except EndpointConnectionError as my_Error:
			# Can't connect to this particular region's endpoint - which may not exist.
			if str(my_Error).find("Could not connect to the endpoint URL") > 0:
				print(ERASE_LINE+profile+": Endpoint Connection Failure")
		except NewConnectionError as my_Error:
			# Can't connect to this particular region's endpoint - which may not exist.
			if str(my_Error).find("Failed to establish a new connection") > 0:
				print(ERASE_LINE+profile+": Endpoint Connection Failure")
		if len(Output['DetectorIds']) > 0:
			print(fmt % (profile,pregion,Output['DetectorIds'][0]))
			NumObjectsFound += 1
print(ERASE_LINE)
print("Found",NumObjectsFound,"Detectors across",NumProfilesInvestigated,"profiles across",NumRegions,"regions")
print()

if DeletionRun:
	for y in range(len(DetectorsToDelete)):
		logging.info("Deleting detector-id: %s from profile %s in region %s" % (DetectorsToDelete[y][0],DetectorsToDelete[y][1],DetectorsToDelete[y][2]))
		print("Deleting in profile {} in region {}".format(DetectorsToDelete[y][0],DetectorsToDelete[y][1]))
		Output=Inventory_Modules.del_gd_detectors(DetectorsToDelete[y][0],DetectorsToDelete[y][1],DetectorsToDelete[y][2])
