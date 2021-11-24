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
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Region
verbose = args.loglevel
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
# The time between checks to see if the stackset instances have been created, or imported...
sleep_interval = 5
# Currently, this is a hard-stop at 10, but I made it a variable in case they up the limit
stack_ids = dict()

"""
This script attempts to update a stack-set (like the ALZ stackset to the Control Tower Customizations StackSets) without any impact to the ultimate resources.
Here's what's needed:
	0. The new stackset must exist, since without it, we wouldn't need this script. 
	1. Determine the attributes of the existing stackset (this includes the body, description, tags, parameters and capabilities).
	2. Compare the attributes of the new and old stacksets. If there's NO difference, then we can exit safely with success,
	    otherwise we need to notify the user of the changes, and allow them to push the changes, if they want.
	3. We should check to see if the stackset runs to completion with the changes. If possible - we should report any errors that happen as well. 
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
			StackSetOperationStatus = client_cfn.describe_stack_set(StackSetName=fStack_set_name,
			                                         CallAs='SELF')['StackSet']
			return_response['StackSetName'] = fStack_set_name
			return_response['StackSetStatus'] = StackSetOperationStatus['Status']
			return_response['Success'] = True
			return (return_response)
		except client_cfn.exceptions.StackSetNotFoundException as myError:
			logging.error(f"Stack Set {fStack_set_name} Not Found: {myError}")
			return_response['StackSetName'] = fStack_set_name
			return_response['Success'] = False
			return (return_response)
	else:
		try:
			StackSetOperationStatus = client_cfn.describe_stack_set_operation(StackSetName=fStack_set_name,
			                                                                  OperationId=fOperationId,
			                                                                  CallAs='SELF')['StackSetOperation']
			return_response['StackSetOperationStatus'] = StackSetOperationStatus['Status']
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
		return_response['ErrorMessage'] = myError
		return_response['Success'] = False
	return (return_response)


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
		return_response['ErrorMessage'] = myError
		return_response['Success'] = False
	return (return_response)


def compare_stacksets(faws_acct, fExisting_stack_set_name, fNew_stack_set_name):
	"""
	The idea here is to compare the templates and parameters of the stacksets, to ensure that the import will succeed.
	"""

	return_response = {'Success'                : False,
	                   'TemplateComparison'     : False,
	                   'CapabilitiesComparison' : False,
	                   'ParametersComparison'   : False,
	                   'TagsComparison'         : False,
	                   'DescriptionComparison'  : False,
	                   'ExecutionRoleComparison': False}
	Stack_Set_Info_old = get_template_body_and_parameters(faws_acct, fExisting_stack_set_name)
	Stack_Set_Info_new = get_template_body_and_parameters(faws_acct, fNew_stack_set_name)
	# Time to compare - only the Template Body, Parameters, and Capabilities are critical to making sure the stackset works.
	return_response['TemplateComparison'] = (Stack_Set_Info_old['stack_set_info']['TemplateBody'] ==
	                                         Stack_Set_Info_new['stack_set_info']['TemplateBody'])
	return_response['CapabilitiesComparison'] = (Stack_Set_Info_old['stack_set_info']['Capabilities'] ==
	                                             Stack_Set_Info_new['stack_set_info']['Capabilities'])
	return_response['ParametersComparison'] = (Stack_Set_Info_old['stack_set_info']['Parameters'] ==
	                                           Stack_Set_Info_new['stack_set_info']['Parameters'])
	return_response['TagsComparison'] = (Stack_Set_Info_old['stack_set_info']['Tags'] ==
	                                     Stack_Set_Info_new['stack_set_info']['Tags'])
	try:
		return_response['DescriptionComparison'] = (Stack_Set_Info_old['stack_set_info']['Description'] ==
	                                            Stack_Set_Info_new['stack_set_info']['Description'])
	except KeyError as myError:
		logging.error(f"The 'Description' key is missing from one of your stacksets.\n"
		              f"Error: {myError}")
		return_response['DescriptionComparison'] = False
	return_response['ExecutionRoleComparison'] = (Stack_Set_Info_old['stack_set_info']['ExecutionRoleName'] ==
	                                              Stack_Set_Info_new['stack_set_info']['ExecutionRoleName'])

	if (return_response['TemplateComparison'] and return_response['CapabilitiesComparison'] and return_response['ParametersComparison']):
		return_response['Success'] = True
	return (return_response)


def update_stack_set_with_body_and_parameters(faws_acct, fTarget_stack_set_name, fStack_set_info):
	"""
	Request:
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

	Response:
	{
    'OperationId': 'string'
	}
	"""

	logging.info(
			f"Updating stackset {fTarget_stack_set_name} in account {faws_acct.acct_number} with a template body, parameters, capabilities, description and tagging from this:")
	logging.info(f"{fStack_set_info}")
	client_cfn = faws_acct.session.client('cloudformation')
	return_response = {'Success'   : None,
	                   'StackSetId': None}
	# TODO: We should change the template body to a template url to accommodate really big templates
	if 'Description' not in fStack_set_info.keys():
		fStack_set_info['Description'] = 'This is a Description'
	try:
		OperationId = client_cfn.update_stack_set(StackSetName=fTarget_stack_set_name,
		                                          TemplateBody=fStack_set_info['TemplateBody'],
		                                          Description=fStack_set_info['Description'],
		                                          Parameters=fStack_set_info['Parameters'],
		                                          Capabilities=fStack_set_info['Capabilities'],
		                                          Tags=fStack_set_info['Tags'],
		                                          OperationPreferences={
			                                          'RegionConcurrencyType'  : 'PARALLEL',
			                                          'FailureToleranceCount'  : 1,
			                                          'MaxConcurrentPercentage': 100
			                                          }
		                                          )
		# StackSetStatus = check_stack_set_status(faws_acct, fTarget_stack_set_name, OperationId)
		# return_response['StackSetId'] = OperationId['OperationId']
		# intervals_waited = 1
		# while StackSetStatus['StackSetOperationStatus'] in ['RUNNING']:
		# 	StackSetStatus = check_stack_set_status(faws_acct, fTarget_stack_set_name, OperationId)
		# 	print(f"Waiting for StackSet {fTarget_stack_set_name} to be ready - {sleep_interval * intervals_waited} second waited", end='\r')
		# 	sleep(sleep_interval)
		# 	intervals_waited += 1
		# if StackSetStatus['Success']:
		# 	return_response['Success'] = True
		# else:
		return_response['OperationId'] = OperationId['OperationId']
		return_response['Success'] = True
	# There is currently no waiter to use for this operation...
	except (client_cfn.exceptions.NameAlreadyExistsException,
	        client_cfn.exceptions.CreatedButModifiedException,
	        client_cfn.exceptions.LimitExceededException) as myError:
		logging.error(f"Operation Failed: {myError}")
		return_response['ErrorMessage'] = myError
		return_response['Success'] = False
	return (return_response)


def create_change_set_for_new_stack():
	"""
	Do we need to do this?
	"""


########################

aws_acct = aws_acct_access(pProfile)

# The following is just letting the user know what we're going to do in this script.
# Since this script is by nature intrusive, we want the user to confirm everything before they continue.
# Check to see if the new StackSet already exists, or we need to create it.
if find_if_stack_set_exists(aws_acct, pNewStackSet)['Success']:
	print(f"{Fore.GREEN}The 'New' Stackset {pNewStackSet} exists within the account {aws_acct.acct_number}{Fore.RESET}")
	NewStackSetExists = True
else:
	print(
			f"{Fore.RED}The 'New' Stackset {pNewStackSet} does not exist within the account {aws_acct.acct_number}{Fore.RESET}")
	print(
			f"This script is only used to update a stackset from another. Therefore, since the stackset {pNewStackSet} doesn't exist, we're exiting.")
	NewStackSetExists = False
	sys.exit(1)
# Check to see if the old StackSet exists, as they may have typed something wrong - or the recovery file was never deleted.
if find_if_stack_set_exists(aws_acct, pOldStackSet)['Success']:
	print(f"{Fore.GREEN}The 'Old' Stackset {pOldStackSet} exists within the account {aws_acct.acct_number}{Fore.RESET}")
	OldStackSetExists = True
else:
	print(
			f"{Fore.RED}The 'Old' Stackset {pOldStackSet} does not exist within the account {aws_acct.acct_number}{Fore.RESET}")
	print(
			f"This script is only used to update a stackset from another. Therefore, since the stackset {pOldStackSet} doesn't exist, we're exiting.")
	OldStackSetExists = False
	sys.exit(2)

if OldStackSetExists and NewStackSetExists:
	CompareTemplates = compare_stacksets(aws_acct, pOldStackSet, pNewStackSet)
else:
	print("Not sure how we got here... ")
	CompareTemplates = {'Success': False}
	sys.exit(19)
if CompareTemplates['TemplateComparison'] and CompareTemplates['CapabilitiesComparison'] \
		and CompareTemplates['ParametersComparison'] and CompareTemplates['TagsComparison'] \
		and CompareTemplates['DescriptionComparison'] and CompareTemplates['ExecutionRoleComparison']:
	print()
	print(
			f"{Fore.GREEN}The stacksets appear to match - so there's no need to update anything here... {Fore.RESET}Exiting")
	print()
	sys.exit(5)
elif not CompareTemplates['TemplateComparison'] and CompareTemplates['CapabilitiesComparison'] \
		and CompareTemplates['ParametersComparison']:
	print()
	print(
			f"{Fore.RED}Ok - there's something to do here. The templates or parameters or capabilities in the two stacksets you provided don't match{Fore.RESET}\n"
			f"I assume that's why you're using this script in the first place. {Fore.GREEN}Good{Fore.RESET}")
	print(f"Templates match: {CompareTemplates['TemplateComparison']}")
	print(f"Capabilities match: {CompareTemplates['CapabilitiesComparison']}")
	print(f"Parameters match: {CompareTemplates['ParametersComparison']}")
	print()
	print(f"You should look at the above analysis of the difference between the stacksets, and determine whether you're comfortable moving forward. "
	      f"If so, press 'Y' at the next prompt, and the {pOldStackSet} stackset will be updated to match the {pNewStackSet} stackset so that when \n"
	      f"you do migrate - the import will go smoothly, since the templates will already be the same.")
elif CompareTemplates['Success'] and not (CompareTemplates['TagsComparison'] and
                                          CompareTemplates['DescriptionComparison'] and
                                          CompareTemplates['ExecutionRoleComparison']):
	print()
	print(
			f"{Fore.CYAN}Ok - there {Style.BRIGHT}might{Style.NORMAL} be a problem here. While the templates, parameters and capabilities in the two stacksets you provided match\n{Fore.RESET}"
			f"Either the Description, the Tags, or the ExecutionRole is different between the two stacksets.\n"
			f"But I assume that's why you're using this script...")
	print(f"Tags match: {CompareTemplates['TagsComparison']}")
	print(f"Description match: {CompareTemplates['DescriptionComparison']}")
	print(f"ExecutionRole match: {CompareTemplates['ExecutionRoleComparison']}")
	print()
	print(f"You should look at the above analysis of the difference between the stacksets, and determine whether you're comfortable moving forward. "
	      f"If so, press 'Y' at the next prompt, and the {pOldStackSet} will be updated to match the {pNewStackSet}."
	      f"The templates, capabilities and parameters already match, so the migration should already go smoothly, "
	      f"but the tags, description and ExecutionRole may need to be updated separately"
	      f"- the import will go smoothly, since the templates will already be the same.")

print(
		f"By proceeding, you will update the {pOldStackSet} to match {pNewStackSet}'s attributes (Template, Parameters, Capabilities)")
User_Confirmation = (input(f"Do you want to proceed? (y/n): ") in ['y', 'Y'])
if not User_Confirmation:
	print(f"User cancelled script", file=sys.stderr)
	sys.exit(10)

if OldStackSetExists:
	if NewStackSetExists:
		"""
		1. We've already determined the differences between the stacksets. We've already determined (because they said yes)
			that they want to update the old stackset with the new stackset.
		2. Apply the updates
		3. Poll the stackset to make sure all stack instances update.
		4. Report on progress
		"""
		print()
		print(f"You've asked for us to update the existing stackset {pOldStackSet}"
		      f"using the new stackset called: {pNewStackSet}")
		Stack_Set_Info = get_template_body_and_parameters(aws_acct, pNewStackSet)
		OperationId = update_stack_set_with_body_and_parameters(aws_acct, pOldStackSet,
		                                                        Stack_Set_Info['stack_set_info'])
		print(f"Waiting for old stackset {pOldStackSet} to be updated")
		sleep(sleep_interval)
		StackSetStatus = check_stack_set_status(aws_acct, pOldStackSet, OperationId['OperationId'])
		intervals_waited = 1
		if StackSetStatus['Success']:
			while StackSetStatus['Success'] and not StackSetStatus['StackSetOperationStatus'] in ['SUCCEEDED']:
				print(f"Waiting for StackSet {pOldStackSet} to be ready - waited {intervals_waited * sleep_interval} seconds already", end='\r')
				sleep(sleep_interval)
				intervals_waited += 1
				StackSetStatus = check_stack_set_status(aws_acct, pOldStackSet, OperationId['OperationId'])
			print(f"{ERASE_LINE}Stackset {pOldStackSet} has been successfully updated")
			pass
		else:
			print(f"{pOldStackSet} failed to be created. Exiting...")
			sys.exit(99)

	# else:  # PNewStackSet *does* exist
	# 	"""
	# 	1. Get the stack-ids from the old stack-set - write them to a file (in case we need to recover the process)
	# 	"""
	# 	# First time this script has run...
	# 	print("New Stack Set already exists path...")

# 	""" ######## This code is common across both use-cases ################## """
# 	logging.debug(f"Getting Stack Ids from existing stack set {pOldStackSet}")
# 	# **** 1. Get the stack-ids from the old stack-set ****
# 	if Use_recovery_file:
# 		pass
# 	else:
# 		stack_ids = get_stack_ids_from_existing_stack_set(aws_acct, pOldStackSet, pAccountToMove)
# 	logging.debug(f"Found {len(stack_ids)} stack ids from stackset {pOldStackSet}")
# 	# Write the stack_ids info to a file, so we don't lose this info if the script fails
# 	fileresult = write_info_to_file(aws_acct, stack_ids)
# 	if not fileresult['Success']:
# 		print(f"Something went wrong.\n"
# 		      f"Error Message: {fileresult['ErrorMessage']}")
# 		sys.exit(9)
# 	# For every 10 stack-ids, use the OpId below to verify that the Operation has finished:
# 	# **** 2. Remove the stack-instances from the old stack-set ****
# 	logging.debug(f"Removing stack instances from stackset {pOldStackSet}")
# 	DisconnectStackInstances = disconnect_stack_instances(aws_acct, stack_ids, pOldStackSet)
# 	if not DisconnectStackInstances['Success']:
# 		if DisconnectStackInstances['ErrorMessage'].find('has no matching instances') > 0 and Use_recovery_file:
# 			pass  # This could be because the Old Stackset already had the instances disconnected when the script failed
# 		else:
# 			print(f"Failure... exiting due to: {DisconnectStackInstances['ErrorMessage']}")
# 			sys.exit(7)
# 	logging.debug(f"Removed stack instances from {pOldStackSet}")
# 	if DisconnectStackInstances['OperationId'] is not None:
# 		StackInstancesAreGone = check_stack_set_status(aws_acct, pOldStackSet, DisconnectStackInstances['OperationId'])
# 		if not StackInstancesAreGone['Success']:
# 			sys.exit(f"There was a problem with removing the stack instances from stackset {pOldStackSet}. Exiting...")
# 		logging.debug(
# 				f"The operation id {DisconnectStackInstances['OperationId']} is {StackInstancesAreGone['StackSetStatus']}")
# 		intervals_waited = 1
# 		while StackInstancesAreGone['StackSetStatus'] in ['RUNNING']:
# 			print(f"Waiting for stack instances to be disconnected from stackset {pOldStackSet} -",
# 			      # f"." * intervals_waited,
# 			      f"{sleep_interval * intervals_waited} seconds waited so far", end='\r')
# 			sleep(sleep_interval)
# 			intervals_waited += 1
# 			StackInstancesAreGone = check_stack_set_status(aws_acct, pOldStackSet,
# 			                                               DisconnectStackInstances['OperationId'])
# 		if not StackInstancesAreGone['Success']:
# 			print(f"There was a problem with removing the stack instances from stackset {pOldStackSet}. Exiting...")
# 			sys.exit(8)
# 	# For every 10 stack-ids:
# 	# **** 3. Import those stack-ids into the new stack-set, 10 at a time ****
# 	x = 0
# 	limit = StackInstancesImportedAtOnce
# 	while x < len(stack_ids['Stack_instances']):
# 		stack_ids_subset = [stack_ids['Stack_instances'][x + i] for i in range(limit) if
# 		                    x + i < len(stack_ids['Stack_instances'])]
# 		x += limit
# 		print(f"{ERASE_LINE}Importing {len(stack_ids_subset)} stacks into the new stackset now...")
# 		ReconnectStackInstances = populate_new_stack_with_existing_stack_instances(aws_acct, stack_ids_subset,
# 		                                                                           pNewStackSet)
# 		if not ReconnectStackInstances['Success']:
# 			print(f"Re-attaching the stack-instance to the new stackset seems to have failed."
# 			      f"The error received was: {ReconnectStackInstances['ErrorMessage']}")
# 			print(
# 					f"You'll have to resolve the issue that caused this problem, and then re-run this script using the recovery file.")
# 			sys.exit(9)
# 		StackReadyToImport = check_stack_set_status(aws_acct, pNewStackSet, ReconnectStackInstances['OperationId'])
# 		if not StackReadyToImport['Success']:
# 			sys.exit(f"There was a problem with importing the stack"
# 			         f" instances into stackset {pNewStackSet}. Exiting...")
# 		intervals_waited = 1
# 		while StackReadyToImport['StackSetStatus'] in ['RUNNING', 'QUEUED']:
# 			print(f"Waiting for StackSet {pNewStackSet} to finish importing -",
# 			      # f"." * intervals_waited,
# 			      f"{sleep_interval * intervals_waited} seconds waited so far", end='\r')
# 			sleep(sleep_interval)
# 			intervals_waited += 1
# 			StackReadyToImport = check_stack_set_status(aws_acct, pNewStackSet, ReconnectStackInstances['OperationId'])
# 			if not StackReadyToImport['Success']:
# 				sys.exit(
# 						f"There was a problem with importing the stack instances into stackset {pNewStackSet}. Exiting...")
# 		logging.info(f"{ERASE_LINE}That import took {intervals_waited * sleep_interval} seconds to complete")
#
# else:  # Old Stackset doesn't exist - so there was a typo somewhere. Tell the user and exit
# 	print(f"It appears that the legacy stackset you provided {pOldStackSet} doesn't exist.\n"
# 	      f"Please check the spelling, or the account, and try again.\n\n"
# 	      f"{Fore.LIGHTBLUE_EX}Perhaps the recovery file was never deleted?{Fore.RESET}")

print()
print("Thank you for using this tool")
print()
