#!/usr/local/bin/python3


import os, sys, argparse, logging, pprint
import boto3, re
from botocore.exceptions import ClientError, NoCredentialsError

# pProfile="ChildAccount"
# pRegion="us-east-1"
# pVPCId=""
# pDryRun=True
#
# UsageMsg="You need to run this and provide the profile, region, and vpcid."
# parser = argparse.ArgumentParser(description="We\'re going to find all publicly open Security Groups ad close them up.",prefix_chars='-+/')
# parser.add_argument("-p","--profile", dest="pProfile", metavar="Profile", default="EmptyProfile", help="The Profile to use for access")
# parser.add_argument("-r","--region", dest="pRegion", metavar="Region", default="us-east-1", help="The Region where the VPC is located")
# parser.add_argument("-v","--vpcid", dest="pVPCId", metavar="VPCId", default="EmptyVPC",help="The ID of the VPC to forcibly delete")
# parser.add_argument("-d","--dryrun", dest="pDryRun", default=True, action='store_false', help='Whether this is a DryRun or not. Default is TRUE (it\'s a dry-run), but \'-d\' will really run the script.')
# parser.add_argument("+d","++dryrun", dest="pDryRun", default=True, action='store_true', help='Whether this is a DryRun or not. Default is TRUE (it\'s a dry-run), but \'-d\' will really run the script.')
# parser.add_argument("-b","--badcidr", dest="pBadSrcCIDR", metavar="BadSrcCIDR", default="0.0.0.0/0", help="The CIDR Range from which the SG is *inappropriately* open")
# parser.add_argument("-g","--goodcidr", dest="pGoodSrcCIDR", metavar="GoodSrcCIDR", nargs='+', default=["8.8.8.0/24","9.9.9.0/24"], help="The CIDR List you'd like to replace that with")
#
# args=parser.parse_args()
#
# # print("Profile:",args.pProfile, type(args.pProfile))
# # print("Region:",args.pRegion, type(args.pRegion))
# # print("VPC:",args.pVPCId, type(args.pVPCId))
# # print("DryRun:",args.pDryRun, type(args.pDryRun))
# if args.pProfile == 'EmptyProfile':
# 	print()
# 	print("The Profile parameter is required. Please try again")
# 	print()
# 	sys.exit("Required Parameters weren\'t set")
#
# pProfile=args.pProfile
# pRegion=args.pRegion
# pVPCId=args.pVPCId
# pDryRun=args.pDryRun
# pBadSrcCIDR=args.pBadSrcCIDR
# pGoodSrcCIDR=args.pGoodSrcCIDR

fRegion = "us-east-1"

def find_org_root(fProfile,fRegion):

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations',fRegion)
	response=client_org.describe_organization()
	root_org=response['Organization']['MasterAccountId']
	return (root_org)

def find_child_accounts(fProfile,fRegion):

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations',fRegion)
	response=client_org.list_accounts()
	for account in response['Accounts']:
		child_accounts.append(account['Id'])
	return (child_accounts)

def find_account_number(fProfile,fRegion):

	session_sts = boto3.Session(profile_name=fProfile)
	client_sts = session_sts.client('sts',fRegion)
	response=client_sts.get_caller_identity()
	acct_num=response['Account']
	return (acct_num)

def get_profiles():
	from pathlib import Path
	home = str(Path.home())

	profiles = []

	with open(home+"/.aws/credentials","r") as creds_file:
		cred_data = creds_file.readlines()

	# with open(home+"/.aws/config","r") as config_file:
	# 	conf_data = config_file.readlines()

	for line in cred_data:
		if ("[" in line and not line[1] == "#"):
			profile = (line[1:-2])
			# print (profile)
			profiles.append(profile)
	# for line in conf_data:
	# 	if ("[profile" in line and not line[0] == "#"):
	# 		profile = (line[9:-2])
	# 		# print (profile)
	# 		profiles.append(profile)
	return(profiles)


print ("------------------------------------")
print ("%-20s %-20s %-40s %-10s" % ("Profile Name","Account Number","Master Org Acct","Root Acct?"))
print ("%-20s %-20s %-40s %-10s" % ("------------","--------------","---------------","----------"))

RootAccts=[]
RootProfiles=[]
for profile in get_profiles():
	AcctNum = "Blank Acct"
	MasterAcct = "Blank Root"
	ErrorFlag = False
	try:
		AcctNum = find_account_number(profile,fRegion)
		MasterAcct = find_org_root(profile,fRegion)
	except ClientError as my_Error:
		ErrorFlag = True
		if str(my_Error).find("AWSOrganizationsNotInUseException") > 0:
			MasterAcct="Not an Org Account"
		elif str(my_Error).find("AccessDenied") > 0:
			MasterAcct="Not authorized for API call."
		else:
			print(my_Error)
	except NoCredentialsError as my_Error:
		ErrorFlag = True
		if str(my_Error).find("Unable to locate credentials") > 0:
			MasterAcct="This profile doesn't have credentials."
		else:
			print(my_Error)

	if (AcctNum==MasterAcct and not ErrorFlag):
		RootAcct=True
		RootAccts.append(MasterAcct)
		RootProfiles.append(profile)
	else:
		RootAcct=False
	print ("%-20s %-20s %-40s %-10s" % (profile,AcctNum,MasterAcct,RootAcct))

print ("-------------------")

# print("Root Accounts found:",set(RootAccts))
# print("Root Profiles found:",set(RootProfiles))

for profile in RootProfiles:
	child_accounts=[]
	child_accounts=find_child_accounts(profile,fRegion)
	print("%-20s" % (profile),":",child_accounts)
