import boto3
from datetime import datetime
from Inventory_Modules import display_results, get_all_credentials
from ArgumentsClass import CommonArguments
from colorama import init, Fore

init()

__script_version__ = '2023-04-11'

parser = CommonArguments()
parser.my_parser.description = ("We're going to find all roles within any of the accounts we have access to, given the profile provided.")
parser.my_parser.add_argument(
	"--role",
	dest="pRole",
	metavar="specific role to find",
	default=None,
	help="Please specify the role you're searching for")
parser.my_parser.add_argument(
	"+d", "--delete",
	dest="pDelete",
	action="store_const",
	const=True,
	default=False,
	help="Whether you'd like to delete that specified role.")
parser.multiprofile()
parser.singleregion()
parser.extendedargs()  # This adds the "DryRun" and "Force" objects
parser.rootOnly()
parser.verbosity()
parser.timing()
parser.version(__script_version__)
args = parser.my_parser.parse_args()

pProfiles = args.Profiles
pRole = args.pRole
pDelete = args.pDelete
pRegionList = [args.Region]
pTiming = args.Time
pSkipAccounts = args.SkipAccounts
pSkipProfiles = args.SkipProfiles
pAccounts = args.Accounts
pForce = args.Force
pRootOnly = args.RootOnly
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(""message)s")
###########################

ChildAccounts = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList)


# Create a Cost Explorer client
ce_session = boto3.Session(profile_name='LZRoot')
# ce_client = ce_session.client('ce', region_name='eu-west-1')
ce_client = ce_session.client('ce')

# Get the current month and year
now = datetime.now()
current_month = now.strftime('%m')
last_month = f"{int(current_month) - 1:02d}"
current_year = now.strftime('%Y')

# Define the start and end dates for the current month
start_date = f'{current_year}-{last_month}-01'
end_date = f'{current_year}-{current_month}-{now.day}'

# Define the time period for the cost query
time_period = {
	'Start': start_date,
	'End'  : end_date
}

# Define the granularity for the cost query (MONTHLY)
granularity = 'MONTHLY'
metric = 'NetUnblendedCost'

# Define the group by parameter to group costs by 'SERVICE' (optional)
group_by = [
	{
		'Type': 'DIMENSION',
		'Key' : 'SERVICE'
	}, {
		'Type': 'DIMENSION',
		'Key' : 'LINKED_ACCOUNT'
	}
]

# Get the costs for the current month
response = ce_client.get_cost_and_usage(
	TimePeriod=time_period,
	Granularity=granularity,
	GroupBy=group_by,
	Metrics=[metric]
)

# Print the costs for the current month
print(f'Costs for {now.strftime("%B %Y")}:')
Costs = dict()
for result in response['ResultsByTime']:
	print()
	print(f"{'Start':12s} {'End':12s} {'Account':12s} {'Service':40s} {'Amount':8s}")
	print(f"{'-' * 12} {'-' * 12} {'-' * 12} {'-' * 40} {'-' * 8}")
	for service_item in result['Groups']:
		month = datetime.strptime(result['TimePeriod']['Start'], "%Y-%m-%d").strftime('%Y-%B')
		amount = round(float(service_item['Metrics'][metric]['Amount']),2)
		unit = service_item['Metrics'][metric]['Unit']
		service = service_item['Keys'][0]
		service_key = service.replace(' ', '_')
		account = service_item['Keys'][1]
		# print(f'{service}, Cost: {amount} {unit}')
		print(f"{result['TimePeriod']['Start']:12s} {result['TimePeriod']['End']:12s} {account:12s} {service:40s} {amount:0.3f}")
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
		Costs[month_k]['Total'] = month_total
print("Done")
