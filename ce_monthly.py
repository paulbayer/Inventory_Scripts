import boto3
from datetime import datetime, timedelta
from time import time
from dateutil.relativedelta import relativedelta
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
verbose = args.loglevel
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(""message)s")
###########################

if pTiming:
	begin_time = time()

ChildAccounts = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)
RegionList = list(set([x['Region'] for x in ChildAccounts if x['Success']])) if pRegionList is not None else None
if pAccounts is not None:
	AccountList = list(set([x['AccountId'] for x in ChildAccounts if x['Success']]))
elif pRootOnly:
	AccountList = list(set([x['AccountId'] for x in ChildAccounts if x['Success'] and x['MgmtAccount'] == x['AccountId']]))
else:
	AccountList = None

print()
print(f"Showing Cost Explorer data for: ", end='')
print(f"{len(AccountList)} {'accounts' if len(AccountList) != 1 else 'account'}") if AccountList is not None else print("all accounts", end='')
print(f"{len(RegionList)} {'regions' if len(RegionList) != 1 else 'region'}") if RegionList is not None else print("all regions")

if verbose < 50:
	print(f"\t\tAccounts: {AccountList}")
	print(f"\t\tRegions: {RegionList}")

# Create a Cost Explorer client
ce_session = boto3.Session(profile_name='LZRoot')
# ce_client = ce_session.client('ce', region_name='eu-west-1')
ce_client = ce_session.client('ce')

# Get the current month and year
now = datetime.now()
# Define the start and end dates for the cost lookups
start_date = (now - relativedelta(months=int(pMonths_back)) - timedelta(days=now.day - 1)).strftime('%Y-%m-%d')
end_date = now.strftime('%Y-%m-%d')
# current_month = now.strftime('%m')
# current_year = now.strftime('%Y')
# if int(current_month) == 1:
# 	last_month = 12
# last_month = f"{int(current_month) - 1:02d}"

filter_enabled = False
# Defining the filter to be used, in case the user provided one
if AccountList is not None:
	my_filter = my_accounts_filter = {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': AccountList}}
	filter_enabled = True

# Defining the filter to be used, in case the user provided one
if RegionList is not None:
	my_filter = my_regions_filter = {'Dimensions': {'Key': 'REGION', 'Values': RegionList}}
	filter_enabled = True

if AccountList is not None and RegionList is not None:
	my_filter = {'And': [my_accounts_filter, my_regions_filter]}

# Define the time period for the cost query
time_period = {
	'Start': start_date,
	'End'  : end_date
}

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
x.field_names = ['Month', 'Dimension', 'Region', 'Amount']

if pGroupBy == 'account_and_region':
	group_by = group_by_account_and_region
	x.field_names = ['Month', 'Dimension', 'Region', 'Amount']
elif pGroupBy == 'service_and_region':
	group_by = group_by_service_and_region
	x.field_names = ['Month', 'Dimension', 'Region', 'Amount']
else:
	group_by = group_by_service_and_account
	x.field_names = ['Month', 'Account', 'Region', 'Amount']

# Get the costs for the current month
if filter_enabled:
	response = ce_client.get_cost_and_usage(
		TimePeriod=time_period,
		Granularity=granularity,
		GroupBy=group_by,
		Metrics=[metric],
		Filter=my_filter
	)
else:
	response = ce_client.get_cost_and_usage(
		TimePeriod=time_period,
		Granularity=granularity,
		GroupBy=group_by,
		Metrics=[metric]
	)

# Print the costs for the current month
# print(f'Costs for {now.strftime("%B %Y")}:')
Costs = dict()

for result in response['ResultsByTime']:
	print()
	print(f"{'Start':12s} {'End':12s} {'Account':13s} {'Region':12s} {'Service':40s} {'Amount':8s}")
	print(f"{'-' * 12} {'-' * 12} {'-' * 13} {'-' * 12} {'-' * 40} {'-' * 8}")
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
		print(f"{result['TimePeriod']['Start']:12s} {result['TimePeriod']['End']:12s} {account:13s} {region:12s} {service:40s} {amount:0.3f}")
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
	x.add_row([f"{Back.RED}{Fore.BLACK}{month_k}", 'Total', region, f"{round(month_total, 2)}{Style.RESET_ALL}"])

print()
print(x)
print()
if pTiming:
	print(f"{Fore.GREEN}\tThis script took {time() - begin_time} seconds{Fore.RESET}")
	print()
print("Done")
