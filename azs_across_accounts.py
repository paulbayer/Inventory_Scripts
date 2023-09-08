#!/usr/bin/env python3

import logging
from ArgumentsClass import CommonArguments
# from account_class import aws_acct_access
import Inventory_Modules
from Inventory_Modules import get_org_accounts_from_profiles, display_results, get_all_credentials, get_region_azs2
from time import time
# from botocore.exceptions import ClientError, NoCredentialsError, InvalidConfigError
from colorama import init, Fore, Style
import sys

init()
__version__ = "2023.09.01"
ERASE_LINE = '\x1b[2K'


def parse_args(args):
	parser = CommonArguments()
	parser.multiprofile()
	parser.multiregion()
	parser.extendedargs()
	parser.rootOnly()
	parser.timing()
	parser.save_to_file()
	parser.rolestouse()
	parser.verbosity()
	parser.version(__version__)
	return parser.my_parser.parse_args(args)


"""
TODO:
	If they provide a profile that isn't a root profile, you should find out which org it belongs to, 
	and then show the org for that. 
	This will be difficult, since we don't know which profile that belongs to. Hmmm...
"""


##################

def azs_across_accounts(fProfiles, fRegionList, fSkipProfiles, fSkipAccounts, fAccountList, fTiming, fRootOnly, fverbose, fRoleList):
	if fTiming:
		begin_time = time()
	logging.warning(f"These profiles are being checked {fProfiles}.")
	AllCredentials = get_all_credentials(fProfiles, fTiming, fSkipProfiles, fSkipAccounts, fRootOnly, fAccountList, fRegionList, fRoleList)
	OrgList = list(set([x['MgmtAccount'] for x in AllCredentials]))
	print(f"Please bear with us as we run through {len(OrgList)} organizations / standalone accounts")

	print(ERASE_LINE)

	AllOrgAZs = []
	SuccessfulCredentials = [x for x in AllCredentials if x['Success']]
	passnumber = 0
	for item in SuccessfulCredentials:
		passnumber +=1
		if item['Success']:
			region_azs = get_region_azs2(item)
			print(f"{ERASE_LINE}Looking at account {item['AccountNumber']} in region {item['Region']} -- {passnumber}/{len(SuccessfulCredentials)}", end='\r')
		AllOrgAZs.append(region_azs)

	print()
	if fTiming:
		print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
	print("Thanks for using this script")
	print()
	return (AllOrgAZs)


if __name__ == '__main__':
	args = parse_args(sys.argv[1:])

	pProfiles = args.Profiles
	pRegions = args.Regions
	pRootOnly = args.RootOnly
	pTiming = args.Time
	pSkipProfiles = args.SkipProfiles
	pSkipAccounts = args.SkipAccounts
	pverbose = args.loglevel
	pSaveFilename = args.Filename
	pAccountList = args.Accounts
	pRoleList = args.AccessRoles
	logging.basicConfig(level=pverbose, format="[%(filename)s:%(lineno)s - %(processName)s %(threadName)s %(funcName)20s() ] %(message)s")

	print(f"Collecting credentials for all accounts in your org, across multiple regions")
	AllOrgAZs = azs_across_accounts(pProfiles, pRegions, pSkipProfiles, pSkipAccounts, pAccountList, pTiming, pRootOnly, pverbose, pRoleList)
	histogram = list()
	for account in AllOrgAZs:
		for az in account:
			if az['ZoneType'] == 'availability-zone':
				print(az)
				histogram.append({'Region': az['Region'], 'Name': az['ZoneName'], 'Id': az['ZoneId']})

	histogram_sorted = sorted(histogram, key=lambda k: (k['Region'], k['Name'], k['Id']))
	summary = dict()
	for item in histogram_sorted:
		if item['Region'] not in summary.keys():
			summary[item['Region']] = dict()
		if item['Name'] not in summary[item['Region']].keys():
			summary[item['Region']][item['Name']] = list()
		summary[item['Region']][item['Name']].append(item['Id'])

	# display_dict = {'MgmtAccount': {'DisplayOrder': 1, 'Heading': 'Parent Acct'},
	#                 'AccountId'  : {'DisplayOrder': 2, 'Heading': 'Account Number'},
	#                 'Region'     : {'DisplayOrder': 3, 'Heading': 'Region Name'},
	#                 'ZoneName'   : {'DisplayOrder': 4, 'Heading': 'Zone Name'},
	#                 'ZoneId'     : {'DisplayOrder': 5, 'Heading': 'Zone Id'},
	#                 'ZoneType'   : {'DisplayOrder': 6, 'Heading': 'Zone Type'}}
	# sorted_Results = sorted(summary, key=lambda d: (d['MgmtAccount'], d['AccountId'], d['Region']))
	# display_results(sorted_Results, display_dict, "None", pSaveFilename)
