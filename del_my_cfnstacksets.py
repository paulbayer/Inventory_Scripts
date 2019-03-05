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

import os, sys, pprint, argparse, logging, time
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
	dest="pProfile",
	metavar="profile to use",
	help="You need to specify a specific ROOT profile")
parser.add_argument(
	"-f","--fragment",
	dest="pStackfrag",
	nargs="*",
	metavar="CloudFormation stack fragment",
	default=["all"],
	help="List containing fragment(s) of the cloudformation stack or stackset(s) you want to check for.")
parser.add_argument(
	"-r","--region",
	dest="pRegion",
	metavar="region name string",
	default="us-east-1",
	help="The Master region you want to check for StackSets.")
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
parser.add_argument(
    '+forreal','+for-real','-for-real','-forreal','--for-real','--forreal','--forrealsies', '+delete',
    help="Do a Dry-run; don't delete anything",
    action="store_const",
	const=False,
	default=True,
	dest="DryRun")
args = parser.parse_args()

pProfile=args.pProfile
pRegion=args.pRegion
pStackfrag=args.pStackfrag
verbose=args.loglevel
pdryrun=args.DryRun
logging.basicConfig(level=args.loglevel)

SkipProfiles=["default","Shared-Fid"]

##########################
ERASE_LINE = '\x1b[2K'

AllInstances=[]
StackSetNames2=[]

print()

if pdryrun:
	print("You asked me to find (but not delete) stacksets that match the following:")
else:
	print("You asked me to find (and delete) stacksets that match the following:")
print("		In the ROOT profile {} and all children".format(pProfile))
print("		In these regions: {}".format(pRegion))
print("		For stacksets that contain these fragments: {}".format(pStackfrag))
print()
# fmt='%-20s | %-12s | %-10s | %-50s | %-25s | %-50s'
# print(fmt % ("Parent Profile","Acct Number","Region","Parent StackSet Name","Stack Status","Child Stack Name"))
# print(fmt %	("--------------","-----------","------","--------------------","----------------","----------------"))

''' Get the StackSet names from the Master Profile '''
StackSetNames=Inventory_Modules.find_stacksets(pProfile,pRegion,pStackfrag)
logging.info("Found %s StackSetNames that matched your fragment" % (len(StackSetNames)))
for i in range(len(StackSetNames)):
	if 'AWSControlTower' in StackSetNames[i]['StackSetName']:
		continue
	else:
		StackSetNames2.append(StackSetNames[i])
StackSetNames=StackSetNames2
for i in range(len(StackSetNames)):
	StackInstances=Inventory_Modules.find_stack_instances(pProfile,pRegion,StackSetNames[i]['StackSetName'])
	logging.warning("Found %s Stack Instances within the StackSet %s" % (len(StackInstances),StackSetNames[i]['StackSetName']))
	for j in range(len(StackInstances['Summaries'])):
		AllInstances.append({
			'ChildAccount':StackInstances['Summaries'][j]['Account'],
			'ChildRegion':StackInstances['Summaries'][j]['Region'],
			# This next line finds the value of the Child StackName (which includes a random GUID) and assigns it within our dict
			'StackName':StackInstances['Summaries'][j]['StackId'][StackInstances['Summaries'][j]['StackId'].find('/')+1:StackInstances['Summaries'][j]['StackId'].find('/',
			StackInstances['Summaries'][j]['StackId'].find('/')+1)],
			'StackStatus':StackInstances['Summaries'][j]['Status'],
			'StackSetName':StackInstances['Summaries'][j]['StackSetId'][:StackInstances['Summaries'][j]['StackSetId'].find(':')]
		})


# for profile in ProfileList:	# Expectation that there is ONLY ONE PROFILE MATCHED.
logging.warning("There are supposed to be %s stack instances." % (len(AllInstances)))
# pprint.pprint(AllInstances)

if args.loglevel < 31:
	for i in range(len(AllInstances)):
		print("Account {} in Region {} has Stack {} in status {}".format(
			AllInstances[i]['ChildAccount'],
			AllInstances[i]['ChildRegion'],
			AllInstances[i]['StackName'],
			AllInstances[i]['StackStatus'])
		)

if pdryrun:
	print("We're Done")
	sys.exit(0)

print("Removing {} stack instances from the StackSet".format(len(AllInstances)))

# ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
AccountList=[]
for i in range(len(AllInstances)):
	AccountList.append(AllInstances[i]['ChildAccount'])

AccountList=list(set(AccountList))

RegionList=[]
for i in range(len(AllInstances)):
	RegionList.append(AllInstances[i]['ChildRegion'])

RegionList=list(set(RegionList))


for account in AccountList:
	session_org=boto3.Session(profile_name=pProfile,region_name=pRegion)
	client_org=session_org.client('organizations')
	try:
		response=client_org.detach_policy(
			PolicyId='p-xtoiesld',
	    	TargetId=account
		)
		response=client_org.detach_policy(
			PolicyId='p-jbzyssxv',
	    	TargetId=account
		)
		response=client_org.detach_policy(
			PolicyId='p-vw7tcpfx',
	    	TargetId=account
		)
		response=client_org.detach_policy(
			PolicyId='p-t8f04zf9',
	    	TargetId=account
		)
		logging.info("Successfully detached policies from account %s" % (account))
	except Exception as e:
		if e.response['Error']['Code'] == 'OperationInProgressException':
			logging.info("Caught exception 'OperationInProgressException', handling the exception...")
			pass
		elif e.response['Error']['Code'] == 'PolicyNotAttachedException':
			logging.info("Caught exception 'PolicyNotAttachedException', handling the exception...")
			pass
		elif e.response['Error']['Code'] == 'ConcurrentModificationException':
			logging.info("Caught exception 'ConcurrentModificationException', handling the exception...")
			pass
		else:
			logging.info("Wasn't able to successfully detach policy from account %s. Maybe it's already detached?" % (account))
			break

for i in range(len(AllInstances)):
	logging.warning("Profile: %s | Region: %s | ChildAccount: %s" % (pProfile,AllInstances[i]['ChildRegion'],AllInstances[i]['ChildAccount']))
	session_cfn=Inventory_Modules.get_child_access(pProfile,AllInstances[i]['ChildRegion'],AllInstances[i]['ChildAccount'])
	client_cfn=session_cfn.client('cloudformation')
	try:
		response=client_cfn.update_termination_protection(
			EnableTerminationProtection=False,
	    	StackName=AllInstances[i]['StackName']
		)
	except Exception as e:
		if e.response['Error']['Code'] == 'ValidationError':
			logging.info("Caught exception 'ValidationError', ignoring the exception...")
			print()
			pass

	logging.info("Stack %s had termination protection removed from it in Account %s in Region %s" % (AllInstances[i]['StackName'],AllInstances[i]['ChildAccount'],AllInstances[i]['ChildRegion']))

for i in range(len(StackSetNames)):
	logging.warning("Removing all instances from %s StackSet" % (StackSetNames[i]['StackSetName']))
	OperationName=StackSetNames[i]['StackSetName']+'Deletion'
	try:
		response=Inventory_Modules.delete_stack_instances(pProfile,pRegion,AccountList,RegionList,StackSetNames[i]['StackSetName'],OperationName)
	except Exception as e:
		if e.response['Error']['Code'] == 'StackSetNotFoundException':
			logging.info("Caught exception 'StackSetNotFoundException', ignoring the exception...")
			pprint.pprint(e)
			print()
			pass

	StackInstancesDeleted=False
	while not StackInstancesDeleted:
		try:
			response1=client_cfn.list_stack_set_operations(StackSetName=StackSetNames[i]['StackSetName'])['Summaries'][0]['Status']
			response2=client_cfn.list_stack_instances(StackSetName=StackSetNames[i]['StackSetName'])['Summaries']
			StackInstancesDeleted=((response1 == 'SUCCEEDED' or response1 == 'FAILED') and (len(response2)==0))
			if not StackInstancesDeleted:
				print("Still waiting for {} to be fully deleted...")
				time.sleep(30)
		except Exception as e:
			logging.info("Caught exception 'StackSetNotFoundException', ignoring the exception...")
			StackInstancesDeleted=True
			pass

print("Now deleting {} stacksets from Root Profile".format(len(StackSetNames)))

try:
	for i in range(len(StackSetNames)):
		response=Inventory_Modules.delete_stackset(pProfile,pRegion,StackSetNames[i]['StackSetName'])
		logging.warning("StackSet %s has been deleted from Root account %s in region %s" % (StackSetNames[i]['StackSetName'],pProfile,pRegion))
except Exception as e:
	# if e.response['Error']['Code'] == 'OperationInProgressException':
	# 	logging.info("Caught exception 'OperationInProgressException', handling the exception...")
	# 	pass
	# elif e.response['Error']['Code'] == 'PolicyNotAttachedException':
	# 	logging.info("Caught exception 'PolicyNotAttachedException', handling the exception...")
	# 	pass
	# elif e.response['Error']['Code'] == 'ConcurrentModificationException':
	# 	logging.info("Caught exception 'ConcurrentModificationException', handling the exception...")
		pprint.pprint(e)
		pass

print()
print("Now we're done")
print()
sys.exit(95)
# AllInstancesSorted=
