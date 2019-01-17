#!/usr/local/bin/python3

'''
TODO:
	- Enable this script to accept a Session Token to allow for Federated users via Isengard
	- Pythonize the whole thing
	- Write a requirements file to desribe the requirements (like colorama, pprint, argparse, etc.)
	- More Commenting throughout script
	- Right now it supports multiple profiles - however, deleting the stackSETs at the end only works if there's only one "main" profile submitted. Deleting the child stacks works regardless
	- Consider using "f'strings" for the print statements
	- There are four possible use-cases:
		- The stack exists as an association within the stackset AND it exists within the child account (typical)
			- We should remove the stackset-association with "--RetainStacks=False" and that will remove the child stack in the child account.
		- The stack exists as an association within the stackset, but has been manually deleted within the child account
			- If we remove the stackset-association with "--RetainStacks=False", it won't error, even when the stack doesn't exist within the child.
		- The stack doesn't exist within the stackset association, but DOES exist within the child account (because its association was removed from the stackset)
			- The only way to remove this is to remove the stack from the child account. This would have to be done after having found the stack within the child account. This will be a ToDo for later...
		- The stack doesn't exist within the child account, nor within the stack-set
			- Nothing to do here
'''

import os, sys, pprint, argparse, logging
# from sty import
import Inventory_Modules
import boto3
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfiles",
	nargs="*",
	metavar="profile to use",
	default=["default"],
	help="To specify a specific profile, use this parameter. Default will be ALL profiles, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-f","--fragment",
	dest="pstackfrag",
	nargs="*",
	metavar="CloudFormation stack fragment",
	default=["all"],
	help="List containing fragment(s) of the cloudformation stack or stackset(s) you want to check for.")
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
parser.add_argument(
    '+forreal','+for-real','-for-real','-forreal','--for-real','--forreal','--forrealsies',
    help="Do a Dry-run; don't delete anything",
    action="store_const",
	const=False,
	default=True,
	dest="DryRun")
args = parser.parse_args()

pProfiles=args.pProfiles
pRegionList=args.pregion
pstackfrag=args.pstackfrag
verbose=args.loglevel
pdryrun=args.DryRun
logging.basicConfig(level=args.loglevel)

SkipProfiles=["default","Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

NumStacksFound = 0
NumStackSetsFound=0
# NumMasterRegions = 0
StacksToDelete=[]
StackInstancesToDelete=[]
print()

# Find all stacksets in this region
RegionList=Inventory_Modules.get_ec2_regions(pRegionList)
# This is just here to validate that we're finding the right SINGLE profile.
ProfileList=Inventory_Modules.get_profiles(pProfiles,SkipProfiles)
logging.info("There are %s profiles that match your profile string" % (len(ProfileList)))

if pdryrun:
	print("You asked me to find (but not delete) stacksets that match the following:")
else:
	print("You asked me to find (and delete) stacksets that match the following:")
print("		In this profile: {}".format(pProfiles))
print("		In these regions: {}".format(pRegionList))
print("		For stacksets that contain these fragments: {}".format(pstackfrag))
print()
# fmt='%-20s | %-12s | %-10s | %-50s | %-25s | %-50s'
# print(fmt % ("Parent Profile","Acct Number","Region","Parent StackSet Name","Stack Status","Child Stack Name"))
# print(fmt %	("--------------","-----------","------","--------------------","----------------","----------------"))
if len(pProfiles) > 1:
	print("There is only supposed to be one profile that matches!")
	pprint.pprint(ProfileSet)
	print("Exiting now... ")
	sys.exit(11)
else:
	profile=pProfiles[0]
	pregion=RegionList[0]
	print("The single profile to be looked at {}:".format(profile))
	print("The single region to be looked at {}:".format(pregion))


# for profile in ProfileList:	# Expectation that there is ONLY ONE PROFILE MATCHED.
if True:
# for profile in pProfiles:
	if True:
	# for pregion in RegionList:
	# This section gets the listing of Stacksets for the profile(s) that were supplied at the command line.
		try:
			print(ERASE_LINE,Fore.BLUE,"	Looking in profile {profile_name} in region {region_name}".format(profile_name=profile,region_name=pregion),Fore.RESET,end='\r')
			# The command below finds the stacksets with the fragment in the name
			"""
			Import to note that the below command requires the "pstackfrag" parameter to be a list. Otherwise just about everything will be returned.
			"""
			Stacksets=Inventory_Modules.find_stacksets(profile,pregion,pstackfrag)
			NumStackSetsFound = NumStackSetsFound + len(Stacksets)
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				print(profile+": Authorization Failure")
		# Delve into the stack associations for each StackSet, and find which accounts and regions have the child stacks
		# Since "Stacksets" comes from the previous function - we know every stackset listed has the fragment in the name.
		print("Found {} StackSets that match your fragment(s): {}".format(len(Stacksets),pstackfrag))
		for Stackset in Stacksets:
			stackset_associations=Inventory_Modules.find_stack_instances(profile,pregion,Stackset['StackSetName'])
			logging.info("Profile: %s Stack: %s has %s child stacks" % (profile,Stackset['StackSetName'],len(stackset_associations['Summaries'])))
			for operation in stackset_associations['Summaries']:
				# Since we should be able to remove the child stack from the parent stackset - we're going to change the code to use that method instead.
				logging.info("StackSet %s in the parent profile %s is connected to the account %s in the %s Region" % (Stackset['StackSetName'],profile,operation['Account'],operation['Region']))
				StackInstancesToDelete.append([profile,pregion,operation['Account'],operation['Region'],Stackset['StackSetName']])
				"""
				Explanation of StackInstancesToDelete Dictionary:
					StackInstancesToDelete[0] = Master Account Profile
					StackInstancesToDelete[1] = Master Account Region where the StackSet is
					StackInstancesToDelete[2] = Child Account Number
					StackInstancesToDelete[3] = Child Account Region
					StackInstancesToDelete[4] = Master Account StackSetName
				"""
				logging.info(Fore.BLUE+"Instead of deleting the relevant child stack just yet - we'll list it first..."+Fore.RESET)

		# This is the level where we should delete by region
		# Go to all of those accounts and delete their stacks

	# This is the level where we should delete by profile
print ("Found a total of {} associations".format(len(StackInstancesToDelete)))

StackSetRegionSet=set()
StackSetAccountSet=set()
StackSetNameSet=set()
ProfileSet=set()
StackSetMasterRegionSet=set()

for i in range(len(StackInstancesToDelete)):
	ProfileSet.add(StackInstancesToDelete[i][0])
for i in range(len(StackInstancesToDelete)):
	StackSetMasterRegionSet.add(StackInstancesToDelete[i][1])
for i in range(len(StackInstancesToDelete)):
	StackSetNameSet.add(StackInstancesToDelete[i][4])

for StackSetName in StackSetNameSet:
	for i in range(len(StackInstancesToDelete)):
		if StackInstancesToDelete[i][4]==StackSetName:
			logging.info("StackSetName: %s | Account %s | Region %s" % (StackInstancesToDelete[i][4],StackInstancesToDelete[i][2],StackInstancesToDelete[i][3]))

for StackSetName in StackSetNameSet:
	if not pdryrun:
		"""
		Already picking the stackname -
			- In only the Master Account
			- In only the region which this stackset was found
			- Delete the stackset_instances, in all regions listed (extra regions won't matter)
			- in all the accounts it's been found in
		"""


		print("Deleting all associations for: {}".format(StackSetName))
		for i in range(len(StackInstancesToDelete)):
			if StackInstancesToDelete[i][4]==StackSetName:
				StackSetAccountSet.add(StackInstancesToDelete[i][2])
				StackSetRegionSet.add(StackInstancesToDelete[i][3])
		print("The Accounts and Regions for StackSet {}".format(StackSetName))
		pprint.pprint(StackSetAccountSet)
		pprint.pprint(StackSetRegionSet)
		session_cfn=boto3.Session(profile_name=profile,region_name=pregion)
		client_cfn=session_cfn.client('cloudformation')
		StackInstance_response=client_cfn.delete_stack_instances(
		    			StackSetName=StackSetName,
						Accounts=list(StackSetAccountSet),
						Regions=list(StackSetRegionSet),
						RetainStacks=False
						)
		logging.info("Deleting StackSet %s in Profile %s" % (StackSetName,profile))
		print("Deleting StackSet %s in Profile %s" % (StackSetName,profile))
		StackSet_response=client_cfn.delete_stack_set(StackSetName=StackSetName)

# Now to delete the original stackset itself
sys.exit(13)


print()
print("Account Set:")
pprint.pprint(AccountSet)
print(Fore.RED+"Initially found {} StackSets across {} regions within the Master profile".format(NumStackSetsFound,len(StackRegionSet))+Fore.RESET)
print(Fore.RED+"Then we found {} child stacks across {} regions across {} accounts".format(len(StacksToDelete),len(StackRegionSet),len(AccountSet))+Fore.RESET)
print()
