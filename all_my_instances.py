#!/usr/bin/env python3

import sys
import Inventory_Modules
from Inventory_Modules import get_credentials_for_accounts_in_org, display_results
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore
from botocore.exceptions import ClientError
from queue import Queue
from threading import Thread
from time import time

import logging

init()
__version__ = "2023.11.06"

# TODO: Need a table at the bottom that summarizes the results, by instance-type, by running/ stopped, maybe by account and region
##################
def parse_args(args):
	"""
	Description: Parses the arguments passed into the script
	@param args: args represents the list of arguments passed in
	@return: returns an object namespace that contains the individualized parameters passed in
	"""
	parser = CommonArguments()
	parser.my_parser.description = ("We're going to find all instances within any of the accounts we have access to, given the profile(s) provided.")
	parser.multiprofile()
	parser.multiregion()
	parser.extendedargs()
	parser.rootOnly()
	parser.timing()
	parser.verbosity()
	parser.version(__version__)
	parser.my_parser.add_argument(
		"-s", "--status",
		dest="pStatus",
		choices=['running', 'stopped'],
		type=str,
		default=None,
		help="Whether you want to limit the instances returned to either 'running', 'stopped'. Default is both")
	return(parser.my_parser.parse_args(args))

def get_credentials(fProfile_list:list, fRegion_list:list)->list:
	"""
	Description: Finds all the credentials for the member accounts within the profile you've specified
	@param fProfile_list: Profile of an Org account
	@param fRegion_list: Regions to look within
	@return: list of all credentials
	"""
	AllCredentials = []
	if fProfile_list is None:  # Default use case from the classes
		print("Using the default profile - gathering info")
		aws_acct = aws_acct_access()
		RegionList = Inventory_Modules.get_regions3(aws_acct, fRegion_list)
		# This should populate the list "AllCreds" with the credentials for the relevant accounts.
		logging.info(f"Queueing default profile for credentials")
		profile = 'default'
		AllCredentials.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList, fTiming=pTiming))
	else:
		ProfileList = Inventory_Modules.get_profiles(fSkipProfiles=pSkipProfiles, fprofiles=fProfile_list)
		print(f"Capturing info for {len(ProfileList)} requested profiles {ProfileList}")
		for profile in ProfileList:
			# Eventually - getting credentials for a single account may require passing in the region in which it's valid, but not yet.
			try:
				aws_acct = aws_acct_access(profile)
				print(f"Validating {len(aws_acct.ChildAccounts)} accounts within {profile} profile now... ")
				RegionList = Inventory_Modules.get_regions3(aws_acct, fRegion_list)
				logging.info(f"Queueing {profile} for credentials")
				# This should populate the list "AllCredentials" with the credentials for the relevant accounts.
				AllCredentials.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList, fTiming=pTiming))
				print()
			except AttributeError as my_Error:
				logging.error(f"Profile {profile} didn't work... Skipping")
				continue
	return(AllCredentials)

# The parameters passed to this function should be the dictionary of attributes that will be examined within the thread.
def find_all_instances(fAllCredentials:list, fStatus:str=None) -> list:
	"""
	Description: Finds all the instances from all the accounts/ regions within the Credentials supplied
	@param fAllCredentials: list of all credentials for all member accounts supplied
	@param fStatus: string determining whether you're looking for "running" or "stopped" instances
	@return: Returns a list of Instances
	"""
	# This function is called
	class FindInstances(Thread):

		def __init__(self, queue):
			Thread.__init__(self)
			self.queue = queue

		def run(self):
			while True:
				# Get the work from the queue and expand the tuple
				c_account_credentials, c_PlaceCount = self.queue.get()
				logging.info(f"De-queued info for account number {c_account_credentials['AccountId']}")
				try:
					# Now go through those stacksets and determine the instances, made up of accounts and regions
					# Most time spent in this loop
					# for i in range(len(fStackSetNames['StackSets'])):
					# print(f"{ERASE_LINE}Checking account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']}", end='\r')
					Instances = Inventory_Modules.find_account_instances2(c_account_credentials, c_account_credentials['Region'])
					logging.info(f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(Instances['Reservations'])} instances")
					State = InstanceType = InstanceId = PublicDnsName = Name = ""
					if 'Reservations' in Instances.keys():
						for y in range(len(Instances['Reservations'])):
							for z in range(len(Instances['Reservations'][y]['Instances'])):
								InstanceType = Instances['Reservations'][y]['Instances'][z]['InstanceType']
								InstanceId = Instances['Reservations'][y]['Instances'][z]['InstanceId']
								PublicDnsName = Instances['Reservations'][y]['Instances'][z]['PublicDnsName']
								State = Instances['Reservations'][y]['Instances'][z]['State']['Name']
								Name = "No Name Tag"
								try:
									for x in range(len(Instances['Reservations'][y]['Instances'][z]['Tags'])):
										if Instances['Reservations'][y]['Instances'][z]['Tags'][x]['Key'] == "Name":
											Name = Instances['Reservations'][y]['Instances'][z]['Tags'][x]['Value']
								except KeyError as my_Error:  # This is needed for when there is no "Tags" key within the describe-instances output
									logging.info(my_Error)
									pass
								if fStatus is None or fStatus == State:
									AllInstances.append({'MgmtAccount'  : c_account_credentials['MgmtAccount'],
									                     'AccountId'    : c_account_credentials['AccountId'],
									                     'Region'       : c_account_credentials['Region'],
									                     'State'        : State,
									                     'InstanceType' : InstanceType,
									                     'InstanceId'   : InstanceId,
									                     'PublicDNSName': PublicDnsName,
									                     'ParentProfile': c_account_credentials['ParentProfile'],
									                     'Name'         : Name, })
								else:
									continue
				except KeyError as my_Error:
					logging.error(f"Account Access failed - trying to access {c_account_credentials['AccountId']}")
					logging.info(f"Actual Error: {my_Error}")
					pass
				except AttributeError as my_Error:
					logging.error(f"Error: Likely that one of the supplied profiles was wrong")
					logging.warning(my_Error)
					continue
				except ClientError as my_Error:
					if str(my_Error).find("AuthFailure") > 0:
						logging.error(f"Authorization Failure accessing account {c_account_credentials['AccountId']} in {c_account_credentials['Region']} region")
						logging.warning(f"It's possible that the region {c_account_credentials['Region']} hasn't been opted-into")
						continue
					else:
						logging.error(f"Error: Likely throttling errors from too much activity")
						logging.warning(my_Error)
						continue
				finally:
					# print(f"{ERASE_LINE}Finished finding instances in account {c_account_credentials['AccountId']} in region {c_account_credentials['Region']} - {c_PlaceCount} / {len(AllCredentials)}", end='\r')
					print(".", end='')
					self.queue.task_done()

	###########

	checkqueue = Queue()

	AllInstances = []
	PlaceCount = 0
	WorkerThreads = min(len(fAllCredentials), 25)

	for x in range(WorkerThreads):
		worker = FindInstances(checkqueue)
		# Setting daemon to True will let the main thread exit even though the workers are blocking
		worker.daemon = True
		worker.start()

	for credential in fAllCredentials:
		logging.info(f"Beginning to queue data - starting with {credential['AccountId']}")
		try:
			# I don't know why - but double parens are necessary below. If you remove them, only the first parameter is queued.
			checkqueue.put((credential, PlaceCount))
			PlaceCount += 1
		except ClientError as my_Error:
			if str(my_Error).find("AuthFailure") > 0:
				logging.error(f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region")
				logging.warning(f"It's possible that the region {credential['Region']} hasn't been opted-into")
				pass
	checkqueue.join()
	return (AllInstances)

##################

if __name__ == '__main__':
	args = parse_args(sys.argv[1:])
	pProfiles = args.Profiles
	pRegionList = args.Regions
	pAccounts = args.Accounts
	pSkipAccounts = args.SkipAccounts
	pSkipProfiles = args.SkipProfiles
	pStatus = args.pStatus
	pRootOnly = args.RootOnly
	pTiming = args.Time
	verbose = args.loglevel
	logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

	ERASE_LINE = '\x1b[2K'
	logging.info(f"Profiles: {pProfiles}")
	begin_time = time()

	print()
	print(f"Checking for instances... ")
	print()

	# Find credentials for all Child Accounts
	CredentialList = get_credentials(pProfiles, pRegionList)
	# OrgNum = len(set([x['MgmtAccount'] for x in AllCredentials if x['OrgType'] == 'Root']))
	AccountNum = len(set([acct['AccountId'] for acct in CredentialList]))
	RegionNum = len(set([acct['Region'] for acct in CredentialList]))
	print()
	print(f"Searching total of {AccountNum} accounts and {RegionNum} regions")
	if pTiming:
		print()
		milestone_time1 = time()
		print(f"{Fore.GREEN}\t\tFiguring out what regions are available to your accounts, and capturing credentials for all accounts in those regions took: {(milestone_time1 - begin_time):.3f} seconds{Fore.RESET}")
		print()
	print(f"Now running through all accounts and regions identified to find resources...")
	# Collect all the instances from the credentials found
	AllInstances = find_all_instances(CredentialList, pStatus)
	# Display the information we've found thus far
	display_dict = {'ParentProfile': {'DisplayOrder': 1, 'Heading': 'Parent Profile'},
	                'MgmtAccount'  : {'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
	                'AccountId'    : {'DisplayOrder': 3, 'Heading': 'Acct Number'},
	                'Region'       : {'DisplayOrder': 4, 'Heading': 'Region'},
	                'InstanceType' : {'DisplayOrder': 5, 'Heading': 'Instance Type'},
	                'Name'         : {'DisplayOrder': 6, 'Heading': 'Name'},
	                'InstanceId'   : {'DisplayOrder': 7, 'Heading': 'Instance ID'},
	                'PublicDNSName': {'DisplayOrder': 8, 'Heading': 'Public Name'},
	                'State'        : {'DisplayOrder': 9, 'Heading': 'State', 'Condition': ['running']}}

	sorted_all_instances = sorted(AllInstances, key=lambda d: (d['ParentProfile'], d['MgmtAccount'], d['Region'], d['AccountId']))
	display_results(sorted_all_instances, display_dict)

	if pTiming:
		print(ERASE_LINE)
		print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
	print(ERASE_LINE)

	print(f"Found {len(AllInstances)} instances across {AccountNum} accounts across {RegionNum} regions")
	print()
	print("Thank you for using this script")
	print()
