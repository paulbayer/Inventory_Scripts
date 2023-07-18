import boto3
import logging
from graphviz import Digraph
from time import time
from colorama import init, Fore
from ArgumentsClass import CommonArguments

__version__ = '2023.05.31'
init()

parser = CommonArguments()
parser.my_parser.description = ("To draw the Organization and its policies.")
parser.singleprofile()
parser.verbosity()
parser.timing()
parser.version(__version__)
parser.my_parser.add_argument(
	"--policy",
	dest='policy',
	action="store_true",  # Defaults to False, meaning it won't show policies by default
	help="Only run this code for the root account, not the children")
parser.my_parser.add_argument(
	"--aws", "--managed",
	dest='aws_managed',
	action="store_true",  # Defaults to False, meaning it defaults to NOT showing the AWS managed policies applied
	help="Use this parameter to SHOW the AWS Managed SCPs as well, otherwise they're hidden")
args = parser.my_parser.parse_args()

pProfile = args.Profile
pTiming = args.Time
pPolicy = args.policy
pManaged = args.aws_managed
verbose = args.loglevel
logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(""message)s")

# Create an AWS Organizations client
org_client = boto3.Session(profile_name=pProfile).client('organizations')
ERASE_LINE = '\x1b[2K'
if pTiming:
	begin_time = time()

root = org_client.list_roots()['Roots'][0]['Id']
account_fillcolor = 'orange'
account_shape = 'ellipse'
policy_fillcolor = 'azure'
policy_linecolor = 'red'
policy_shape = 'hexagon'
ou_fillcolor = 'burlywood'
ou_shape = 'box'

"""
Possible Org policy values as of 5/23/2023
AISERVICES_OPT_OUT_POLICY
BACKUP_POLICY
SERVICE_CONTROL_POLICY
TAG_POLICY
"""
aws_policy_type_list = ['SERVICE_CONTROL_POLICY', 'TAG_POLICY', 'BACKUP_POLICY', 'AISERVICES_OPT_OUT_POLICY']
#####################


def round_up(number):
	return int(number) + (number % 1 > 0)


def get_root_OUS(root_id):
	try:
		ChildOUs = org_client.list_children(ParentId=root_id, ChildType='ORGANIZATIONAL_UNIT')
		return (ChildOUs['Children'])
	except (org_client.exceptions.AccessDeniedException,
	        org_client.exceptions.AWSOrganizationsNotInUseException,
	        org_client.exceptions.InvalidInputException,
	        org_client.exceptions.ParentNotFoundException,
	        org_client.exceptions.ServiceException,
	        org_client.exceptions.TooManyRequestsException) as myError:
		logging.error(f"Error: {myError}")
	return ()


# Function to recursively traverse the OUs and accounts
def traverse_ous_and_accounts(ou_id, dot):
	# Retrieve the details of the current OU
	ou = org_client.describe_organizational_unit(OrganizationalUnitId=ou_id)
	ou_name = ou['OrganizationalUnit']['Name']

	if pPolicy:
		# Retrieve the policies associated with this OU
		ou_associated_policies = []
		for aws_policy_type in aws_policy_type_list:
			ou_associated_policies.extend(org_client.list_policies_for_target(TargetId=ou_id, Filter=aws_policy_type)['Policies'])
		for policy in ou_associated_policies:
			# If it's a Managed Policy and the user didn't want to see managed policies, then skip, otherwise show it.
			if policy['AwsManaged'] and not pManaged:
				continue
			else:
				dot.edge(ou_id, policy['Id'])

	# Retrieve the accounts under the current OU
	accounts = org_client.list_accounts_for_parent(ParentId=ou_id)

	# Add the current OU as a node in the diagram, with the number of direct accounts it has under it
	dot.node(ou_id, label=f"{ou_name} | {len(accounts['Accounts'])}\n{ou_id}", shape=ou_shape, style='filled', fillcolor=ou_fillcolor)

	all_account_associated_policies = []
	account_associated_policies = []
	for account in accounts['Accounts']:
		account_id = account['Id']
		account_name = account['Name']
		# Add the account as a node in the diagram
		dot.node(account_id, label=f"{account_name}\n{account_id}", shape=account_shape, style='filled', fillcolor=account_fillcolor)
		# Add an edge from the current OU to the account
		dot.edge(ou_id, account_id)

		if pPolicy:
			# Gather every kind of policy that could be attached to an account
			for aws_policy_type in aws_policy_type_list:
				logging.info(f"Checking for {aws_policy_type} policies on account {account_id}")
				account_associated_policies.extend(org_client.list_policies_for_target(TargetId=account_id, Filter=aws_policy_type)['Policies'])
			# Create a list of policy associations with the account that's connected to them
			all_account_associated_policies.extend([{'AcctId': account_id,
			                                         'PolicyId': x['Id'],
			                                         'PolicyName':x['Name'],
			                                         'PolicyType': x['Type'],
			                                         'AWS_Managed': x['AwsManaged']} for x in account_associated_policies])

	if pPolicy:
		all_account_associated_policies_uniq = set()
		for item in all_account_associated_policies:
			# This if statement skips showing the "FullAWSAccess" policies, if the "Managed" parameter wasn't used.
			if item['AWS_Managed'] and not pManaged:
				continue
			else:
				all_account_associated_policies_uniq.add((item['AcctId'], item['PolicyId']))
		for association in all_account_associated_policies_uniq:
			dot.edge(association[0], association[1])

	# Retrieve the child OUs under the current OU
	child_ous = org_client.list_organizational_units_for_parent(ParentId=ou_id)
	for child_ou in child_ous['OrganizationalUnits']:
		child_ou_id = child_ou['Id']

		# Recursively traverse the child OU and add edges to the diagram
		traverse_ous_and_accounts(child_ou_id, dot)
		dot.edge(ou_id, child_ou_id)


def create_policy_nodes(dot):
	associated_policies = []
	for aws_policy_type in aws_policy_type_list:
		associated_policies.extend(org_client.list_policies(Filter=aws_policy_type)['Policies'])
	for policy in associated_policies:
		policy_id = policy['Id']
		policy_name = policy['Name']

		if policy['Type'] == 'SERVICE_CONTROL_POLICY':
			policy_type = 'scp'
		elif policy['Type'] == 'TAG_POLICY':
			policy_type = 'tag'
		elif policy['Type'] == 'BACKUP_POLICY':
			policy_type = 'backup'
		elif policy['Type'] == 'AISERVICES_OPT_OUT_POLICY':
			policy_type = 'ai'
		else:
			policy_type = 'unknown'

		# This if statement allows us to skip showing the "FullAWSAccess" policies unless the user provided the parameter to want to see them
		if policy['AwsManaged'] and not pManaged:
			continue
		else:
			dot.node(policy_id, label=f"{policy_name}\n {policy_id} | {policy_type}", shape=policy_shape, color=policy_linecolor, style='filled', fillcolor=policy_fillcolor)


# Specify the AWS root organization ID
root_OUs = get_root_OUS(root)

# Create a new Digraph object for the diagram
dot = Digraph('AWS Organization', format='png', comment="Organization Structure")
# dot = dot_wide.unflatten(stagger=round_up(len(root_OUs)/5))

if pPolicy:
	create_policy_nodes(dot)
# Call the function to traverse the OUs and accounts starting from the root
for ou in root_OUs:
	traverse_ous_and_accounts(ou['Id'], dot)

# Render the diagram to a PNG image
# dot.render('aws_organization', view=True)
dot_unflat = dot.unflatten(stagger=round_up(len(root_OUs)/5))
dot_unflat.render('aws_organization2', view=True)

if pTiming:
	print(f"{Fore.GREEN}\tThis script took {time()-begin_time:.2f} seconds{Fore.RESET}")
	print()
print("Thank you for using this script")
print()
