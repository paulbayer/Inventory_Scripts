#!/usr/bin/env python3

from os import remove
from os.path import exists
import sys
import pprint
import Inventory_Modules
import logging

from ArgumentsClass import CommonArguments
from account_class import aws_acct_access
from colorama import init, Fore, Back, Style
from botocore.exceptions import ClientError, NoCredentialsError, WaiterError
from time import sleep

init()

parser = CommonArguments()
parser.singleregion()
parser.singleprofile()
parser.verbosity()
# parser.version()
parser.my_parser.add_argument(
		"--old",
		dest="pOldStackSet",
		metavar="The name of the old stackset",
		help="This is the name of the old stackset, which manages the existing stack instances in the legacy accounts.")
parser.my_parser.add_argument(
		"--new",
		dest="pNewStackSet",
		metavar="The name of the new stackset",
		help="This is the name of the new stackset, which will manage the existing stack instances going forward.")
parser.my_parser.add_argument(
		"-A", "--Account",
		dest="pAccountToMove",
		default=None,
		metavar="Account Number",
		help="The single account to be moved from one stackset to another",
		)
parser.my_parser.add_argument(
		"--recovery",
		dest="pRecoveryFlag",
		action="store_true",
		help="Whether we should use the recovery file.",
		)
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Region
verbose = args.loglevel
pRecoveryFlag = args.pRecoveryFlag
# version = args.Version
pOldStackSet = args.pOldStackSet
pNewStackSet = args.pNewStackSet
pAccountToMove = args.pAccountToMove
# Logging Settings
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
# Set Log Level
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

ERASE_LINE = '\x1b[2K'
# The time between checks to see if the stackset instances have been created, or imported...
sleep_interval = 5
# Currently, this is a hard-stop at 10, but I made it a variable in case they up the limit
StackInstancesImportedAtOnce = 10
stack_ids = []

"""
This script attempts to move stack-instances from one stack-set to another without any impact to the ultimate resources.
Here's what's needed:
	0. Either Create or be provided with the new stackset... 
	
	If we have to CREATE the NewStackSet:
	1. Determine the template body of the existing stackset. The body will need to be cleaned up, since the JSON is escaped all over.
	2. Determine the parameters from the existing stackset
		2.5 Determine whether you need to specify "--capabilities CAPABILITIES_NAMED_IAM" when creating the new stackset 
	3. Create a new stackset with the template body of the existing stackset.
	
	If NewStackSet is PROVIDED:
	1. Accept the parameters of the stackset name - assuming the template body and parameters have been applied already.  
		
	COMMON to both cases:
	4. Determine the stack-ids of the existing stack-instances you want to move from the existing stackset
	**** At this point it's important to write the recovery file, so you have the stack_ids saved, before you begin removing them from the old stackset (during the import)
	5. Run the import to the new stackset, specifying the stack-ids of the existing stack-instances, no more than 10 at a time. 
		Ideally, you would aggregate accounts into a single run, so you could parallelize the regional deployments
	6. Verify that the operation returned a success for all stack-instances
	7. Loop through the stack-ids until complete - verifying after each one
		7.5 Remember the script will have to continuously poll the stack-set to determine when it's complete 
	8. Report on status at the end.
	

"""

########################

def check_stack_set_status(faws_acct, fStack_set_name, fOperationId=None):
	"""
	response = client.describe_stack_set_operation(
	    StackSetName='string',
	    OperationId='string',
	    CallAs='SELF'|'DELEGATED_ADMIN'
	)
	"""
	import logging

	client_cfn = faws_acct.session.client('cloudformation')
	return_response = dict()
	# If the calling process couldn't supply the OpId, then we have to find it, based on the name of the stackset
	if fOperationId is None:
		# If there is no OperationId, they've called us after creating the stack-set itself,
		# so we need to check the status of the stack-set creation, and not the operations that happen to the stackset
		try:
			response = client_cfn.describe_stack_set(StackSetName=fStack_set_name,
			                                         CallAs='SELF')['StackSet']
			return_response['StackSetStatus'] = response['Status']
			return_response['Success'] = True
			return (return_response)
		except client_cfn.exceptions.StackSetNotFoundException as myError:
			logging.error(f"Stack Set {fStack_set_name} Not Found: {myError}")
			return_response['Success'] = False
			return (return_response)
	try:
		response = client_cfn.describe_stack_set_operation(StackSetName=fStack_set_name,
		                                                   OperationId=fOperationId,
		                                                   CallAs='SELF')['StackSetOperation']
		return_response['StackSetStatus'] = response['Status']
		return_response['Success'] = True
	except client_cfn.exceptions.StackSetNotFoundException as myError:
		print(f"StackSet Not Found: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.OperationNotFoundException as myError:
		print(f"Operation Not Found: {myError}")
		return_response['Success'] = False
	return (return_response)


def find_if_stack_set_exists(faws_acct, fStack_set_name):
	"""
	response = client.describe_stack_set(
	    StackSetName='string',
	    CallAs='SELF'|'DELEGATED_ADMIN'
	)
	"""
	import logging

	logging.info(f"Verifying whether the stackset {fStack_set_name} in account {faws_acct.acct_number} exists")
	client_cfn = faws_acct.session.client('cloudformation')
	return_response = dict()
	try:
		response = client_cfn.describe_stack_set(StackSetName=fStack_set_name, CallAs='SELF')['StackSet']
		return_response = {'Payload': response, 'Success': True}
	except client_cfn.exceptions.StackSetNotFoundException as myError:
		logging.info(f"StackSet {fStack_set_name} not found in this account.")
		logging.debug(f"{myError}")
		return_response['Success'] = False
	return (return_response)


# def operation_is_complete(faws_acct, fOperationId):
# 	"""
#
# 	"""
# 	import logging
# 	client_cfn = aws_acct.session.client('cloudformation')
# 	# response = client_cfn.


def get_template_body_and_parameters(faws_acct, fExisting_stack_set_name):
	"""
	describe_stack_set output:
	{
	    "StackSet": {
	        "StackSetName": "AWS-Landing-Zone-Baseline-DemoRoles",
	        "StackSetId": "AWS-Landing-Zone-Baseline-DemoRoles:872bab58-25b9-4785-8973-e7920cbe46d3",
	        "Status": "ACTIVE",
	        "TemplateBody": "AWSTemplateFormatVersion: \"2010-09-09\"\nDescription: Sample of a new role with the use of a managed policy, and a parameterized trust policy.\n\nParameters:\n  AdministratorAccountId:\n    Type: String\n    Default: \"287201118218\"\n    Description: AWS Account Id of the administrator account.\nResources:\n  SampleRole:\n    Type: \"AWS::IAM::Role\"\n    Properties:\n      RoleName: DemoRole\n      Path: /\n      AssumeRolePolicyDocument:\n        Version: \"2012-10-17\"\n        Statement:\n          -\n            Effect: \"Allow\"\n            Principal:\n              AWS:\n                - !Sub 'arn:aws:iam::${AdministratorAccountId}:role/Owner'\n                - !Sub 'arn:aws:iam::${AdministratorAccountId}:user/Paul'\n            Action:\n              - \"sts:AssumeRole\"\n      ManagedPolicyArns:\n        - arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess\n",
	        "Parameters": [
	            {
	                "ParameterKey": "AdministratorAccountId",
	                "ParameterValue": "517713657778",
	                "UsePreviousValue": false
	            }
	        ],
	        "Capabilities": [
	            "CAPABILITY_NAMED_IAM"
	        ],
	        "Tags": [
	            {
	                "Key": "AWS_Solutions",
	                "Value": "LandingZoneStackSet"
	            }
	        ],
	        "StackSetARN": "arn:aws:cloudformation:us-east-1:517713657778:stackset/AWS-Landing-Zone-Baseline-DemoRoles:872bab58-25b9-4785-8973-e7920cbe46d3",
	        "AdministrationRoleARN": "arn:aws:iam::517713657778:role/AWSCloudFormationStackSetAdministrationRole",
	        "ExecutionRoleName": "AWSCloudFormationStackSetExecutionRole",
	        "StackSetDriftDetectionDetails": {
	            "DriftStatus": "NOT_CHECKED",
	            "TotalStackInstancesCount": 0,
	            "DriftedStackInstancesCount": 0,
	            "InSyncStackInstancesCount": 0,
	            "InProgressStackInstancesCount": 0,
	            "FailedStackInstancesCount": 0
	        },
	        "OrganizationalUnitIds": []
	    }
	}
	"""
	import logging

	logging.info(f"Connecting to account {faws_acct.acct_number} to get info about stackset {fExisting_stack_set_name}")
	client_cfn = faws_acct.session.client('cloudformation')
	return_response = {'Success': False}
	try:
		stack_set_info = client_cfn.describe_stack_set(StackSetName=fExisting_stack_set_name)['StackSet']
		return_response['stack_set_info'] = stack_set_info
		return_response['Success'] = True
	except client_cfn.exceptions.StackSetNotFoundException as myError:
		ErrorMessage = f"{fExisting_stack_set_name} doesn't seem to exist. Please check the spelling"
		print(f"{ErrorMessage}: {myError}")
		return_response['Success'] = False
	return (return_response)


def get_stack_ids_from_existing_stack_set(faws_acct, fExisting_stack_set_name, fAccountToMove=None):
	"""
	response = client.list_stack_instances(
	    StackSetName='string',
	    NextToken='string',
	    MaxResults=123,
	    Filters=[
	        {
	            'Name': 'DETAILED_STATUS',
	            'Values': 'string'
	        },
	    ],
	    StackInstanceAccount='string',
	    StackInstanceRegion='string',
	    CallAs='SELF'|'DELEGATED_ADMIN'
	)
	"""
	import logging

	client_cfn = faws_acct.session.client('cloudformation')
	return_response = dict()
	try:
		response = client_cfn.list_stack_instances(StackSetName=fExisting_stack_set_name, CallAs='SELF')
		return_response['Stack_instances'] = response['Summaries']
		while 'NextToken' in response.keys():
			response = client_cfn.list_stack_instances(StackSetName=fExisting_stack_set_name, CallAs='SELF',
			                                           NextToken=response['NextToken'])
			return_response['Stack_instances'].extend(response['Summaries'])
		return_response['Success'] = True
	except client.exceptions.StackSetNotFoundException as myError:
		print(myError)
		return_response['Success'] = False
	if fAccountToMove is None:
		logging.debug(f"No Account was specified, so all stack-instance-ids are being returned")
		pass
	else:
		return_response['Stack_instances'] = [stacksetinfo for stacksetinfo in return_response['Stack_instances'] if stacksetinfo['Account'] == fAccountToMove]
		logging.debug(
				f"Account {fAccountToMove} was specified, so only the {len(return_response['Stack_instances'])} "
				f"stack-instance-ids matching that account are being returned")
	return (return_response)


def write_info_to_file(faws_acct, fstack_ids):
	"""
	Docs go here
	"""
	import logging
	import simplejson as json

	# Create a dictionary that will represent everything we're trying to do
	try:
		StackSetsInfo = {
			'ProfileUsed': pProfile,
			'ManagementAccount': faws_acct.MgmtAccount,
			'Region': pRegion,
			'AccountNumber': faws_acct.acct_number,
			'AccountToMove' : pAccountToMove,
			'OldStackSetName': pOldStackSet,
			'NewStackSetName': pNewStackSet,
			'stack_ids': fstack_ids
			}
		logging.info(f"Writing data to the file {InfoFilename}")
		logging.debug(f"Here's the data we're writing: {StackSetsInfo}")
		file_data = json.dumps(StackSetsInfo, sort_keys=True, indent=4*' ')
		with open(InfoFilename, 'w') as out:
			print(file_data, file=out)
		return_response = {'Success': True}
		return(return_response)
	except:
		logging.error("There was a problem. Not sure... ")
		return_response = {'Success': False, 'ErrorMessage': 'Unsure yet'}
		return(return_response)


def read_stack_info_from_file():
	"""
	Docs go here
	"""
	import logging
	import simplejson as json

	try:
		with open(InfoFilename) as input_file:
			my_input_file = json.load(input_file)
		return_response = {'Success': True, 'Payload': my_input_file}
		return(return_response)
	except:
		logging.error("There was a problem. Not sure... ")
		return_response = {'Success': False, 'ErrorMessage': 'Unsure yet'}
		return(return_response)


def create_stack_set_with_body_and_parameters(faws_acct, fNew_stack_set_name, fStack_set_info):
	"""
	response = client.create_stack_set(
	    StackSetName='string',
	    Description='string',
	    TemplateBody='string',
	    TemplateURL='string',
	    StackId='string',
	    Parameters=[
	        {
	            'ParameterKey': 'string',
	            'ParameterValue': 'string',
	            'UsePreviousValue': True|False,
	            'ResolvedValue': 'string'
	        },
	    ],
	    Capabilities=[
	        'CAPABILITY_IAM'|'CAPABILITY_NAMED_IAM'|'CAPABILITY_AUTO_EXPAND',
	    ],
	    Tags=[
	        {
	            'Key': 'string',
	            'Value': 'string'
	        },
	    ],
	    AdministrationRoleARN='string',
	    ExecutionRoleName='string',
	    PermissionModel='SERVICE_MANAGED'|'SELF_MANAGED',
	    AutoDeployment={
	        'Enabled': True|False,
	        'RetainStacksOnAccountRemoval': True|False
	    },
	    CallAs='SELF'|'DELEGATED_ADMIN',
	    ClientRequestToken='string'
	)
	"""

	import logging

	logging.info(
			f"Creating a new stackset name {fNew_stack_set_name} in account {faws_acct.acct_number} with a template body, parameters, capabilities and tagging from this:")
	logging.info(f"{fStack_set_info}")
	client_cfn = faws_acct.session.client('cloudformation')
	return_response = dict()
	# TODO: We should change the template body to a template url to accommodate really big templates
	try:
		response = client_cfn.create_stack_set(StackSetName=fNew_stack_set_name,
		                                       TemplateBody=fStack_set_info['TemplateBody'],
		                                       Description=fStack_set_info['Description'],
		                                       Parameters=fStack_set_info['Parameters'],
		                                       Capabilities=fStack_set_info['Capabilities'],
		                                       Tags=fStack_set_info['Tags'])
		return_response['StackSetId'] = response['StackSetId']
		return_response['Success'] = True
	# There is currently no waiter to use for this operation...
	except client_cfn.exceptions.NameAlreadyExistsException as myError:
		logging.error(f"Operation Failed: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.CreatedButModifiedException as myError:
		logging.error(f"Operation Failed: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.LimitExceededException as myError:
		logging.error(f"Operation Failed: {myError}")
		return_response['Success'] = False
	return (return_response)


def disconnect_stack_instances(faws_acct, fStack_instances, fOldStackSet):
	"""
	response = client.delete_stack_instances(
	    StackSetName='string',
	    Accounts=[
	        'string',
	    ],
	    DeploymentTargets={
	        'Accounts': [
	            'string',
	        ],
	        'AccountsUrl': 'string',
	        'OrganizationalUnitIds': [
	            'string',
	        ]
	    },
	    Regions=[
	        'string',
	    ],
	    OperationPreferences={
	        'RegionConcurrencyType': 'SEQUENTIAL'|'PARALLEL',
	        'RegionOrder': [
	            'string',
	        ],
	        'FailureToleranceCount': 123,
	        'FailureTolerancePercentage': 123,
	        'MaxConcurrentCount': 123,
	        'MaxConcurrentPercentage': 123
	    },
	    RetainStacks=True|False,
	    OperationId='string',
	    CallAs='SELF'|'DELEGATED_ADMIN'
	)

	"""
	import logging

	logging.info(f"Disassociating stacks from {fOldStackSet}")
	return_response = dict()
	if len(fStack_instances['Stack_instances']) == 0:
		return_response = {'Success': False,
		                   'ErrorMessage': f"Stackset {fOldStackSet} has no matching instances",
		                   'OperationId': None}
		return(return_response)
	client_cfn = faws_acct.session.client('cloudformation')
	regions = set()
	accounts = set()
	for item in fStack_instances['Stack_instances']:
		regions.add(item['Region'])
		accounts.add(item['Account'])
	try:
		response = client_cfn.delete_stack_instances(
				StackSetName=fOldStackSet,
				Accounts=list(accounts),
				Regions=list(regions),
				OperationPreferences={
					'RegionConcurrencyType'     : 'PARALLEL',
					'FailureTolerancePercentage': 10,
					'MaxConcurrentPercentage'   : 100},
				RetainStacks=True,
				CallAs='SELF')
		return_response['OperationId'] = response['OperationId']
		return_response['Success'] = True
	except client_cfn.exceptions.StackSetNotFoundException as myError:
		logging.error(f"Operation Failed: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.OperationInProgressException as myError:
		logging.error(f"Operation Failed: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.OperationIdAlreadyExistsException as myError:
		logging.error(f"Operation Failed: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.StaleRequestException as myError:
		logging.error(f"Operation Failed: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.InvalidOperationException as myError:
		logging.error(f"Operation Failed: {myError}")
		return_response['Success'] = False
	stack_instance_operation_waiter = client_cfn.get_waiter('stack_delete_complete')
	try:
		stack_instance_operation_waiter.wait(StackName=fOldStackSet)
		return_response['Success'] = True
	except WaiterError as myError:
		if "Max attempts exceeded" in myError.message:
			logging.error(f"Import didn't complete within 600 seconds")
		else:
			logging.error(myError)
		return_response['Success'] = False
	return (return_response)


def create_change_set_for_new_stack():
	"""
	Do we need to do this?
	"""


def populate_new_stack_with_existing_stack_instances(faws_acct, fStack_instance_info, fNew_stack_name):
	"""
	response = client.import_stacks_to_stack_set(
	    StackSetName='string',
	    StackIds=[
	        'string',
	    ],
	    OperationPreferences={
	        'RegionConcurrencyType': 'SEQUENTIAL'|'PARALLEL',
	        'RegionOrder': [
	            'string',
	        ],
	        'FailureToleranceCount': 123,
	        'FailureTolerancePercentage': 123,
	        'MaxConcurrentCount': 123,
	        'MaxConcurrentPercentage': 123
	    },
	    OperationId='string',
	    CallAs='SELF'|'DELEGATED_ADMIN'
	)

	The Operation Id as the response is really important, because that's how we determine whether teh operation is done (or a success),
	so that we can add 10 more stacks... This can take a long time for a lot of instances...
	"""
	import logging

	stack_instance_ids = [stack_instance['StackId'] for stack_instance in fStack_instance_info
	                      if stack_instance['Status'] in ['CURRENT', 'OUTDATED', 'CREATE_COMPLETE', 'UPDATE_COMPLETE']]
	logging.info(f"Populating new stackset {fNew_stack_name} in account {faws_acct.acct_number} with stack_ids: {stack_instance_ids}")
	client_cfn = faws_acct.session.client('cloudformation')
	return_response = dict()
	try:
		response = client_cfn.import_stacks_to_stack_set(StackSetName=fNew_stack_name,
		                                                 StackIds=stack_instance_ids,
		                                                 OperationPreferences={
			                                                 'RegionConcurrencyType'     : 'PARALLEL',
			                                                 'FailureTolerancePercentage': 0,
			                                                 'MaxConcurrentPercentage'   : 100},
		                                                 CallAs='SELF')
		return_response['OperationId'] = response['OperationId']
	except client_cfn.exceptions.LimitExceededException as myError:
		logging.error(f"Limit Exceeded: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.StackSetNotFoundException as myError:
		logging.error(f"Stack Set Not Found: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.InvalidOperationException as myError:
		logging.error(f"Invalid Operation: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.OperationInProgressException as myError:
		logging.error(f"Operation is already in progress: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.StackNotFoundException as myError:
		logging.error(f"Stack Not Found: {myError}")
		return_response['Success'] = False
	except client_cfn.exceptions.StaleRequestException as myError:
		logging.error(f"Stale Request: {myError}")
		return_response['Success'] = False
	except ClientError as myError:
		logging.error(f"Client Error: {myError}")
		return_response['Success'] = False
	return (return_response)


########################

aws_acct = aws_acct_access(pProfile)
InfoFilename = (f"{pOldStackSet}-{pNewStackSet}-{aws_acct.acct_number}-{pRegion}")
Use_recovery_file = False

if exists(InfoFilename) and pRecoveryFlag:
	print(f"You requested to use the recovery file {InfoFilename}, so we'll use that to pick up from where we left off")
	Use_recovery_file = True
elif pRecoveryFlag:
	print(f"You requested to use the Recovery file, but we couldn't find one named {InfoFilename}, so we're exiting\n"
	      f"Please supply the proper StackSet, Region and Profile parameters so we can find the recovery file.", file=sys.stderr)
	sys.exit(5)
elif exists(InfoFilename):
	print(f"There exists a recovery file for the parameters you've supplied, named {InfoFilename}\n")
	Use_recovery_file = (input(f"Do you want to use this file? (y/n): ") in ['y', 'Y'])
	if not Use_recovery_file:
		print(f"If you don't want to use that file, please change the filename, and re-run this script.", file=sys.stderr)
		sys.exit(6)

if Use_recovery_file:
	fileinput = read_stack_info_from_file()
	AccountNumber = fileinput['Payload']['AccountNumber']
	if not AccountNumber == aws_acct.acct_number:
		print(f"You're running this script referencing a different account than the one used last when the recovery file {InfoFilename} was created.\n"
		      f"Please make sure you finish that last task before starting a new one.\n", file=sys.stderr)
		sys.exit(4)
	pAccountToMove = fileinput['Payload']['AccountToMove']
	pOldStackSet = fileinput['Payload']['OldStackSetName']
	pNewStackSet = fileinput['Payload']['NewStackSetName']
	pRegion = fileinput['Payload']['Region']
	stack_ids = fileinput['Payload']['stack_ids']

# The following is just letting the user know what we're going to do in this script.
# Since this script is by nature intrusive, we want the user to confirm everything before they continue.
if pAccountToMove is None:
	logging.info(f"Successfully connected to account {aws_acct.acct_number} to move stack instances "
	             f"from {pOldStackSet} to {pNewStackSet}")
else:
	logging.info(f"Connecting to account {aws_acct.acct_number} to move instances for account {pAccountToMove}"
	             f" from {pOldStackSet} to {pNewStackSet}")
# Check to see if the new StackSet already exists, or we need to create it.
if find_if_stack_set_exists(aws_acct, pNewStackSet)['Success']:
	print(f"{Fore.GREEN}The 'New' Stackset {pNewStackSet} exists within the account {aws_acct.acct_number}{Fore.RESET}")
	NewStackSetExists = True
else:
	print(f"{Fore.RED}The 'New' Stackset {pNewStackSet} does not exist within the account {aws_acct.acct_number}{Fore.RESET}")
	NewStackSetExists = False
# Check to see if the old StackSet exists, as they may have typed something wrong - or the recovery file was never deleted.
if find_if_stack_set_exists(aws_acct, pOldStackSet)['Success']:
	print(f"{Fore.GREEN}The 'Old' Stackset {pOldStackSet} exists within the account {aws_acct.acct_number}{Fore.RESET}")
	OldStackSetExists = True
else:
	print(f"{Fore.RED}The 'Old' Stackset {pOldStackSet} does not exist within the account {aws_acct.acct_number}{Fore.RESET}")
	OldStackSetExists = False

User_Confirmation = (input(f"Is the above information correct? Do you want to proceed? (y/n): ") in ['y', 'Y'])
if not User_Confirmation:
	print(f"User cancelled script", file=sys.stderr)
	sys.exit(10)


# Ignore whether or not the recovery file exists, since if it does - it's just updating the variables needed for this run.
# We shouldn't be doing much of anything differently, based on whether the recovery file exists.
if OldStackSetExists:
	# We would only get to this point if (for some reason) the script dies before a new stackset could be made.
	# In that case, we may not have even written a recovery file yet.
	if not NewStackSetExists:       # We need to create the new stacksets
		"""
		1. Determine the template body of the existing stackset.
		2. Determine the parameters from the existing stackset
			2.5 Determine whether you need to specify "--capabilities CAPABILITIES_NAMED_IAM" when creating the new stackset 
		3. Create a new stackset with the template body of the existing stackset.
		"""
		# print(f"New Stack Set {pNewStackSet} needs to be created...")
		print()
		print(f"You've asked for us to move stacksets from the existing stackset {pOldStackSet}"
		      f" and create a new stackset called: {pNewStackSet}")
		if pAccountToMove is not None:
			print(f"But only for account {pAccountToMove}")
		print()
		Stack_Set_Info = get_template_body_and_parameters(aws_acct, pOldStackSet)
		NewStackSetId = create_stack_set_with_body_and_parameters(aws_acct, pNewStackSet, Stack_Set_Info['stack_set_info'])
		logging.warning(f"Waiting for new stackset {pNewStackSet} to be created")
		sleep(sleep_interval)
		NewStackSetStatus = check_stack_set_status(aws_acct, pNewStackSet)
		intervals_waited = 1
		if NewStackSetStatus['Success']:
			while NewStackSetStatus['Success'] and not NewStackSetStatus['StackSetStatus'] in ['ACTIVE']:
				print(f"Waiting for StackSet {pNewStackSet} to be ready", f"." * intervals_waited, end='\r')
				sleep(sleep_interval)
				intervals_waited += 1
				NewStackSetStatus = check_stack_set_status(aws_acct, pNewStackSet)
			print(f"{ERASE_LINE}Stackset {pNewStackSet} has been successfully created")
			# TODO: Use the NewStackSetId Operation Id, to check if the empty new stackset has successfully been created
			pass
		else:
			print(f"{pNewStackSet} failed to be created. Exiting...")
			sys.exit(99)

	else:       # PNewStackSet *does* exist
		"""
		1. Get the stack-ids from the old stack-set - write them to a file (in case we need to recover the process)
		"""
		# First time this script has run...
		print("New Stack Set already exists path...")

	######## This code is common across both use-cases ##################
	logging.debug(f"Getting Stack Ids from existing stack set {pOldStackSet}")
	# **** 1. Get the stack-ids from the old stack-set ****
	if Use_recovery_file:
		pass
	else:
		stack_ids = get_stack_ids_from_existing_stack_set(aws_acct, pOldStackSet, pAccountToMove)
	logging.debug(f"Found {len(stack_ids)} stack ids from stackset {pOldStackSet}")
	# Write the stack_ids info to a file, so we don't lose this info if the script fails
	fileresult = write_info_to_file(aws_acct, stack_ids)
	if not fileresult['Success']:
		print(f"Something went wrong.\n"
		      f"Error Message: {fileresult['ErrorMessage']}")
		sys.exit(9)
	# For every 10 stack-ids, use the OpId below to verify that the Operation has finished:
	# **** 2. Remove the stack-instances from the old stack-set ****
	logging.debug(f"Removing stack instances from stackset {pOldStackSet}")
	DisconnectStackInstances = disconnect_stack_instances(aws_acct, stack_ids, pOldStackSet)
	if not DisconnectStackInstances['Success']:
		if DisconnectStackInstances['ErrorMessage'].find('has no matching instances') > 0 and Use_recovery_file:
			pass    # This could be because the Old Stackset already had the instances disconnected when the script failed
		else:
			print(f"Failure... exiting due to: {DisconnectStackInstances['ErrorMessage']}")
			sys.exit(7)
	logging.debug(f"Removed stack instances from {pOldStackSet}")
	if DisconnectStackInstances['OperationId'] is not None:
		StackInstancesAreGone = check_stack_set_status(aws_acct, pOldStackSet, DisconnectStackInstances['OperationId'])
		if not StackInstancesAreGone['Success']:
			sys.exit(f"There was a problem with removing the stack instances from stackset {pOldStackSet}. Exiting...")
		logging.debug(f"The operation id {DisconnectStackInstances['OperationId']} is {StackInstancesAreGone['StackSetStatus']}")
		intervals_waited = 1
		while StackInstancesAreGone['StackSetStatus'] in ['RUNNING']:
			print(f"Waiting for stack instances to be disconnected from stackset {pOldStackSet} -",
			      # f"." * intervals_waited,
			      f"{sleep_interval * intervals_waited} seconds waited so far", end='\r')
			sleep(sleep_interval)
			intervals_waited += 1
			StackInstancesAreGone = check_stack_set_status(aws_acct, pOldStackSet, DisconnectStackInstances['OperationId'])
		if not StackInstancesAreGone['Success']:
			print(f"There was a problem with removing the stack instances from stackset {pOldStackSet}. Exiting...")
			sys.exit(8)
	# For every 10 stack-ids:
	# **** 3. Import those stack-ids into the new stack-set, 10 at a time ****
	x = 0
	limit = StackInstancesImportedAtOnce
	while x < len(stack_ids['Stack_instances']):
		stack_ids_subset = [stack_ids['Stack_instances'][x + i] for i in range(limit) if
		                    x + i < len(stack_ids['Stack_instances'])]
		x += limit
		print(f"{ERASE_LINE}Importing {len(stack_ids_subset)} stacks into the new stackset now...")
		ReconnectStackInstances = populate_new_stack_with_existing_stack_instances(aws_acct, stack_ids_subset, pNewStackSet)
		StackReadyToImport = check_stack_set_status(aws_acct, pNewStackSet, ReconnectStackInstances['OperationId'])
		if not StackReadyToImport['Success']:
			sys.exit(f"There was a problem with importing the stack"
			         f" instances into stackset {pNewStackSet}. Exiting...")
		intervals_waited = 1
		while StackReadyToImport['StackSetStatus'] in ['RUNNING', 'QUEUED']:
			print(f"Waiting for StackSet {pNewStackSet} to finish importing -",
			      # f"." * intervals_waited,
			      f"{sleep_interval * intervals_waited} seconds waited so far", end='\r')
			sleep(sleep_interval)
			intervals_waited += 1
			StackReadyToImport = check_stack_set_status(aws_acct, pNewStackSet, ReconnectStackInstances['OperationId'])
			if not StackReadyToImport['Success']:
				sys.exit(
					f"There was a problem with importing the stack instances into stackset {pNewStackSet}. Exiting...")
		logging.info(f"{ERASE_LINE}That import took {intervals_waited * sleep_interval} seconds to complete")

else:  # Old Stackset doesn't exist - so there was a typo somewhere. Tell the user and exit
	print(f"It appears that the legacy stackset you provided {pOldStackSet} doesn't exist.\n"
	      f"Please check the spelling, or the account, and try again.\n\n"
	      f"{Fore.LIGHTBLUE_EX}Perhaps the recovery file was never deleted?{Fore.RESET}")

# Delete the recovery file, if it exists
if exists(InfoFilename):
	try:
		FileDeleted = remove(InfoFilename)
	except OSError as myError:
		print(myError)

print()
print("Thank you for using this script")
print()
