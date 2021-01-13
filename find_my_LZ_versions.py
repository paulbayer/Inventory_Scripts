#!/usr/local/bin/python3

import os, sys, pprint, datetime
import Inventory_Modules
import argparse, boto3
from colorama import init,Fore,Back,Style
from botocore.exceptions import ClientError, NoCredentialsError

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
	help="Must specify a root profile. Default will be the default profile")
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



print()
fmt='%-20s %-15s %-21s'
print(fmt % ("Account","ALZ Stack Name","ALZ Version"))
print(fmt % ("-------","--------------","-----------"))

accountnum=Inventory_Modules.find_account_number(pProfile)

aws_session=boto3.Session(profile_name=pProfile)
aws_client=aws_session.client('cloudformation')

stack_list=aws_client.describe_stacks()['Stacks']

for i in range(len(stack_list)):
	print(ERASE_LINE+"Checking stack {}".format(stack_list[i]['StackName']),end='\r')
	if 'Description' in stack_list[i].keys() and stack_list[i]['Description'].find("SO0044") > 0:
		print(fmt % (accountnum, stack_list[i]['StackName'],stack_list[i]['Outputs'][1]['OutputValue']))


print(ERASE_LINE)
print()
print("Thank you for using this script.")
