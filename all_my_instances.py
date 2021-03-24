#!/user/bin/env python3

import os, sys, pprint, boto3, datetime
import Inventory_Modules
import argparse
from colorama import init, Fore
from botocore.exceptions import ClientError, ProfileNotFound, InvalidConfigError, NoCredentialsError, CredentialRetrievalError

import logging

init()

parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	default=None,
	help="To specify a specific profile, use this parameter. Default will be to use Environment Variables, including those in ~/.aws/credentials and ~/.aws/config")
parser.add_argument(
	"-r", "--region",
	nargs="*",
	dest="pRegion",
	metavar="region name string",
	default=["us-east-1"],
	help="String fragment of the region(s) you want to check for resources.")
parser.add_argument(
	"-k", "--skip",
	dest="pSkipAccounts",
	nargs="*",
	metavar="Accounts to leave alone",
	default=[],
	help="These are the account numbers you don't want to screw with. Likely the core accounts.")
parser.add_argument(
	'-d', '--debug',
	help="Print debugging statements - only for developers",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 10
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print info statements - mainly for developers",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vv',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING, # args.loglevel = 30
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-v', '--verbose',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR, # args.loglevel = 40
	default=logging.CRITICAL) # args.loglevel = 50
args = parser.parse_args()

pProfile=args.pProfile
pRegionList=args.pRegion
AccountsToSkip=args.pSkipAccounts
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

EnvVars={}
# Get environment variables
EnvVars['Profile'] = os.getenv('AWS_PROFILE')
EnvVars['AccessKey'] = os.getenv('AWS_ACCESS_KEY_ID')
EnvVars['SecretKey'] = os.getenv('AWS_SECRET_ACCESS_KEY')
EnvVars['SessionToken'] = os.getenv('AWS_SESSION_TOKEN')
EnvVars['DefaultRegion'] = os.getenv('AWS_DEFAULT_REGION')

pprint.pprint(EnvVars)

# try:
# 	response=Inventory_Modules.find_calling_identity('default')
# 	defaultWorks=True
# except ProfileNotFound as e:
# 	print(e)
# 	defaultWorks=False

# They provided a profile (or more than one) at the command line
if pProfile is not None:
	logging.error("Using the provided profile from the command line")
	SessionToken=False
	ProfileSupplied=True
	pass
# They didn't provide a profile parameter
elif pProfile is None:
	# They provided the profile name in the Environment Variables
	if EnvVars['Profile'] is not None:
		pProfile = [EnvVars['Profile']]
		SessionToken=False
		ProfileSupplied = True
		logging.error("Using profile from env vars: %s", pProfile[0])
	# They provided the Persistent Access Key and Secret in the Environment Variables
	elif EnvVars['AccessKey'] is not None and EnvVars['SessionToken'] is None:
		pProfile = [EnvVars['Profile']]
		SessionToken=False
		ProfileSupplied = False
		logging.error("Using provided access key: %s", pProfile)
	# They provided the ephemeral Access Key and Token in the Environment Variables
	elif EnvVars['AccessKey'] is not None and EnvVars['SessionToken'] is not None:
		pProfile = [EnvVars['Profile']]
		SessionToken=True
		ProfileSupplied = False
		logging.error("Using provided access key with a session token: %s", pProfile)
# They provided no credentials at all
else:
	print("No authentication mechanisms left!")
	sys.exit("No credentials left")

logging.error("We're using profiles: %s" % (pProfile))

SkipProfile=["default"]


##########################
ERASE_LINE = '\x1b[2K'

NumInstancesFound = 0
print()
if ProfileSupplied:
	fmt='%-12s %-15s %-10s %-15s %-25s %-20s %-42s %-12s'
	print(fmt % ("Profile", "Account #", "Region", "InstanceType", "Name", "Instance ID", "Public DNS Name", "State"))
	print(fmt % ("-------", "---------", "------", "------------", "----", "-----------", "---------------", "-----"))
elif not ProfileSupplied:
	fmt='%-15s %-10s %-15s %-25s %-20s %-42s %-12s'
	print(fmt % ("Account #", "Region", "InstanceType", "Name", "Instance ID", "Public DNS Name", "State"))
	print(fmt % ("---------", "------", "------------", "----", "-----------", "---------------", "-----"))


RegionList=Inventory_Modules.get_regions(pRegionList)
AllChildAccounts=[]
SoughtAllProfiles=False

# if "all" in pProfile:
# 	SoughtAllProfiles=True
# 	logging.info("Profiles sent to function get_parent_profiles: %s", pProfile)
# 	print("Since you specified 'all' profiles, we going to look through ALL of your profiles. Then we go through and determine which profiles represent the Master of an Organization and which are stand-alone accounts. This will enable us to go through all accounts you have access to for inventorying.")
# 	logging.error("Time: %s", datetime.datetime.now())
# 	try:
# 		pProfile=Inventory_Modules.get_parent_profiles('all',SkipProfiles)
# 	except ClientError as e:
# 		pass
# 	except CredentialRetrievalError as e:
# 		print(e)
# 		pass
# 	logging.error("Time: %s", datetime.datetime.now())
# 	logging.error("Found %s root profiles", len(pProfile))
# 	logging.info("Profiles Returned from function get_parent_profiles: %s", pProfile)

ProfileIsRoot = Inventory_Modules.find_if_org_root(pProfile)
#
# for pProfile in pProfile:
# 	if not SoughtAllProfiles:
# 		logging.info("Checking to see if the profiles passed in (%s) are root profiles", pProfile)
# 		# ProfileIsRoot=Inventory_Modules.find_if_org_root(pProfile)
# 		logging.info("---%s Profile---", ProfileIsRoot)
if ProfileIsRoot == 'Root':
	logging.info("Profile %s is a Root account", pProfile)
	ChildAccounts=Inventory_Modules.find_child_accounts2(pProfile)
	AllChildAccounts=Inventory_Modules.RemoveCoreAccounts(ChildAccounts, AccountsToSkip)
elif ProfileIsRoot == 'StandAlone':
	logging.info("Profile %s is a Standalone account", pProfile)
	MyAcctNumber=Inventory_Modules.find_account_number(pProfile)
	Accounts=[{
		'ParentProfile': pProfile,
		'AccountId': MyAcctNumber,
		'AccountEmail': 'noonecares@doesntmatter.com'}]
	AllChildAccounts=Accounts
elif ProfileIsRoot == 'Child':
	logging.info("Profile %s is a Child Account", pProfile)
	MyAcctNumber=Inventory_Modules.find_account_number(pProfile)
	Accounts=[{
		'ParentProfile': pProfile,
		'AccountId': MyAcctNumber,
		'AccountEmail': 'noonecares@doesntmatter.com'}]
	AllChildAccounts=Accounts

"""
logging.info("Passed as parameter %s:", pProfile)
logging.info("Passed to function %s:", pProfile)
logging.info("ChildAccounts %s:", ChildAccounts)
logging.info("AllChildAccounts %s:", AllChildAccounts)
"""
# ProfileList=Inventory_Modules.get_profiles(SkipProfiles, pProfile)
# pprint.pprint(RegionList)
# aws_session = boto3.Session(profile_name=pProfile)
# sts_client = aws_session.client('sts')
for i in range(len(AllChildAccounts)):
	aws_session = boto3.Session(profile_name=AllChildAccounts[i]['ParentProfile'])
	sts_client = aws_session.client('sts')
	logging.info("Single account record %s:", AllChildAccounts[i])
	"""
	TO DO - figure a way to find out whether this rolename is correct for every account?
	"""
	role_arn = "arn:aws:iam::{}:role/AWSCloudFormationStackSetExecutionRole".format(AllChildAccounts[i]['AccountId'])
	logging.info("Role ARN: %s" % role_arn)
	try:
		account_credentials = sts_client.assume_role(
			RoleArn=role_arn,
			RoleSessionName="Find-Instances")['Credentials']
		account_credentials['AccountNumber']=AllChildAccounts[i]['AccountId']
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			logging.error("%s: Authorization Failure for account %s", AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId'])
		elif str(my_Error).find("AccessDenied") > 0:
			logging.error("%s: Access Denied Failure for account %s", AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId'])
			logging.warning(my_Error)
		else:
			logging.error("%s: Other kind of failure for account %s", AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId'])
			logging.warning(my_Error)
		continue
	for pRegion in RegionList:
		try:
			Instances=Inventory_Modules.find_account_instances(account_credentials, pRegion)
			logging.warning("Account %s being looked at now", account_credentials['AccountNumber'])
			InstanceNum=len(Instances['Reservations'])
			print(ERASE_LINE+"Org Profile: {} Account: {} Region: {} Found {} instances".format(AllChildAccounts[i]['ParentProfile'], account_credentials['AccountNumber'], pRegion, InstanceNum), end='\r')
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error("Authorization Failure using {} parent profile to access {} account in {} region".format(AllChildAccounts[i]['ParentProfile'], AllChildAccounts[i]['AccountId'], pRegion))
				logging.warning("It's possible that the region %s hasn't been opted-into", pRegion)
				pass
		# if len(Instances['Reservations']) > 0:
		if 'Reservations' in Instances.keys():
			for y in range(len(Instances['Reservations'])):
				for z in range(len(Instances['Reservations'][y]['Instances'])):
					InstanceType=Instances['Reservations'][y]['Instances'][z]['InstanceType']
					InstanceId=Instances['Reservations'][y]['Instances'][z]['InstanceId']
					PublicDnsName=Instances['Reservations'][y]['Instances'][z]['PublicDnsName']
					State=Instances['Reservations'][y]['Instances'][z]['State']['Name']
					# print("Length:", len(Instances['Reservations'][y]['Instances'][z]['Tags']))
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
print("Found {} instances across {} profiles across {} regions".format(NumInstancesFound, len(AllChildAccounts), len(RegionList)))
print()
