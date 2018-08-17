#!/usr/local/bin/python3


import os, sys, argparse, logging, pprint
import boto3

pProfile="ChildAccount"
pRegion="us-east-1"
pVPCId=""
pDryRun=True

UsageMsg="You need to run this and provide the profile, region, and vpcid."
parser = argparse.ArgumentParser(description="We\'re going to find all publicly open Security Groups ad close them up.",prefix_chars='-+/')
parser.add_argument("-p","--profile", dest="pProfile", metavar="Profile", default="EmptyProfile", help="The Profile to use for access")
parser.add_argument("-r","--region", dest="pRegion", metavar="Region", default="us-east-1", help="The Region where the VPC is located")
parser.add_argument("-v","--vpcid", dest="pVPCId", metavar="VPCId", default="EmptyVPC",help="The ID of the VPC to forcibly delete")
parser.add_argument("-d","--dryrun", dest="pDryRun", default=True, action='store_false', help='Whether this is a DryRun or not. Default is TRUE (it\'s a dry-run), but \'-d\' will really run the script.')
parser.add_argument("+d","++dryrun", dest="pDryRun", default=True, action='store_true', help='Whether this is a DryRun or not. Default is TRUE (it\'s a dry-run), but \'-d\' will really run the script.')
parser.add_argument("-b","--badcidr", dest="pBadSrcCIDR", metavar="BadSrcCIDR", default="0.0.0.0/0", help="The CIDR Range from which the SG is *inappropriately* open")
parser.add_argument("-g","--goodcidr", dest="pGoodSrcCIDR", metavar="GoodSrcCIDR", nargs='+', default=["8.8.8.0/24","9.9.9.0/24"], help="The CIDR List you'd like to replace that with")

args=parser.parse_args()

# print("Profile:",args.pProfile, type(args.pProfile))
# print("Region:",args.pRegion, type(args.pRegion))
# print("VPC:",args.pVPCId, type(args.pVPCId))
# print("DryRun:",args.pDryRun, type(args.pDryRun))
if args.pProfile == 'EmptyProfile':
	print()
	print("The Profile parameter is required. Please try again")
	print()
	sys.exit("Required Parameters weren\'t set")

pProfile=args.pProfile
pRegion=args.pRegion
pVPCId=args.pVPCId
pDryRun=args.pDryRun
pBadSrcCIDR=args.pBadSrcCIDR
pGoodSrcCIDR=args.pGoodSrcCIDR


def find_open_sgs(fProfile,fRegion,fVPCId,fCIDRRange):

	import boto3

	session_ec2 = boto3.Session(profile_name=fProfile)
	client_ec2 = session_ec2.client('ec2',fRegion)
	open_sgs=client_ec2.describe_security_groups(
		Filters=[
		{
			'Name': 'ip-permission.cidr',
			'Values': [fCIDRRange]
		}  ]
	)
	return (open_sgs)
