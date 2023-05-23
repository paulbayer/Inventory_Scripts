import boto3
import logging
from graphviz import Digraph
from ArgumentsClass import CommonArguments

__version__ = '2023.05.04'

parser = CommonArguments()
parser.my_parser.description = ("To draw the Organization.")
parser.singleprofile()
parser.verbosity()
parser.version(__version__)
args = parser.my_parser.parse_args()

pProfile = args.Profile
verbose = args.loglevel
logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(""message)s")

# Create an AWS Organizations client
org_client = boto3.Session(profile_name=pProfile).client('organizations')

root = org_client.list_roots()['Roots'][0]['Id']
account_fillcolor = 'orange'
account_shape = 'ellipse'
policy_fillcolor = 'azure'
policy_linecolor = 'red'
policy_shape = 'hexagon'
ou_fillcolor = 'burlywood'
ou_shape = 'box'

def get_root_OUS(root_id):
	try:
		ChildOUs = org_client.list_children(ParentId=root_id, ChildType='ORGANIZATIONAL_UNIT')
	except (org_client.exceptions.AccessDeniedException,
	        org_client.exceptions.AWSOrganizationsNotInUseException,
	        org_client.exceptions.InvalidInputException,
	        org_client.exceptions.ParentNotFoundException,
	        org_client.exceptions.ServiceException,
	        org_client.exceptions.TooManyRequestsException) as myError:
		logging.error(f"Error: {myError}")
	return (ChildOUs['Children'])


# Function to recursively traverse the OUs and accounts
def traverse_ous_and_accounts(ou_id, dot):
	# Retrieve the details of the current OU
	ou = org_client.describe_organizational_unit(OrganizationalUnitId=ou_id)
	ou_name = ou['OrganizationalUnit']['Name']

	# Retrieve the policies associated with this OU
	associated_scps = org_client.list_policies_for_target(TargetId=ou_id, Filter='SERVICE_CONTROL_POLICY')['Policies']
	for policy in associated_scps:
		policy_id = policy['Id']
		policy_name = policy['Name']
		"""
		Possible values as of 5/23/2023
		AISERVICES_OPT_OUT_POLICY
		BACKUP_POLICY
        SERVICE_CONTROL_POLICY
        TAG_POLICY
		"""
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
		dot.node(policy_id, label=f"{policy_name}\n {policy_id} | {policy_type}", shape=policy_shape, color=policy_linecolor, style='filled', fillcolor=policy_fillcolor)
		dot.edge(ou_id, policy_id)

	# Retrieve the accounts under the current OU
	accounts = org_client.list_accounts_for_parent(ParentId=ou_id)

	# Add the current OU as a node in the diagram
	dot.node(ou_id, label=f"{ou_name} | {len(accounts['Accounts'])}\n{ou_id}", shape=ou_shape, style='filled', fillcolor=ou_fillcolor)

	for account in accounts['Accounts']:
		account_id = account['Id']
		account_name = account['Name']

		# Add the account as a node in the diagram
		dot.node(account_id, label=f"{account_name}\n{account_id}", shape=account_shape, style='filled', fillcolor=account_fillcolor)

		# Add an edge from the current OU to the account
		dot.edge(ou_id, account_id)

	# Retrieve the child OUs under the current OU
	child_ous = org_client.list_organizational_units_for_parent(ParentId=ou_id)
	for child_ou in child_ous['OrganizationalUnits']:
		child_ou_id = child_ou['Id']

		# Recursively traverse the child OU and add edges to the diagram
		traverse_ous_and_accounts(child_ou_id, dot)
		dot.edge(ou_id, child_ou_id)


# Specify the AWS root organization ID
root_OUs = get_root_OUS(root)

# Create a new Digraph object for the diagram
dot = Digraph('AWS Organization', format='png')

# Call the function to traverse the OUs and accounts starting from the root
for ou in root_OUs:
	traverse_ous_and_accounts(ou['Id'], dot)

# Render the diagram to a PNG image
dot.render('aws_organization', view=True)

print("Done")
