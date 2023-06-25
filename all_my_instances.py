#!/usr/bin/env python3

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
__version__ = "2023.05.10"

parser = CommonArguments()
parser.multiprofile()
parser.multiregion()
parser.extendedargs()
parser.rootOnly()
parser.timing()
parser.verbosity()
parser.version(__version__)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pAccounts = args.Accounts
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pRootOnly = args.RootOnly
pTiming = args.Time
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

##################


ERASE_LINE = '\x1b[2K'

logging.info(f"Profiles: {pProfiles}")

if pTiming:
	begin_time = time()


##################

def display_results_old(results_list, fdisplay_dict, defaultAction=None):
	"""
	Note that this function simply formats the output of the data within the list provided
	- results_list: This should be a list of dictionaries, matching to the fields in fdisplay_dict
	- fdisplay_dict: Should look like the below. It's simply a list of fields and formats
	- defaultAction: this is a default string or type to assign to fields that (for some reason) don't exist within the results_list.
	display_dict = {'ParentProfile': {'Format': '20s', 'DisplayOrder': 1, 'Heading': 'Parent Profile'},
	                'MgmtAccount'  : {'Format': '12s', 'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
	                'AccountId'    : {'Format': '12s', 'DisplayOrder': 3, 'Heading': 'Acct Number'},
	                'Region'       : {'Format': '15s', 'DisplayOrder': 4, 'Heading': 'Region'},
	                'InstanceType' : {'Format': '15s', 'DisplayOrder': 5, 'Heading': 'Instance Type'},
	                'Name'         : {'Format': '40s', 'DisplayOrder': 6, 'Heading': 'Name'},
	                'InstanceId'   : {'Format': '40s', 'DisplayOrder': 7, 'Heading': 'Instance ID'},
	                'PublicDNSName': {'Format': '62s', 'DisplayOrder': 8, 'Heading': 'Public Name'},
	                'State'        : {'Format': '12s', 'DisplayOrder': 9, 'Heading': 'State', 'Condition': ['running']}}
		- The first field ("MgmtAccount") should match the field name within the list of dictionaries you're passing in (results_list)
		- The first field within the nested dictionary is the format you want to use to display the result of that field - generally a width
		- The second field within the nested dictionary is the SortOrder you want the results to show up in
		- The third field within the nested dictionary is the heading you want to display at the top of the column (which allows spaces)
		- The fourth field ('Condition') is new, and allows to highlight a special value within the output. This can be used multiple times.
		The dictionary doesn't have to be ordered, as long as the 'SortOrder' field is correct.
	"""
	# TODO:
	# 	Probably have to do a pre-emptive error-check to ensure the SortOrder is unique within the Dictionary
	# 	Also need to enclose this whole thing in a try...except to trap errors.
	# 	Also need to find a way to order the data within this function.

	sorted_display_dict = dict(sorted(fdisplay_dict.items(), key=lambda x: x[1]['DisplayOrder']))

	# This is an effort to find the right size spaces for the dictionary
	print()
	needed_space = {}
	for field, value in sorted_display_dict.items():
		needed_space[field] = 0
	for result in results_list:
		for field, value in sorted_display_dict.items():
			needed_space[field] = max(min(int(value['Format'][:-1]), len(result[field])),len(value['Heading']), needed_space[field])
		# 	logging.debug(f"Heading: {value['Heading']} | Format Size: {value['Format']} | Data Length: {result[field]}({len(result[field])}) | space: {needed_space[field]}")
		# logging.debug('---------')

	# This writes out the headings
	for field, value in sorted_display_dict.items():
		header_format = needed_space[field]
		print(f"{value['Heading']:{header_format}s} ", end='')
	print()
	# This writes out the dashes (separators)
	for field, value in sorted_display_dict.items():
		repeatvalue = needed_space[field]
		print(f"{'-' * repeatvalue} ", end='')
	print()

	# This writes out the data
	for result in results_list:
		for field, value in sorted_display_dict.items():
			# This assigns the proper space for the output
			data_format = needed_space[field]
			if field not in result.keys():
				result[field] = defaultAction
			# This allows for a condition to highlight a specific value
			if 'Condition' in value and result[field] in value['Condition']:
				print(f"{Fore.RED}{result[field]:{data_format}{value['Format'][-1:]}}{Fore.RESET} ", end='')
			elif result[field] is None:
				print(f"{'':{data_format}} ", end='')
			else:
				print(f"{result[field]:{data_format}{value['Format'][-1:]}} ", end='')
		print()  # This is the end of line character needed at the end of every line
	print()  # This is the new line needed at the end of the script.


# The parameters passed to this function should be the dictionary of attributes that will be examined within the thread.
def find_all_instances(fAllCredentials):
	"""
	Note that this function takes a list of stack set names and finds the stack instances within them

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
								# if State == 'running':
								# 	fmt = f"%-12s %-12s %-10s %-15s %-20s %-20s %-42s {Fore.RED}%-12s{Fore.RESET}"
								# else:
								# 	fmt = '%-12s %-12s %-10s %-15s %-20s %-20s %-42s %-12s'
								# print(fmt % (
								# 	c_account_credentials['MgmtAccount'], c_account_credentials['AccountId'], c_region, InstanceType, Name, InstanceId,
								# 	PublicDnsName, State))
								AllInstances.append({'MgmtAccount'  : c_account_credentials['MgmtAccount'],
								                     'AccountId'    : c_account_credentials['AccountId'],
								                     'Region'       : c_account_credentials['Region'],
								                     'State'        : State,
								                     'InstanceType' : InstanceType,
								                     'InstanceId'   : InstanceId,
								                     'PublicDNSName': PublicDnsName,
								                     'ParentProfile': c_account_credentials['ParentProfile'],
								                     'Name'         : Name, })
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
		# for region in fRegionList:
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


print()
print(f"Checking for instances... ")
print()

print()

AllInstances = []
AllCredentials = []
RegionList = ['us-east-1']

if pProfiles is None:  # Default use case from the classes
	print("Using the default profile - gathering info")
	aws_acct = aws_acct_access()
	RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
	# This should populate the list "AllCreds" with the credentials for the relevant accounts.
	logging.info(f"Queueing default profile for credentials")
	profile = 'default'
	AllCredentials.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList, fTiming=pTiming))
else:
	ProfileList = Inventory_Modules.get_profiles(fSkipProfiles=pSkipProfiles, fprofiles=pProfiles)
	print(f"Capturing info for {len(ProfileList)} requested profiles {ProfileList}")
	for profile in ProfileList:
		# Eventually - getting credentials for a single account may require passing in the region in which it's valid, but not yet.
		try:
			aws_acct = aws_acct_access(profile)
			print(f"Validating {len(aws_acct.ChildAccounts)} accounts within {profile} profile now... ")
			RegionList = Inventory_Modules.get_regions3(aws_acct, pRegionList)
			logging.info(f"Queueing {profile} for credentials")
			# This should populate the list "AllCredentials" with the credentials for the relevant accounts.
			AllCredentials.extend(get_credentials_for_accounts_in_org(aws_acct, pSkipAccounts, pRootOnly, pAccounts, profile, RegionList, fTiming=pTiming))
			print()
		except AttributeError as my_Error:
			logging.error(f"Profile {profile} didn't work... Skipping")
			continue

# OrgNum = len(set([x['MgmtAccount'] for x in AllCredentials if x['OrgType'] == 'Root']))
AccountNum = len(set([acct['AccountId'] for acct in AllCredentials]))

cf_regions = Inventory_Modules.get_service_regions('config', RegionList)
print()
print(f"Searching total of {AccountNum} accounts and {len(cf_regions)} regions")
if pTiming:
	print()
	milestone_time1 = time()
	print(f"{Fore.GREEN}\t\tFiguring out what regions are available to your accounts, and capturing credentials for all accounts in those regions took: {(milestone_time1 - begin_time):.3f} seconds{Fore.RESET}")
	print()
print(f"Now running through all accounts and regions identified to find resources...")

display_dict = {'ParentProfile': {'Format': '20s', 'DisplayOrder': 1, 'Heading': 'Parent Profile'},
                'MgmtAccount'  : {'Format': '12s', 'DisplayOrder': 2, 'Heading': 'Mgmt Acct'},
                'AccountId'    : {'Format': '12s', 'DisplayOrder': 3, 'Heading': 'Acct Number'},
                'Region'       : {'Format': '15s', 'DisplayOrder': 4, 'Heading': 'Region'},
                'InstanceType' : {'Format': '15s', 'DisplayOrder': 5, 'Heading': 'Instance Type'},
                'Name'         : {'Format': '40s', 'DisplayOrder': 6, 'Heading': 'Name'},
                'InstanceId'   : {'Format': '40s', 'DisplayOrder': 7, 'Heading': 'Instance ID'},
                'PublicDNSName': {'Format': '62s', 'DisplayOrder': 8, 'Heading': 'Public Name'},
                'State'        : {'Format': '12s', 'DisplayOrder': 9, 'Heading': 'State', 'Condition': ['running']}}

AllInstances = find_all_instances(AllCredentials)
sorted_all_instances = sorted(AllInstances, key=lambda d: (d['ParentProfile'], d['MgmtAccount'], d['Region'], d['AccountId']))
# display_instances(AllInstances)

display_results(sorted_all_instances, display_dict)

if pTiming:
	print(ERASE_LINE)
	print(f"{Fore.GREEN}This script took {time() - begin_time:.2f} seconds{Fore.RESET}")
print(ERASE_LINE)

print(f"Found {len(AllInstances)} instances across {AccountNum} accounts across {len(RegionList)} regions")
print()
print("Thank you for using this script")
print()
