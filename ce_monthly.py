import boto3
from datetime import datetime, timedelta
from time import time
from dateutil.relativedelta import relativedelta

import Inventory_Modules
from Inventory_Modules import display_results, get_all_credentials
from ArgumentsClass import CommonArguments
from colorama import init, Fore, Style, Back
from prettytable import PrettyTable
import logging

init()

__script_version__ = '2023-04-17'

parser = CommonArguments()
parser.my_parser.description = ("We're going to find all roles within any of the accounts we have access to, given the profile provided.")
parser.multiprofile()
parser.multiregion_nodefault()
parser.extendedargs()  # This adds the "DryRun" and "Force" objects
parser.rootOnly()
parser.verbosity()
parser.timing()
parser.version(__script_version__)
parser.my_parser.add_argument(
	"--back", "--from", "--start",
	help="How many months back to look for costs",
	dest="months_back",
	default=1
)
parser.my_parser.add_argument(
	"--group_by",
	help="How should the results be grouped?",
	dest="group_by",
	choices=['service_and_account', 'service_and_region', 'account_and_region'],
	default="service_and_account"
)
parser.my_parser.add_argument(
	"--aggregate", "-A",
	help="Should the child accounts be shown?",
	dest="aggregated",
	action="store_true",
)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRegionList = args.Regions
pTiming = args.Time
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pAccounts = args.Accounts
pRootOnly = args.RootOnly
pMonths_back = args.months_back
pGroupBy = args.group_by
pAggregate = args.aggregated
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(""message)s")
###########################

if pTiming:
	begin_time = time()
"""
Figure out which accounts we're getting cost explorer information for
"""
ProfileList = Inventory_Modules.get_profiles(pSkipProfiles, pProfiles)
AllCredentials = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)
RegionList = list(set([x['Region'] for x in AllCredentials if x['Success']])) if pRegionList is not None else None
if pAccounts is not None:
	# This indicates that we only want data for the specified account numbers
	AccountList = list(set([x['AccountId'] for x in AllCredentials if x['Success']]))
elif pRootOnly:
	# This indicates that we only want data for the ROOT accounts - which should imply an aggregation of the child accounts too.
	# Because otherwise, they would have specified only the root account number at the command line.
	AccountList = list(set([x['AccountId'] for x in AllCredentials if x['Success'] and x['MgmtAccount'] == x['AccountId']]))
else:  # This would indicate that they want broken out costs for all accounts within the profile(s) specified.
	AccountList = None

print()
print(f"Showing Cost Explorer data for: ", end='')
# TODO: Update this to represent whether it's RootOnly, Specific Accounts, Consolidated or Broken out
print(f"\t* {len(AccountList)} {'accounts' if len(AccountList) != 1 else 'account'}") if AccountList is not None else print("all accounts ", end='')
print(f"\t* {len(RegionList)} {'regions' if len(RegionList) != 1 else 'region'}") if RegionList is not None else print("all regions")

if verbose < 50:
	print(f"\t\tAccounts: {AccountList}")
	print(f"\t\tRegions: {RegionList}")

#################################

# Initialize the Metric Parameters

now = datetime.now()
# Define the start and end dates for the cost lookups
start_date = (now - relativedelta(months=int(pMonths_back)) - timedelta(days=now.day - 1)).strftime('%Y-%m-%d')
end_date = now.strftime('%Y-%m-%d')
# Define the time period for the cost query
time_period = {
	'Start': start_date,
	'End'  : end_date
}

filter_enabled = False
# Defining the AccountList filter to be used, in case the user provided one
if AccountList is not None:
	my_filter = my_accounts_filter = {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': AccountList}}
	filter_enabled = True

# Defining the Regions filter to be used, in case the user provided one
if RegionList is not None:
	my_filter = my_regions_filter = {'Dimensions': {'Key': 'REGION', 'Values': RegionList}}
	filter_enabled = True

# Combining the Regions and Accounts filter together
if AccountList is not None and RegionList is not None:
	my_filter = {'And': [my_accounts_filter, my_regions_filter]}

# Define the granularity for the cost query (MONTHLY)
granularity = 'MONTHLY'
metric = 'NetUnblendedCost'

# Define the group by parameter to group costs by 'SERVICE' (optional)
group_by_service_and_account = [
	{
		'Type': 'DIMENSION',
		'Key' : 'SERVICE'
	}, {
		'Type': 'DIMENSION',
		'Key' : 'LINKED_ACCOUNT'
	}
]
group_by_service_and_region = [
	{
		'Type': 'DIMENSION',
		'Key' : 'SERVICE'
	}, {
		'Type': 'DIMENSION',
		'Key' : 'REGION'
	}
]
group_by_account_and_region = [
	{
		'Type': 'DIMENSION',
		'Key' : 'LINKED_ACCOUNT'
	}, {
		'Type': 'DIMENSION',
		'Key' : 'REGION'
	}
]

x = PrettyTable()
y = PrettyTable()

if pGroupBy == 'account_and_region':
	group_by = group_by_account_and_region
	x.field_names = ['Month', 'Dimension', 'Region', 'Amount']
	y.field_names = ['Start', 'End', 'Account', 'Region', 'Amount']
elif pGroupBy == 'service_and_region':
	group_by = group_by_service_and_region
	x.field_names = ['Month', 'Dimension', 'Region', 'Amount']
	y.field_names = ['Start', 'End', 'Service', 'Region', 'Amount']
else:
	group_by = group_by_service_and_account
	x.field_names = ['Month', 'Account', 'Region', 'Amount']
	y.field_names = ['Start', 'End', 'Account', 'Service', 'Amount']

ce_metrics = {
	'time_period': time_period,
	'granularity': granularity,
	'group_by'   : group_by,
	'metric'     : metric,
	'my_filter'  : my_filter
}


#################################
def get_cost_explorer_data(fcredentials, fce_metrics, faggregated):
	# Create a Cost Explorer client
	ce_session = boto3.Session(aws_access_key_id=fcredentials['AccessKeyId'],
	                           aws_secret_access_key=fcredentials['SecretAccessKey'],
	                           aws_session_token=fcredentials['SessionToken'],
	                           region_name=fcredentials['Region'])
	ce_client = ce_session.client('ce')

	if fce_metrics['filter_enabled']:
		ce_response = ce_client.get_cost_and_usage(
			TimePeriod=fce_metrics['time_period'],
			Granularity=fce_metrics['granularity'],
			GroupBy=fce_metrics['group_by'],
			Metrics=[fce_metrics['metric']],
			Filter=fce_metrics['my_filter']
		)
	else:
		ce_response = ce_client.get_cost_and_usage(
			TimePeriod=fce_metrics['time_period'],
			Granularity=fce_metrics['granularity'],
			GroupBy=fce_metrics['group_by'],
			Metrics=[fce_metrics['metric']]
		)
	return (ce_response)


#################################
Costs = dict()

for credential in AllCredentials:
	response = get_cost_explorer_data(credential, ce_metrics)
	for result in response['ResultsByTime']:
		print()
		# print(f"{'Start':12s} {'End':12s} {response['GroupDefinitions'][1]['Key']:13s} {'Region':12s}{response['GroupDefinitions'][0]['Key']:40s} {'Amount':8s}")
		# print(f"{'-' * 12} {'-' * 12} {'-' * 13} {'-' * 12} {'-' * 40} {'-' * 8}")
		for service_item in result['Groups']:
			month = datetime.strptime(result['TimePeriod']['Start'], "%Y-%m-%d").strftime('%Y-%B')
			amount = round(float(service_item['Metrics'][metric]['Amount']), 2)
			unit = service_item['Metrics'][metric]['Unit']
			service = service_item['Keys'][0]
			service_key = service.replace(' ', '_')
			account = service_item['Keys'][1]
			region = ""
			if RegionList is None:
				region = 'all'
			elif len(RegionList) == 1:
				region = RegionList[0]
			elif len(RegionList) > 1:
				region = "multiple"
			# print(f'{service}, Cost: {amount} {unit}')
			y.add_row([result['TimePeriod']['Start'], result['TimePeriod']['End'], account, service, amount])
			# print(f"{result['TimePeriod']['Start']:12s} {result['TimePeriod']['End']:12s} {account:13s} {region:12s} {service:40s} {amount:0.3f}")
			if month not in Costs:
				Costs[month] = dict()
			if account not in Costs[month]:
				Costs[month][account] = dict()
			Costs[month][account][service_key] = amount

for month_k, month_v in Costs.items():
	month_total = 0
	if month_k == 'Total':
		continue
	for account_k, account_v in month_v.items():
		if account_k == 'Total':
			continue
		account_total = 0
		for service_item in account_v:
			account_total += account_v[service_item]
		Costs[month_k][account_k]['Total'] = account_total
		month_total += account_total
		x.add_row([month_k, account_k, region, round(account_total, 2)])
	Costs[month_k]['Total'] = month_total
	x.add_row([f"{Back.RED}{Fore.WHITE}{month_k}", 'Total', region, f"{round(month_total, 2)}{Style.RESET_ALL}"])

print()
print(x)
print()
if pTiming:
	print(f"{Fore.GREEN}\tThis script took {time() - begin_time} seconds{Fore.RESET}")
	print()
print("Done")
