#!/usr/bin/env python3


import re
from datetime import timedelta, datetime, timezone
from time import time

from Inventory_Modules import display_results, get_all_credentials, find_ssm_parameters2
from colorama import init, Fore
# import boto3
from botocore.exceptions import ClientError
from ArgumentsClass import CommonArguments

import logging

init()
__version__ = "2023.06.22"

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
parser.rootOnly()
parser.timing()
parser.save_to_file()
parser.verbosity()
parser.version(__version__)

parser.my_parser.add_argument(
	'--ALZ',
	help="Identify left-over parameters created by the ALZ solution",
	action="store_const",
	dest="ALZParam",
	const=True,
	default=False)
parser.my_parser.add_argument(
	'-b', '--daysback',
	help="Only keep the last x days of Parameters (default 90)",
	dest="DaysBack",
	default=90)
parser.my_parser.add_argument(
	'+delete',
	help="Deletion is not working currently (as of 6/22/23)",
	# help="Delete left-over parameters created by the ALZ solution. DOES NOT DELETE ANY OTHER PARAMETERS!!",
	action="store_const",
	dest="DeletionRun",
	const=True,
	default=False)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pAccounts = args.Accounts
pRootOnly = args.RootOnly
ALZParam = args.ALZParam
pTiming = args.Time
pFilename = args.Filename
DeletionRun = args.DeletionRun
dtDaysBack = timedelta(days=int(args.DaysBack))
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

##########################
if pTiming:
	begin_time = time()
ERASE_LINE = '\x1b[2K'
ALZRegex = '/\w{8,8}-\w{4,4}-\w{4,4}-\w{4,4}-\w{12,12}/\w{3,3}'
print()

CredentialList = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts,pRootOnly, pAccounts, pRegionList)
RegionList = list(set([x['Region'] for x in CredentialList]))
AccountList = list(set([x['AccountId'] for x in CredentialList]))

Parameters = []
ParamsToDelete = []
ALZParams = 0

for credential in CredentialList:
	# TODO: Have to multi-thread this...
	try:
		# Since there could be 10,000 parameters stored in the Parameter Store - this function COULD take a long time
		# Consider making this a multi-threaded operation. Perhaps the library function would multi-thread it.
		print(f"Gathering parameters from account {credential['AccountNumber']} in region {credential['Region']}")
		Parameters.extend(find_ssm_parameters2(credential))
		if verbose < 50 or len(Parameters) == 0:
			print(f"Found a running total of {len(Parameters)} parameters in account {Fore.RED}{credential['AccountNumber']}{Fore.RESET} in region {Fore.RED}{credential['Region']}{Fore.RESET}")
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"Profile {credential['Profile']}: Authorization Failure for account {credential['AccountNumber']}")

display_dict = {'AccountNumber'   : {'DisplayOrder': 1, 'Heading': 'Acct Number'},
                'Region'          : {'DisplayOrder': 2, 'Heading': 'Region'},
                'Name'            : {'DisplayOrder': 3, 'Heading': 'Parameter Name'},
                'LastModifiedDate': {'DisplayOrder': 4, 'Heading': 'Last Modified'}}
sorted_Parameters = sorted(Parameters, key=lambda x: (x['AccountNumber'], x['Region'], x['Name']))
display_results(sorted_Parameters, display_dict, 'Default', pFilename)

if ALZParam:
	today = datetime.now(tz=timezone.utc)
	for y in range(len(Parameters)):
		# If the parameter matches the string regex of "/2ac07efd-153d-4069-b7ad-0d18cc398b11/105" - then it should be a candidate for deletion
		# With Regex - I'm looking for "/\w{8,8}-\w{4,4}-\w{4,4}-\w{4,4}-\w{12,12}/\w{3,3}"
		ParameterDate = Parameters[y]['LastModifiedDate']
		mydelta = today - ParameterDate  # this is a "timedelta" object
		p = re.compile(ALZRegex)  # Sets the regex to look for
		logging.info(f"Parameter{y}: {Parameters[y]['Name']} with date {Parameters[y]['LastModifiedDate']}")
		if p.match(Parameters[y]['Name']) and mydelta > dtDaysBack:
			logging.error(f"Parameter {Parameters[y]['Name']} with date of {Parameters[y]['LastModifiedDate']} matched")
			ALZParams += 1
			ParamsToDelete.append({'Credentials': Parameters[y]['credentials'],
			                      'Name': Parameters[y]['Name']})

if DeletionRun:
	print(f"Currently the deletion function for errored ALZ parameters isn't working. Please contact the author if this functionality is still needed for you... ")

	"""
	The reason this looks so weird, is that the SSM Parameters had to be deleted with a single API call, but the call could only take 10 parameters at a time, 
	so instead of multi-threading this deletion for one at a time (which would still have been a lot of work), I grouped the deletions to run 10 at a time. 
	However, that only worked when it was certain that the parameters found were all in the same account and the same region, to allow the API to run (one account / one region)
	So - since the update above allows this script to find parameters across accounts and regions. the deletion piece no longer works properly. 
	I can update it to figure a way to group the parameters by account and region, and then delete 10 at a time, but that's more work than I think is worthwhile, since I don't 
	think too many people are still using this script... Prove me wrong, and I'll write it...  
	"""

	# session_ssm = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'],
	#                             aws_secret_access_key=ocredentials['SecretAccessKey'],
	#                             aws_session_token=ocredentials['SessionToken'],
	#                             region_name=ocredentials['Region'])
	# client_ssm = session_ssm.client('ssm')
	# print(f"Deleting {len(ParamsToDelete)} ALZ-related Parameters now, further back than {dtDaysBack.days} days")
	# # for i in range(len(ParamsToDelete)):
	# mark = 0
	# i = 0
	# while i < len(ParamsToDelete) + 1:
	# 	i += 1
	# 	if i % 10 == 0:
	# 		response = client_ssm.delete_parameters(Names=ParamsToDelete[mark:i])
	# 		mark = i
	# 		print(ERASE_LINE, f"{i} parameters deleted and {len(ParamsToDelete) - i} more to go...", end='\r')
	# 	elif i == len(ParamsToDelete):
	# 		response = client_ssm.delete_parameters(Names=ParamsToDelete[mark:i])
	# 		logging.warning(f"Deleted the last {i % 10} parameters.")
print()
print(ERASE_LINE)
print(f"Found {len(Parameters)} total parameters")
if ALZParam:
	print(f"And {ALZParams} of them were from buggy ALZ runs more than {dtDaysBack.days} days back")
# if DeletionRun:
# 	print(f"And we deleted {len(ParamsToDelete)} of them")
if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
print()
print(f"These accounts were skipped - as requested: {pSkipAccounts}") if pSkipAccounts is not None else ""
print(f"These profiles were skipped - as requested: {pSkipProfiles}") if pSkipProfiles is not None else ""
print()
print(f"Found {len(Parameters)} SSM parameters across {len(AccountList)} account{'' if len(AccountList) == 1 else 's'} across {len(RegionList)} region{'' if len(RegionList) == 1 else 's'}")
print()
print("Thank you for using this script")
print(f"Your output was saved to {Fore.GREEN}'{pFilename}-{datetime.now().strftime('%y-%m-%d--%H:%M:%S')}'{Fore.RESET}") if pFilename is not None else ""
print()
