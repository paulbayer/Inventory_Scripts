#!/usr/bin/env python3

import os
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
parser.rootOnly()
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
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Region
verbose = args.loglevel
# version = args.Version
pOldStackSet = args.pOldStackSet
pNewStackSet = args.pNewStackSet
# Logging Settings
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
# Set Log Level
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

ERASE_LINE = '\x1b[2K'
sleep_interval = 5
StackInstancesImportedAtOnce = 10

"""
This script attempts to move stack-instances from one stack-set to another without any impact to the ultimate resources.
Here's what's needed:
	0. Either Create or be provided with the new stackset... 
	
	If CREATE:
	1. Determine the template body of the existing stackset. The body will need to be cleaned up, since the JSON is escaped all over.
	2. Determine the parameters from the existing stackset
		2.5 Determine whether you need to specify "--capabilities CAPABILITIES_NAMED_IAM" when creating the new stackset 
	3. Create a new stackset with the template body of the existing stackset.
	4. Determine the stack-ids of the existing stack-instances you want to move from the existing stackset
	5. Run the import to the new stackset, specifying the stack-ids of the existing stack-instances, no more than 10 at a time. 
		Ideally, you would aggregate accounts into a single run, so you could parallelize the regional deployments
	6. Verify that the operation returned a success for all stack-instances
	7. Loop through the stack-ids until complete - verifying after each one
		7.5 Remember the script will have to continuously poll the stack-set to determine when it's complete 
	8. Report on status at the end.
	
	If PROVIDED:
	1. Accept the parameters of the stackset name - assuming the template body and parameters have been applied already.  
	4. Determine the stack-ids of the existing stack-instances you want to move from the existing stackset
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


def get_stack_ids_from_existing_stack_set(faws_acct, fExisting_stack_set_name):
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
	return (return_response)


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


def remove_stack_instances(faws_acct, fStack_instances, fOldStackSet):
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
	client_cfn = faws_acct.session.client('cloudformation')
	return_response = dict()
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
	                      if stack_instance['Status'] in ['CURRENT', 'OUTDATED']]
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
		"""
		The following code is nice, but the "stack_import" waiter doesn't apply to *stacksets*.
		
		import_operation_waiter = client_cfn.get_waiter('stack_import_complete')
		try:
			logging.info(f"Waiting for import to be complete...")
			import_operation_waiter.wait(StackName=fNew_stack_name)
			return_response['Success'] = True
		except WaiterError as myError:
			# if "Max attempts exceeded" in myError.message:
			# logging.error(f"Import didn't complete within 600 seconds {myError}")
			# else:
			logging.error(myError)
			return_response['Success'] = False
		"""
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
	return (return_response)


########################

aws_acct = aws_acct_access(pProfile)
logging.info(
	f"Successfully connected to account {aws_acct.acct_number} to move stack instances from {pOldStackSet} to {pNewStackSet}")
# DoesStackSetExist = find_if_stack_set_exists(aws_acct, pNewStackSet)
if find_if_stack_set_exists(aws_acct, pNewStackSet)['Success']:
	logging.info(f"The Stackset {pNewStackSet} exists within the account {aws_acct.acct_number}")
	NewStackSetExists = True
else:
	logging.info(f"The Stackset {pNewStackSet} does not exist within the account {aws_acct.acct_number}")
	NewStackSetExists = False

if find_if_stack_set_exists(aws_acct, pOldStackSet)['Success']:
	logging.info(f"The Stackset {pOldStackSet} exists within the account {aws_acct.acct_number}")
	OldStackSetExists = True
else:
	logging.info(f"The Stackset {pOldStackSet} does not exist within the account {aws_acct.acct_number}")
	OldStackSetExists = False

if OldStackSetExists:
	if NewStackSetExists:
		"""
		1. Get the stack-ids from the old stack-set
		2. Remove the stack-instances from the old stack-set
		3. Import those stack-ids into the new stack-set, 10 at a time
		4. Verify that all the stack-instances made it over properly
		"""
		print("New Stack Set already exists path...")
		logging.debug(f"Getting Stack Ids from existing stack set {pOldStackSet}")
		# **** 1. Get the stack-ids from the old stack-set ****
		stack_ids = get_stack_ids_from_existing_stack_set(aws_acct, pOldStackSet)
		logging.debug(f"Found {len(stack_ids)} stack ids from stackset {pOldStackSet}")
		# stack_info = stack_instance_info['Stack_instances']
		# **** 2. Remove the stack-instances from the old stack-set ****
		logging.debug(f"Removing ALL stack instances from stackset {pOldStackSet}")
		OpId = remove_stack_instances(aws_acct, stack_ids, pOldStackSet)
		logging.debug(f"Removed stack instances from {pOldStackSet}")
		StackInstancesAreGone = check_stack_set_status(aws_acct, pOldStackSet, OpId['OperationId'])
		if not StackInstancesAreGone['Success']:
			sys.exit(f"There was a problem with removing the stack instances from stackset {pOldStackSet}. Exiting...")
		logging.debug(f"The operation id {OpId['OperationId']} is {StackInstancesAreGone['StackSetStatus']}")
		intervals_waited = 1
		while StackInstancesAreGone['StackSetStatus'] in ['RUNNING']:
			print(f"Waiting {sleep_interval} seconds for operation ID {OpId['OperationId']} to finish",
			      f"." * intervals_waited,
			      f"{sleep_interval * intervals_waited} seconds waited so far", end='\r')
			sleep(sleep_interval)
			intervals_waited += 1
			StackInstancesAreGone = check_stack_set_status(aws_acct, pOldStackSet, OpId['OperationId'])
			if not StackInstancesAreGone['Success']:
				sys.exit(f"There was a problem with removing the stack instances from stackset {pOldStackSet}. "
				         f"Exiting...")
		# For every 10 stack-ids:
		# **** 3. Import those stack-ids into the new stack-set, 10 at a time ****
		x = 0
		limit = StackInstancesImportedAtOnce
		while x < len(stack_ids['Stack_instances']):
			stack_ids_subset = [stack_ids['Stack_instances'][x + i] for i in range(limit) if
			                    x + i < len(stack_ids['Stack_instances'])]
			x += limit
			print(f"Importing {len(stack_ids_subset)} stacks into the new stackset now...")
			OpId = populate_new_stack_with_existing_stack_instances(aws_acct, stack_ids_subset, pNewStackSet)
			StackReadyToImport = check_stack_set_status(aws_acct, pNewStackSet, OpId['OperationId'])
			if not StackReadyToImport['Success']:
				sys.exit(
						f"There was a problem with importing the stack instances into stackset {pNewStackSet}. Exiting...")
			intervals_waited = 1
			while StackReadyToImport['StackSetStatus'] in ['RUNNING', 'QUEUED']:
				print(f"Waiting for StackSet {pNewStackSet} to finish importing", f"." * intervals_waited, end='\r')
				sleep(sleep_interval)
				intervals_waited += 1
				StackReadyToImport = check_stack_set_status(aws_acct, pNewStackSet, OpId['OperationId'])
				if not StackReadyToImport['Success']:
					sys.exit(
							f"There was a problem with importing the stack instances into stackset {pNewStackSet}. "
							f"Exiting...")
			logging.info(f"That import took {intervals_waited * sleep_interval} seconds to complete")
	else:
		"""
		1. Get all the info from the old stackset (template, parameters, capabilities, tags)
		2. Create the new stackset with all of those attributes
		3. Get the stack-ids from the old stack-set
		4. Remove the stack-instances from the old stack-set
		5. Import those stack-ids into the new stack-set, 10 at a time
		6. Verify that all the stack-instances made it over properly
		"""
		print("New Stack Set needs to be created...")
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
			pass
		else:
			logging.error(f"{pNewStackSet} failed to be created. Exiting...")
			sys.exit(99)
		# Use the OpId, to check if the empty new stackset has successfully been created
		logging.debug(f"Getting Stack Ids from existing stack set {pOldStackSet}")
		stack_ids = get_stack_ids_from_existing_stack_set(aws_acct, pOldStackSet)
		logging.debug(f"Found {len(stack_ids)} stack ids from stackset {pOldStackSet}")
		# For every 10 stack-ids, use the OpId below to verify that the Operation has finished:
		logging.debug(f"Removing ALL stack instances from stackset {pOldStackSet}")
		OpId = remove_stack_instances(aws_acct, stack_ids, pOldStackSet)
		logging.debug(f"Removed stack instances from {pOldStackSet}")
		StackInstancesAreGone = check_stack_set_status(aws_acct, pOldStackSet, OpId['OperationId'])
		if not StackInstancesAreGone['Success']:
			sys.exit(f"There was a problem with removing the stack instances from stackset {pOldStackSet}. Exiting...")
		logging.debug(f"The operation id {OpId['OperationId']} is {StackInstancesAreGone['StackSetStatus']}")
		intervals_waited = 1
		while StackInstancesAreGone['StackSetStatus'] in ['RUNNING']:
			print(f"Waiting {sleep_interval} seconds for operation ID {OpId['OperationId']} to finish",
			      f"." * intervals_waited,
			      f"{sleep_interval * intervals_waited} seconds waited so far", end='\r')
			sleep(sleep_interval)
			intervals_waited += 1
			StackInstancesAreGone = check_stack_set_status(aws_acct, pOldStackSet, OpId['OperationId'])
			if not StackInstancesAreGone['Success']:
				sys.exit(
					f"There was a problem with removing the stack instances from stackset {pOldStackSet}. Exiting...")
		x = 0
		limit = StackInstancesImportedAtOnce
		while x < len(stack_ids['Stack_instances']):
			stack_ids_subset = [stack_ids['Stack_instances'][x + i] for i in range(limit) if
			                    x + i < len(stack_ids['Stack_instances'])]
			x += limit
			print(f"Importing {len(stack_ids_subset)} stacks into the new stackset now...")
			OpId = populate_new_stack_with_existing_stack_instances(aws_acct, stack_ids_subset, pNewStackSet)
			StackReadyToImport = check_stack_set_status(aws_acct, pNewStackSet, OpId['OperationId'])
			if not StackReadyToImport['Success']:
				sys.exit(
					f"There was a problem with importing the stack instances into stackset {pNewStackSet}. Exiting...")
			intervals_waited = 1
			while StackReadyToImport['StackSetStatus'] in ['RUNNING', 'QUEUED']:
				print(f"Waiting for StackSet {pNewStackSet} to finish importing", f"." * intervals_waited, end='\r')
				sleep(sleep_interval)
				intervals_waited += 1
				StackReadyToImport = check_stack_set_status(aws_acct, pNewStackSet, OpId['OperationId'])
				if not StackReadyToImport['Success']:
					sys.exit(
						f"There was a problem with importing the stack instances into stackset {pNewStackSet}. Exiting...")
			logging.info(f"That import took {intervals_waited * sleep_interval} seconds to complete")
# Wait for Operation to be completed, so we don't try and run two at a time...
# while not operation_is_complete(aws_acct, OpId):
# 	print(".", end='\r')
# 	sleep(30)
else:  # Old Stackset doesn't exist - so there was a typo somewhere. Tell the user and exit
	print(f"It appears that the legacy stackset you provided {pOldStackSet} doesn't exist.\n"
	      f"Please check the spelling, or the account, and try again.")

print()
print("Thank you for using this script")
print()
