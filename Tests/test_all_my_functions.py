from botocore import client
import pytest
from datetime import datetime
from dateutil.tz import tzutc, tzlocal

from all_my_functions import all_my_functions, fix_my_functions
from Inventory_Modules import get_all_credentials


def _amend_make_api_call(test_key, test_value, mocker):
	orig = client.BaseClient._make_api_call

	def amend_make_api_call(self, operation_name, kwargs):
		# Intercept boto3 operations for <secretsmanager.get_secret_value>. Optionally, you can also
		# check on the argument <SecretId> and control how you want the response would be. This is
		# a very flexible solution as you have full control over the whole process of fetching a
		# secret.
		if operation_name == 'ListFunctions':
			if isinstance(test_value, Exception):
				raise test_value
			# Implied break and exit of the function here...
			print(f"Operation Name mocked: {operation_name}\n"
			      f"Key Name: {test_key}\n"
			      f"kwargs: {kwargs}\n"
			      f"mocked return_response: {test_value}")
			return test_value
		elif operation_name == 'ListAccounts':
			if isinstance(test_value, Exception):
				raise test_value
			# Implied break and exit of the function here...
			print(f"Operation Name mocked: {operation_name}\n"
			      f"Key Name: {test_key}\n"
			      f"kwargs: {kwargs}\n"
			      f"mocked return_response: {test_value}")
			return test_value
		# elif operation_name == 'AssumeRole':
		# 	if isinstance(test_value, Exception):
		# 		raise test_value
		# 	# Implied break and exit of the function here...
		# 	print(f"Operation Name mocked: {operation_name}\n"
		# 	      f"Key Name: {test_key}\n"
		# 	      f"kwargs: {kwargs}\n"
		# 	      f"mocked return_response: {test_value}")
		# 	return test_value

		return_response = orig(self, operation_name, kwargs)
		print(f"Operation Name passed through: {operation_name}\n"
		      f"Key Name: {test_key}\n"
		      f"kwargs: {kwargs}\n"
		      f"Actual return_response: {return_response}")
		return return_response

	mocker.patch('botocore.client.BaseClient._make_api_call', new=amend_make_api_call)


parameters1 = {
	'pProfiles'    : ['LZRoot'],
	'pRegionList'  : ['us-east-1', 'eu-west-1', 'me-south-1'],
	'pSkipProfiles': [],
	'pSkipAccounts': [],
	'pRoleList'    : [],
	'pAccountList' : [],
	'pTiming'      : True,
	'pRootOnly'    : False,
	'pSaveFilename': None,
	'pShortform'   : False,
	'pverbose'     : 20}

RootOnlyParams = {
	'pProfiles'    : ['LZRoot'],
	'pSkipProfiles': [],
	'pAccountList' : [],
	'pTiming'      : True,
	'pRootOnly'    : True,
	'pSaveFilename': None,
	'pShortform'   : False,
	'pverbose'     : 50}
# Below is 10 Credentials
CredentialResponseData = [
	# Management Account Credentials
	{'ParentAcctId' : '111122223333', 'MgmtAccount': '111122223333', 'OrgType': 'Root',
	 'AccessKeyId'  : '*****AccessKeyHere*****', 'SecretAccessKey': '*****SecretAccessKeyHere*****', 'SessionToken': None,
	 'AccountNumber': '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1',
	 'AccountStatus': 'ACTIVE', 'RolesTried': None, 'Role': 'Use Profile', 'Profile': 'LZRoot', 'AccessError': False, 'Success': True,
	 'ErrorMessage' : None, 'ParentProfile': 'LZRoot'},
	# Child Accounts Credentials
	{'AccessKeyId'  : '*****AccessKeyHere*****', 'SecretAccessKey': '*****SecretAccessKeyHere*****', 'SessionToken': '*****SessionTokenHere*****',
	 'Expiration'   : datetime(2023, 9, 8, 1, 30, tzinfo=tzutc()), 'ParentAcctId': '111122223333',
	 'MgmtAccount'  : '111122223333',
	 'OrgType'      : 'Child', 'AccountNumber': '111111111111', 'AccountId': '111111111111', 'Region': 'us-east-1',
	 'AccountStatus': 'ACTIVE', 'RolesTried': None, 'Role': 'AWSCloudFormationStackSetExecutionRole', 'Profile': None,
	 'AccessError'  : False, 'ErrorMessage': None, 'Success': True, 'ParentProfile': 'LZRoot'},
	{'AccessKeyId'  : '*****AccessKeyHere*****', 'SecretAccessKey': '*****SecretAccessKeyHere*****', 'SessionToken': '*****SessionTokenHere*****',
	 'Expiration'   : datetime(2023, 9, 8, 1, 30, tzinfo=tzutc()), 'ParentAcctId': '111122223333',
	 'MgmtAccount'  : '111122223333',
	 'OrgType'      : 'Child', 'AccountNumber': '222222222222', 'AccountId': '222222222222', 'Region': 'us-east-1',
	 'AccountStatus': 'ACTIVE', 'RolesTried': None, 'Role': 'AWSCloudFormationStackSetExecutionRole', 'Profile': None,
	 'AccessError'  : False, 'ErrorMessage': None, 'Success': True, 'ParentProfile': 'LZRoot'},
	{'AccessKeyId'  : '*****AccessKeyHere*****', 'SecretAccessKey': '*****SecretAccessKeyHere*****', 'SessionToken': '*****SessionTokenHere*****',
	 'Expiration'   : datetime(2023, 9, 8, 1, 30, 18, tzinfo=tzutc()), 'ParentAcctId': '111122223333',
	 'MgmtAccount'  : '111122223333',
	 'OrgType'      : 'Child', 'AccountNumber': '333333333333', 'AccountId': '333333333333', 'Region': 'us-east-1', 'AccountStatus': 'ACTIVE',
	 'RolesTried'   : None,
	 'Role'         : 'AWSCloudFormationStackSetExecutionRole', 'Profile': None, 'AccessError': False, 'ErrorMessage': None, 'Success': True,
	 'ParentProfile': 'LZRoot'},
	{'AccessKeyId' : '*****AccessKeyHere*****', 'SecretAccessKey': '*****SecretAccessKeyHere*****', 'SessionToken': '*****SessionTokenHere*****',
	 'Expiration'  : datetime(2023, 9, 8, 1, 30, tzinfo=tzutc()), 'ParentAcctId': '111122223333',
	 'MgmtAccount' : '111122223333', 'OrgType': 'Child', 'AccountNumber': '444444444444', 'AccountId': '444444444444',
	 'Region'      : 'us-east-1', 'AccountStatus': 'ACTIVE', 'RolesTried': None,
	 'Role'        : 'AWSCloudFormationStackSetExecutionRole', 'Profile': None, 'AccessError': False,
	 'ErrorMessage': None, 'Success': True, 'ParentProfile': 'LZRoot'},
	{'AccessKeyId'  : '*****AccessKeyHere*****', 'SecretAccessKey': '*****SecretAccessKeyHere*****', 'SessionToken': '*****SessionTokenHere*****',
	 'Expiration'   : datetime(2023, 9, 8, 1, 30, tzinfo=tzutc()), 'ParentAcctId': '111122223333',
	 'MgmtAccount'  : '111122223333',
	 'OrgType'      : 'Child', 'AccountNumber': '555555555555', 'AccountId': '555555555555', 'Region': 'us-east-1', 'AccountStatus': 'ACTIVE',
	 'RolesTried'   : None,
	 'Role'         : 'AWSCloudFormationStackSetExecutionRole', 'Profile': None, 'AccessError': False, 'ErrorMessage': None, 'Success': True,
	 'ParentProfile': 'LZRoot'},
	{'AccessKeyId'  : '*****AccessKeyHere*****', 'SecretAccessKey': '*****SecretAccessKeyHere*****', 'SessionToken': '*****SessionTokenHere*****',
	 'Expiration'   : datetime(2023, 9, 8, 1, 30, tzinfo=tzutc()), 'ParentAcctId': '111122223333',
	 'MgmtAccount'  : '111122223333',
	 'OrgType'      : 'Child', 'AccountNumber': '666666666666', 'AccountId': '666666666666', 'Region': 'us-east-1',
	 'AccountStatus': 'ACTIVE', 'RolesTried': None, 'Role': 'AWSCloudFormationStackSetExecutionRole', 'Profile': None,
	 'AccessError'  : False, 'ErrorMessage': None, 'Success': True, 'ParentProfile': 'LZRoot'},
	{'AccessKeyId'  : '*****AccessKeyHere*****', 'SecretAccessKey': '*****SecretAccessKeyHere*****', 'SessionToken': '*****SessionTokenHere*****',
	 'Expiration'   : datetime(2023, 9, 8, 1, 30, tzinfo=tzutc()), 'ParentAcctId': '111122223333',
	 'MgmtAccount'  : '111122223333',
	 'OrgType'      : 'Child', 'AccountNumber': '777777777777', 'AccountId': '777777777777', 'Region': 'us-east-1', 'AccountStatus': 'ACTIVE',
	 'RolesTried'   : None,
	 'Role'         : 'AWSCloudFormationStackSetExecutionRole', 'Profile': None, 'AccessError': False, 'ErrorMessage': None, 'Success': True,
	 'ParentProfile': 'LZRoot'},
	{'AccessKeyId'  : '*****AccessKeyHere*****', 'SecretAccessKey': '*****SecretAccessKeyHere*****', 'SessionToken': '*****SessionTokenHere*****',
	 'Expiration'   : datetime(2023, 9, 8, 1, 30, tzinfo=tzutc()), 'ParentAcctId': '111122223333',
	 'MgmtAccount'  : '111122223333',
	 'OrgType'      : 'Child', 'AccountNumber': '888888888888', 'AccountId': '888888888888', 'Region': 'us-east-1',
	 'AccountStatus': 'ACTIVE', 'RolesTried': None, 'Role': 'AWSCloudFormationStackSetExecutionRole', 'Profile': None,
	 'AccessError'  : False, 'ErrorMessage': None, 'Success': True, 'ParentProfile': 'LZRoot'},
	{'AccessKeyId'  : '*****AccessKeyHere*****', 'SecretAccessKey': '*****SecretAccessKeyHere*****', 'SessionToken': '*****SessionTokenHere*****',
	 'Expiration'   : datetime(2023, 9, 8, 1, 30, tzinfo=tzutc()), 'ParentAcctId': '111122223333',
	 'MgmtAccount'  : '111122223333',
	 'OrgType'      : 'Child', 'AccountNumber': '999999999999', 'AccountId': '999999999999', 'Region': 'us-east-1', 'AccountStatus': 'ACTIVE',
	 'RolesTried'   : None, 'Role': 'AWSCloudFormationStackSetExecutionRole', 'Profile': None, 'AccessError': False, 'ErrorMessage': None, 'Success': True,
	 'ParentProfile': 'LZRoot'}]
function_parameters1 = {
	'CredentialList': CredentialResponseData,
	'pFragments'    : ['python3.9', 'Metric'],
	'pverbose'      : 20
}
# 20 functions below - all meeting the filter criteria of either being runtime 'python3.9' or with the fragment 'Metric' in the name, all within one account, within one region (us-east-1).
function_response_data = {
	'Functions': [
		{'FunctionName' : 'AccountAssessmentStack-ResourceBasedPolicyValidate-tziul2Otm32F',
		 'FunctionArn' : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-ResourceBasedPolicyValidate-tziul2Otm32F',
		 'Runtime' : 'python3.9',
		 'Role': 'arn:aws:iam::111122223333:role/paulbaye-us-east-1-ValidateSpokeAccountAccess',
		 'Handler' : 'resource_based_policy/step_functions_lambda/validate_account_access.lambda_handler',
		 'CodeSize': 17578832,
		 'Description' : '',
		 'Timeout': 900,
		 'MemorySize': 1024,
		 'LastModified': '2023-04-14T15:01:53.312+0000',
		 'CodeSha256' : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=',
		 'Version': '$LATEST',
		 'Environment': {
			'Variables': {'SPOKE_ROLE_NAME': 'paulbaye-us-east-1-AccountAssessment-Spoke-ExecutionRole',
			              'POWERTOOLS_SERVICE_NAME': 'ScanResourceBasedPolicy',
			              'SEND_ANONYMOUS_DATA': 'Yes',
			              'TIME_TO_LIVE_IN_DAYS': '90',
			              'STACK_ID'       : 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7',
			              'TABLE_JOBS': 'AccountAssessmentStack-JobHistoryTableE4B293DD-1QRBBBDKUU8G9',
			              'COMPONENT_TABLE': 'AccountAssessmentStack-ResourceBasedPolicyTable7277C643-13R1K510AXFDB',
			              'LOG_LEVEL': 'INFO',
			              'SOLUTION_VERSION': 'v1.0.3'
			}
		 },
		 'TracingConfig': {'Mode': 'Active'},
		 'RevisionId': '6e9ec792-08c6-491d-aa19-aad57aeab78d',
		 'PackageType': 'Zip',
		 'Architectures' : ['x86_64'],
		 'EphemeralStorage': {'Size': 512},
		 'SnapStart': {'ApplyOn': 'None',
		               'OptimizationStatus': 'Off'
		               }
		 },
		{'FunctionName'                                                                                                                                                                    : 'AccountAssessmentStack-TrustedAccessStartScan70308-LfEGZM07HEP6',
		 'FunctionArn'                                                                                                                                                                     : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-TrustedAccessStartScan70308-LfEGZM07HEP6',
		 'Runtime'                                                                                                                                                                         : 'python3.9', 'Role': 'arn:aws:iam::111122223333:role/paulbaye-us-east-1-TrustedAccess',
		 'Handler'                                                                                                                                                                         : 'trusted_access_enabled_services/scan_for_trusted_services.lambda_handler', 'CodeSize': 17578832,
		 'Description'                                                                                                                                                                     : '', 'Timeout': 120, 'MemorySize': 128, 'LastModified': '2023-04-14T15:01:53.914+0000',
		 'CodeSha256'                                                                                                                                                                      : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=', 'Version': '$LATEST', 'Environment': {
			'Variables': {'POWERTOOLS_SERVICE_NAME': 'ScanTrustedAccess', 'SEND_ANONYMOUS_DATA': 'Yes', 'ORG_MANAGEMENT_ROLE_NAME': 'paulbaye-us-east-1-AccountAssessment-OrgMgmtStackRole', 'TIME_TO_LIVE_IN_DAYS': '90',
			              'STACK_ID'               : 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7', 'TABLE_JOBS': 'AccountAssessmentStack-JobHistoryTableE4B293DD-1QRBBBDKUU8G9',
			              'COMPONENT_TABLE'        : 'AccountAssessmentStack-TrustedAccessTable495B447A-GTR0RYDUJU5Q', 'LOG_LEVEL': 'INFO', 'SOLUTION_VERSION': 'v1.0.3'}}, 'TracingConfig': {'Mode': 'Active'}, 'RevisionId': '943aca8c-3984-45cb-97ce-fd3e2a8f7c03', 'PackageType': 'Zip',
		 'Architectures'                                                                                                                                                                   : ['x86_64'], 'EphemeralStorage': {'Size': 512}, 'SnapStart': {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName' : 'lock_down_stacks_sets_role', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:lock_down_stacks_sets_role', 'Runtime': 'python3.9', 'Role': 'arn:aws:iam::111122223333:role/service-role/lock_down_stacks_sets_role-role-pgehgfag',
		 'Handler'      : 'lambda_function.lambda_handler', 'CodeSize': 299, 'Description': '', 'Timeout': 3, 'MemorySize': 128, 'LastModified': '2023-09-06T15:50:05.000+0000', 'CodeSha256': 'fI06ZlRH/KN6Ra3twvdRllUYaxv182Tjx0qNWNlKIhI=', 'Version': '$LATEST',
		 'TracingConfig': {'Mode': 'PassThrough'},
		 'RevisionId'   : 'ec0a7b23-c892-4dc8-935c-954bf6990bf5', 'PackageType': 'Zip', 'Architectures': ['x86_64'], 'EphemeralStorage': {'Size': 512}, 'SnapStart': {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName': 'PrintOutEvents_Function', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:PrintOutEvents_Function', 'Runtime': 'python3.8', 'Role': 'arn:aws:iam::111122223333:role/service-role/PrintOutEvents_Function-role-p29wwswh',
		 'Handler'     : 'lambda_function.lambda_handler',
		 'CodeSize'    : 309, 'Description': '', 'Timeout': 3, 'MemorySize': 128, 'LastModified': '2023-02-03T20:41:15.016+0000', 'CodeSha256': 'O3OGwvaAIbPJr4rqhF1OZuuDThX1qcaCGGEekuse8OY=', 'Version': '$LATEST', 'TracingConfig': {'Mode': 'PassThrough'},
		 'RevisionId'  : 'cfeb671f-f08d-4217-8263-b5110101baf9', 'PackageType': 'Zip', 'Architectures': ['x86_64'], 'EphemeralStorage': {'Size': 512}, 'SnapStart': {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName'                                                                                                                                                                                                                                         : 'AccountAssessmentStack-ResourceBasedPolicyFinishAs-n8TanL9sDr9r',
		 'FunctionArn'                                                                                                                                                                                                                                          : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-ResourceBasedPolicyFinishAs-n8TanL9sDr9r',
		 'Runtime'                                                                                                                                                                                                                                              : 'python3.9',
		 'Role'                                                                                                                                                                                                                                                 : 'arn:aws:iam::111122223333:role/AccountAssessmentStack-ResourceBasedPolicyFinishAs-1RO9MOHKM92VA',
		 'Handler'                                                                                                                                                                                                                                              : 'resource_based_policy/finish_scan.lambda_handler',
		 'CodeSize'                                                                                                                                                                                                                                             : 17578832, 'Description': '',
		 'Timeout'                                                                                                                                                                                                                                              : 60,
		 'MemorySize'                                                                                                                                                                                                                                           : 128,
		 'LastModified'                                                                                                                                                                                                                                         : '2023-04-14T15:01:53.878+0000',
		 'CodeSha256'                                                                                                                                                                                                                                           : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=',
		 'Version'                                                                                                                                                                                                                                              : '$LATEST', 'Environment': {
			'Variables': {'POWERTOOLS_SERVICE_NAME': 'FinishScanForResourceBasedPolicies', 'SEND_ANONYMOUS_DATA': 'Yes', 'TIME_TO_LIVE_IN_DAYS': '90', 'STACK_ID': 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7',
			              'TABLE_JOBS'             : 'AccountAssessmentStack-JobHistoryTableE4B293DD-1QRBBBDKUU8G9', 'COMPONENT_TABLE': 'AccountAssessmentStack-ResourceBasedPolicyTable7277C643-13R1K510AXFDB', 'SOLUTION_VERSION': 'v1.0.3'}}, 'TracingConfig': {'Mode': 'Active'},
		 'RevisionId'                                                                                                                                                                                                                                           : 'e422e2e3-de5b-4a1d-b1f1-09b6125d230e',
		 'PackageType'                                                                                                                                                                                                                                          : 'Zip', 'Architectures': ['x86_64'],
		 'EphemeralStorage'                                                                                                                                                                                                                                     : {'Size': 512},
		 'SnapStart'                                                                                                                                                                                                                                            : {'ApplyOn'           : 'None',
		                                                                                                                                                                                                                                                           'OptimizationStatus': 'Off'}},
		{'FunctionName'                                                                                                                                                                      : 'AccountAssessmentStack-DelegatedAdminsStartScanE7D-Qk14ANSD75ay',
		 'FunctionArn'                                                                                                                                                                       : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-DelegatedAdminsStartScanE7D-Qk14ANSD75ay',
		 'Runtime'                                                                                                                                                                           : 'python3.9', 'Role': 'arn:aws:iam::111122223333:role/paulbaye-us-east-1-DelegatedAdmin',
		 'Handler'                                                                                                                                                                           : 'delegated_admins/scan_for_delegated_admins.lambda_handler', 'CodeSize': 17578832, 'Description': '',
		 'Timeout'                                                                                                                                                                           : 120, 'MemorySize': 128, 'LastModified': '2023-04-14T15:01:52.995+0000',
		 'CodeSha256'                                                                                                                                                                        : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=', 'Version': '$LATEST', 'Environment': {
			'Variables': {'POWERTOOLS_SERVICE_NAME': 'ScanDelegatedAdmin', 'SEND_ANONYMOUS_DATA': 'Yes', 'ORG_MANAGEMENT_ROLE_NAME': 'paulbaye-us-east-1-AccountAssessment-OrgMgmtStackRole', 'TIME_TO_LIVE_IN_DAYS': '90',
			              'STACK_ID'               : 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7', 'TABLE_JOBS': 'AccountAssessmentStack-JobHistoryTableE4B293DD-1QRBBBDKUU8G9',
			              'COMPONENT_TABLE'        : 'AccountAssessmentStack-DelegatedAdminsTable29E80916-F34FK4FZGFP5', 'LOG_LEVEL': 'INFO', 'SOLUTION_VERSION': 'v1.0.3'}}, 'TracingConfig': {'Mode': 'Active'}, 'RevisionId': 'd3fdc6a8-35b5-44b6-ae21-a533eea3f478', 'PackageType': 'Zip',
		 'Architectures'                                                                                                                                                                     : ['x86_64'], 'EphemeralStorage': {'Size': 512},
		 'SnapStart'                                                                                                                                                                         : {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName': 'UpsertDNSNameLambda', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:UpsertDNSNameLambda', 'Runtime': 'python3.9', 'Role': 'arn:aws:iam::111122223333:role/UpsertDNSNameToSQSQueueLambdaRole', 'Handler': 'Route53PHZLambdaUpdate.lambda_handler',
		 'CodeSize'    : 2164,
		 'Description' : 'Lambda to to update DNS Hosted Zone for EC2 starts', 'Timeout': 20, 'MemorySize': 256, 'LastModified': '2023-02-04T02:25:54.603+0000', 'CodeSha256': 'RC3e1d8z3DRLwxRK32sVJ+VoPpsBCRNZLPWzKLgqoHE=', 'Version': '$LATEST',
		 'Environment' : {'Variables': {'HOSTED_ZONE_ID': 'Z06954483PM26JFJ0ET4L', 'CENTRAL_ACCT': '111111111111', 'QUEUE_NAME': 'myDNSUpsertQueue', 'TIME_TO_LIVE': '300', 'LOG_LEVEL': 'INFO'}}, 'TracingConfig': {'Mode': 'PassThrough'}, 'RevisionId': 'bbfc8a57-67de-426f-a63d-08996b688bd8',
		 'Layers'      : [{'Arn': 'arn:aws:lambda:us-east-1:111122223333:layer:DistributedBoto3Library:9', 'CodeSize': 12119917}], 'PackageType': 'Zip', 'Architectures': ['x86_64'], 'EphemeralStorage': {'Size': 512}, 'SnapStart': {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName'                                                                                                                                                                   : 'AccountAssessmentStack-ResourceBasedPolicyScanSpok-xWlINDye4FUd',
		 'FunctionArn'                                                                                                                                                                    : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-ResourceBasedPolicyScanSpok-xWlINDye4FUd',
		 'Runtime'                                                                                                                                                                        : 'python3.9', 'Role': 'arn:aws:iam::111122223333:role/paulbaye-us-east-1-ScanSpokeResource',
		 'Handler'                                                                                                                                                                        : 'resource_based_policy/step_functions_lambda/scan_policy_all_services_router.lambda_handler',
		 'CodeSize'                                                                                                                                                                       : 17578832,
		 'Description'                                                                                                                                                                    : '', 'Timeout': 900, 'MemorySize': 512, 'LastModified': '2023-04-14T15:01:54.774+0000',
		 'CodeSha256'                                                                                                                                                                     : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=', 'Version': '$LATEST', 'Environment': {
			'Variables': {'SPOKE_ROLE_NAME': 'paulbaye-us-east-1-AccountAssessment-Spoke-ExecutionRole', 'POWERTOOLS_SERVICE_NAME': 'ScanResourceBasedPolicyInSpokeAccount', 'SEND_ANONYMOUS_DATA': 'Yes', 'TIME_TO_LIVE_IN_DAYS': '90',
			              'STACK_ID'       : 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7', 'TABLE_JOBS': 'AccountAssessmentStack-JobHistoryTableE4B293DD-1QRBBBDKUU8G9',
			              'COMPONENT_TABLE': 'AccountAssessmentStack-ResourceBasedPolicyTable7277C643-13R1K510AXFDB', 'LOG_LEVEL': 'INFO', 'SOLUTION_VERSION': 'v1.0.3'}}, 'TracingConfig': {'Mode': 'Active'}, 'RevisionId': '5d2d6891-e38f-4038-a5c6-fd0be145f34e', 'PackageType': 'Zip',
		 'Architectures'                                                                                                                                                                  : ['x86_64'], 'EphemeralStorage': {'Size': 512}, 'SnapStart': {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName': 'vpc-mappings-111122223333', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:vpc-mappings-111122223333', 'Runtime': 'python3.9', 'Role': 'arn:aws:iam::111122223333:role/AZ-Mapping-LambdaIAMRole-1MWVK82KVY9O5', 'Handler': 'index.lambda_handler',
		 'CodeSize'    : 1711,
		 'Description' : 'Stores VPC mappings into parameter store', 'Timeout': 5, 'MemorySize': 128, 'LastModified': '2023-09-06T16:44:28.000+0000', 'CodeSha256': 'H1vz9hfL3eHL/GigRMwy5E7ngxFl1XHzaSP5Dai3M8Y=', 'Version': '$LATEST', 'TracingConfig': {'Mode': 'PassThrough'},
		 'RevisionId'  : '14153c9e-b5d0-4e0a-9d18-93868f7dd1ae', 'PackageType': 'Zip', 'Architectures': ['x86_64'], 'EphemeralStorage': {'Size': 512}, 'SnapStart': {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName'                                                                                                                                                                                                                                         : 'AccountAssessmentStack-ResourceBasedPolicyReadDC5D-4fhaK4485acJ',
		 'FunctionArn'                                                                                                                                                                                                                                          : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-ResourceBasedPolicyReadDC5D-4fhaK4485acJ',
		 'Runtime'                                                                                                                                                                                                                                              : 'python3.9',
		 'Role'                                                                                                                                                                                                                                                 : 'arn:aws:iam::111122223333:role/AccountAssessmentStack-ResourceBasedPolicyReadServ-12WZ14XZFTC18',
		 'Handler'                                                                                                                                                                                                                                              : 'resource_based_policy/read_resource_based_policies.lambda_handler',
		 'CodeSize'                                                                                                                                                                                                                                             : 17578832, 'Description': '',
		 'Timeout'                                                                                                                                                                                                                                              : 60,
		 'MemorySize'                                                                                                                                                                                                                                           : 128,
		 'LastModified'                                                                                                                                                                                                                                         : '2023-04-14T15:01:53.924+0000',
		 'CodeSha256'                                                                                                                                                                                                                                           : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=',
		 'Version'                                                                                                                                                                                                                                              : '$LATEST', 'Environment': {
			'Variables': {'POWERTOOLS_SERVICE_NAME': 'ReadResourceBasedPolicy', 'SEND_ANONYMOUS_DATA': 'Yes', 'STACK_ID': 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7',
			              'TABLE_JOBS'             : 'AccountAssessmentStack-JobHistoryTableE4B293DD-1QRBBBDKUU8G9', 'COMPONENT_TABLE': 'AccountAssessmentStack-ResourceBasedPolicyTable7277C643-13R1K510AXFDB', 'SOLUTION_VERSION': 'v1.0.3'}}, 'TracingConfig': {'Mode': 'Active'},
		 'RevisionId'                                                                                                                                                                                                                                           : 'fe607630-2342-4d09-98d2-cee63552cb05',
		 'PackageType'                                                                                                                                                                                                                                          : 'Zip', 'Architectures': ['x86_64'],
		 'EphemeralStorage'                                                                                                                                                                                                                                     : {'Size': 512},
		 'SnapStart'                                                                                                                                                                                                                                            : {'ApplyOn'           : 'None',
		                                                                                                                                                                                                                                                           'OptimizationStatus': 'Off'}},
		{'FunctionName': 'Fix_Default_SGs', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:Fix_Default_SGs', 'Runtime': 'python3.9', 'Role': 'arn:aws:iam::111122223333:role/service-role/Fix_Default_SGs-role-qc5pamya', 'Handler': 'lambda_function.lambda_handler', 'CodeSize': 740,
		 'Description' : '', 'Timeout': 3, 'MemorySize': 128, 'LastModified': '2023-09-06T16:33:20.000+0000', 'CodeSha256': 'XZF1c2Xfl/YT+twYFVmlAGGuuNTO7i3J2FTCMoqFVew=', 'Version': '$LATEST', 'TracingConfig': {'Mode': 'PassThrough'}, 'RevisionId': 'c60151c0-f460-4dfe-98b5-47f6710447b8',
		 'PackageType' : 'Zip', 'Architectures': ['x86_64'], 'EphemeralStorage': {'Size': 512}, 'SnapStart': {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName'                                                                                                                                                                                          : 'AccountAssessmentStack-ResourceBasedPolicyStartSca-RU8utlGVjJyc',
		 'FunctionArn'                                                                                                                                                                                           : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-ResourceBasedPolicyStartSca-RU8utlGVjJyc',
		 'Runtime'                                                                                                                                                                                               : 'python3.9',
		 'Role'                                                                                                                                                                                                  : 'arn:aws:iam::111122223333:role/paulbaye-us-east-1-ResourceBasedPolicy',
		 'Handler'                                                                                                                                                                                               : 'resource_based_policy/start_state_machine_execution_to_scan_services.lambda_handler',
		 'CodeSize'                                                                                                                                                                                              : 17578832, 'Description': '', 'Timeout': 120, 'MemorySize': 128,
		 'LastModified'                                                                                                                                                                                          : '2023-04-14T15:02:10.418+0000',
		 'CodeSha256'                                                                                                                                                                                            : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=', 'Version': '$LATEST', 'Environment': {
			'Variables': {'POWERTOOLS_SERVICE_NAME'               : 'ScanResourceBasedPolicy', 'SEND_ANONYMOUS_DATA': 'Yes', 'ORG_MANAGEMENT_ROLE_NAME': 'paulbaye-us-east-1-AccountAssessment-OrgMgmtStackRole',
			              'SCAN_RESOURCE_POLICY_STATE_MACHINE_ARN': 'arn:aws:states:us-east-1:111122223333:stateMachine:ResourceBasedPolicyScanAllSpokeAccounts38C6FB6E-hEkgjewVuwLc', 'TIME_TO_LIVE_IN_DAYS': '90',
			              'STACK_ID'                              : 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7', 'TABLE_JOBS': 'AccountAssessmentStack-JobHistoryTableE4B293DD-1QRBBBDKUU8G9',
			              'COMPONENT_TABLE'                       : 'AccountAssessmentStack-ResourceBasedPolicyTable7277C643-13R1K510AXFDB', 'LOG_LEVEL': 'INFO', 'SOLUTION_VERSION': 'v1.0.3'}}, 'TracingConfig': {'Mode': 'Active'}, 'RevisionId': '4d80914c-9423-435d-b1fe-d48125ea064d',
		 'PackageType'                                                                                                                                                                                           : 'Zip', 'Architectures': ['x86_64'], 'EphemeralStorage': {'Size': 512},
		 'SnapStart'                                                                                                                                                                                             : {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName'                                                                                                                                                                           : 'AccountAssessmentStack-ResourceBasedPolicyReadScan-DbzA0NZGeTb3',
		 'FunctionArn'                                                                                                                                                                            : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-ResourceBasedPolicyReadScan-DbzA0NZGeTb3',
		 'Runtime'                                                                                                                                                                                : 'python3.9',
		 'Role'                                                                                                                                                                                   : 'arn:aws:iam::111122223333:role/AccountAssessmentStack-ResourceBasedPolicyReadScan-14UZV70G67KSO',
		 'Handler'                                                                                                                                                                                : 'resource_based_policy/supported_configuration/scan_configurations.lambda_handler',
		 'CodeSize'                                                                                                                                                                               : 17578832,
		 'Description'                                                                                                                                                                            : '', 'Timeout': 600, 'MemorySize': 128, 'LastModified': '2023-04-14T15:01:54.572+0000',
		 'CodeSha256'                                                                                                                                                                             : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=', 'Version': '$LATEST', 'Environment': {
			'Variables': {'POWERTOOLS_SERVICE_NAME': 'ReadScanConfigs', 'SEND_ANONYMOUS_DATA': 'Yes', 'STACK_ID': 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7',
			              'COMPONENT_TABLE'        : 'AccountAssessmentStack-ResourceBasedPolicyTable7277C643-13R1K510AXFDB', 'LOG_LEVEL': 'INFO', 'SOLUTION_VERSION': 'v1.0.3'}}, 'TracingConfig': {'Mode': 'Active'}, 'RevisionId': 'b0f59e30-6d16-4368-80b2-27ed25d16d1e', 'PackageType': 'Zip',
		 'Architectures'                                                                                                                                                                          : ['x86_64'], 'EphemeralStorage': {'Size': 512},
		 'SnapStart'                                                                                                                                                                              : {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName'                                                                                                                                                                                                                                                                 : 'AccountAssessmentStack-WebUIDeployerDeployWebUIC2B-ZL1H4n2W05xe',
		 'FunctionArn'                                                                                                                                                                                                                                                                  : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-WebUIDeployerDeployWebUIC2B-ZL1H4n2W05xe',
		 'Runtime'                                                                                                                                                                                                                                                                      : 'python3.9',
		 'Role'                                                                                                                                                                                                                                                                         : 'arn:aws:iam::111122223333:role/AccountAssessmentStack-WebUIDeployerDeployWebUISer-SXOS38SBZPWQ',
		 'Handler'                                                                                                                                                                                                                                                                      : 'deploy_webui/deploy_webui.lambda_handler',
		 'CodeSize'                                                                                                                                                                                                                                                                     : 17578832,
		 'Description'                                                                                                                                                                                                                                                                  : '',
		 'Timeout'                                                                                                                                                                                                                                                                      : 300,
		 'MemorySize'                                                                                                                                                                                                                                                                   : 128,
		 'LastModified'                                                                                                                                                                                                                                                                 : '2023-04-14T15:06:17.107+0000',
		 'CodeSha256'                                                                                                                                                                                                                                                                   : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=',
		 'Version'                                                                                                                                                                                                                                                                      : '$LATEST',
		 'Environment'                                                                                                                                                                                                                                                                  : {'Variables': {
			 'CONFIG'                 : '{"SrcBucket":"solutions-us-east-1","SrcPath":"account-assessment-for-aws-organizations/v1.0.3/webui/","WebUIBucket":"accountassessmentstack-s3bucket07682993-1qnr9dfvuvn8m","awsExports":{"API":{"endpoints":[{"name":"AccountAssessmentApi","endpoint":"https://5ugessads8.execute-api.us-east-1.amazonaws.com/prod"}]},"loggingLevel":"INFO","Auth":{"region":"us-east-1","userPoolId":"us-east-1_4y5EH6RX3","userPoolWebClientId":"10hrrgcdjum45c4jmre3kv7r7d","mandatorySignIn":true,"oauth":{"domain":"paulbaye-amzn.auth.us-east-1.amazoncognito.com","scope":["openid","profile","email","aws.cognito.signin.user.admin"],"redirectSignIn":"https://d12i33hlb8s7se.cloudfront.net/","redirectSignOut":"https://d12i33hlb8s7se.cloudfront.net/","responseType":"code","clientId":"10hrrgcdjum45c4jmre3kv7r7d"}}}}',
			 'POWERTOOLS_SERVICE_NAME': 'DeployWebUI', 'SEND_ANONYMOUS_DATA': 'Yes', 'STACK_ID': 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7', 'LOG_LEVEL': 'INFO', 'SOLUTION_VERSION': 'v1.0.3'}}, 'TracingConfig': {
			'Mode': 'Active'},
		 'RevisionId'                                                                                                                                                                                                                                                                   : 'b79766f8-4e8d-438c-a5b5-8d5e656a165e',
		 'PackageType'                                                                                                                                                                                                                                                                  : 'Zip',
		 'Architectures'                                                                                                                                                                                                                                                                : ['x86_64'],
		 'EphemeralStorage'                                                                                                                                                                                                                                                             : {'Size': 512},
		 'SnapStart'                                                                                                                                                                                                                                                                    : {
			 'ApplyOn'           : 'None',
			 'OptimizationStatus': 'Off'}},
		{'FunctionName': 'orgformation-EmptyS3BucketOnDeletionLambdaFunction-W98Id8S5pK33', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:orgformation-EmptyS3BucketOnDeletionLambdaFunction-W98Id8S5pK33', 'Runtime': 'python3.9',
		 'Role'        : 'arn:aws:iam::111122223333:role/orgformation-EmptyS3BucketOnDeletionLambdaExecutio-1SLZXRGG2YUT5', 'Handler': 'index.handler', 'CodeSize': 1412, 'Description': '', 'Timeout': 3, 'MemorySize': 128, 'LastModified': '2023-09-06T16:44:28.000+0000',
		 'CodeSha256'  : 'kK3SVtC1I7ezvKPsNwno7YY9AfCKV3kkA56RV8kD3DE=', 'Version': '$LATEST', 'TracingConfig': {'Mode': 'PassThrough'}, 'RevisionId': 'c5d3cf2d-8a26-41d0-a0e8-60a36bca1103', 'PackageType': 'Zip', 'Architectures': ['x86_64'], 'EphemeralStorage': {'Size': 512},
		 'SnapStart'   : {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName': 'AccountAssessmentStack-JobHistoryJobsHandler060579-EShvGJzftPCt',
		 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-JobHistoryJobsHandler060579-EShvGJzftPCt',
		 'Runtime': 'python3.9',
		 'Role': 'arn:aws:iam::111122223333:role/AccountAssessmentStack-JobHistoryJobsHandlerServic-HXRBGBPC98KW',
		 'Handler': 'assessment_runner/api_router.lambda_handler',
		 'CodeSize': 17578832, 'Description': '',
		 'Timeout': 60, 'MemorySize': 128,
		 'LastModified': '2023-04-14T15:01:53.918+0000',
		 'CodeSha256': 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=',
		 'Version': '$LATEST', 'Environment': {
			'Variables': {'POWERTOOLS_LOGGER_LOG_EVENT': 'True', 'POWERTOOLS_SERVICE_NAME': 'JobsApiHandler', 'SEND_ANONYMOUS_DATA': 'Yes', 'TABLE_TRUSTED_ACCESS': 'AccountAssessmentStack-TrustedAccessTable495B447A-GTR0RYDUJU5Q',
			              'TABLE_DELEGATED_ADMIN'      : 'AccountAssessmentStack-DelegatedAdminsTable29E80916-F34FK4FZGFP5', 'TIME_TO_LIVE_IN_DAYS': '90', 'STACK_ID': 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7',
			              'TABLE_JOBS'                 : 'AccountAssessmentStack-JobHistoryTableE4B293DD-1QRBBBDKUU8G9', 'SOLUTION_VERSION': 'v1.0.3', 'TABLE_RESOURCE_BASED_POLICY': 'AccountAssessmentStack-ResourceBasedPolicyTable7277C643-13R1K510AXFDB'}}, 'TracingConfig': {'Mode': 'Active'},
		 'RevisionId': '4ebd1e01-2898-4dab-8fb2-a42bad2bb1df',
		 'PackageType': 'Zip',
		 'Architectures': ['x86_64'],
		 'EphemeralStorage': {'Size': 512},
		 'SnapStart': {'ApplyOn'           : 'None',
		               'OptimizationStatus': 'Off'}},
		{'FunctionName': 'CreateidpProvider', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:CreateidpProvider', 'Runtime': 'python2.7', 'Role': 'arn:aws:iam::111122223333:role/service-role/CreateidpProvider-role-o7h6t6no', 'Handler': 'lambda_function.lambda_handler',
		 'CodeSize'    : 886,
		 'Description' : '', 'Timeout': 3, 'MemorySize': 128, 'LastModified': '2019-05-02T15:03:42.436+0000', 'CodeSha256': 'QvxbS4ZbI9bivuDn5kp7ARuHikbV5Xf3/SN3bKCcQdY=', 'Version': '$LATEST', 'TracingConfig': {'Mode': 'PassThrough'}, 'RevisionId': '42c3c4df-fe81-4dfd-9cd8-827a478407b7',
		 'PackageType' : 'Zip', 'Architectures': ['x86_64'], 'EphemeralStorage': {'Size': 512}, 'SnapStart': {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName'    : 'P9E-a8ba4fea-1856-49ca-8aa4-2b7e9b58d7a6', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:P9E-a8ba4fea-1856-49ca-8aa4-2b7e9b58d7a6', 'Runtime': 'python3.7',
		 'Role'            : 'arn:aws:iam::111122223333:role/aws-perspective-51771365777-LambdaEdgeFunctionRole-15OZK21LEUC5O', 'Handler': 'append_headers.handler', 'CodeSize': 1039, 'Description': 'Lambda@Edge for secure headers', 'Timeout': 5, 'MemorySize': 128,
		 'LastModified'    : '2020-09-22T15:54:23.904+0000', 'CodeSha256': 'tZMc1X5ewz2jkq2rML6VPQgb3x4T9wnYvnMacZHO65I=', 'Version': '$LATEST', 'TracingConfig': {'Mode': 'PassThrough'}, 'RevisionId': 'ffa243e9-dbe5-4424-970a-96ecfb5e4a3b', 'PackageType': 'Zip', 'Architectures': ['x86_64'],
		 'EphemeralStorage': {'Size': 512}, 'SnapStart': {'ApplyOn': 'None', 'OptimizationStatus': 'Off'}},
		{'FunctionName'                                                                                                                                                                                                                                  : 'AccountAssessmentStack-TrustedAccessRead96AB6071-NKktqhxZ7fTz',
		 'FunctionArn'                                                                                                                                                                                                                                   : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-TrustedAccessRead96AB6071-NKktqhxZ7fTz',
		 'Runtime'                                                                                                                                                                                                                                       : 'python3.9',
		 'Role'                                                                                                                                                                                                                                          : 'arn:aws:iam::111122223333:role/AccountAssessmentStack-TrustedAccessReadServiceRol-1RC8YXWIAP9YN',
		 'Handler'                                                                                                                                                                                                                                       : 'trusted_access_enabled_services/read_trusted_services.lambda_handler',
		 'CodeSize'                                                                                                                                                                                                                                      : 17578832, 'Description': '', 'Timeout': 60,
		 'MemorySize'                                                                                                                                                                                                                                    : 128,
		 'LastModified'                                                                                                                                                                                                                                  : '2023-04-14T15:01:53.616+0000',
		 'CodeSha256'                                                                                                                                                                                                                                    : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=',
		 'Version'                                                                                                                                                                                                                                       : '$LATEST', 'Environment': {
			'Variables': {'POWERTOOLS_SERVICE_NAME': 'ReadTrustedAccess', 'SEND_ANONYMOUS_DATA': 'Yes', 'STACK_ID': 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7',
			              'TABLE_JOBS'             : 'AccountAssessmentStack-JobHistoryTableE4B293DD-1QRBBBDKUU8G9', 'COMPONENT_TABLE': 'AccountAssessmentStack-TrustedAccessTable495B447A-GTR0RYDUJU5Q', 'SOLUTION_VERSION': 'v1.0.3'}}, 'TracingConfig': {'Mode': 'Active'},
		 'RevisionId'                                                                                                                                                                                                                                    : '41db914e-32ea-4b7c-8a05-a78def9856b1',
		 'PackageType'                                                                                                                                                                                                                                   : 'Zip', 'Architectures': ['x86_64'],
		 'EphemeralStorage'                                                                                                                                                                                                                              : {'Size': 512},
		 'SnapStart'                                                                                                                                                                                                                                     : {'ApplyOn'           : 'None',
		                                                                                                                                                                                                                                                    'OptimizationStatus': 'Off'}},
		{'FunctionName'                                                                                                                                                                                                                                    : 'AccountAssessmentStack-DelegatedAdminsRead591DCC7E-AyGSKEOHKNm2',
		 'FunctionArn'                                                                                                                                                                                                                                     : 'arn:aws:lambda:us-east-1:111122223333:function:AccountAssessmentStack-DelegatedAdminsRead591DCC7E-AyGSKEOHKNm2',
		 'Runtime'                                                                                                                                                                                                                                         : 'python3.9',
		 'Role'                                                                                                                                                                                                                                            : 'arn:aws:iam::111122223333:role/AccountAssessmentStack-DelegatedAdminsReadServiceR-NA50GOH53141',
		 'Handler'                                                                                                                                                                                                                                         : 'delegated_admins/read_delegated_admins.lambda_handler',
		 'CodeSize'                                                                                                                                                                                                                                        : 17578832, 'Description': '', 'Timeout': 60,
		 'MemorySize'                                                                                                                                                                                                                                      : 128,
		 'LastModified'                                                                                                                                                                                                                                    : '2023-04-14T15:01:54.770+0000',
		 'CodeSha256'                                                                                                                                                                                                                                      : 'W3RrpSLyvPWK2fMWGtTwyhNlX/MgiEmi4J4S56uv6qs=',
		 'Version'                                                                                                                                                                                                                                         : '$LATEST', 'Environment': {
			'Variables': {'POWERTOOLS_SERVICE_NAME': 'ReadDelegatedAdmin', 'SEND_ANONYMOUS_DATA': 'Yes', 'STACK_ID': 'arn:aws:cloudformation:us-east-1:111122223333:stack/AccountAssessmentStack/bc6befc0-dacb-11ed-921f-0a41af233cd7',
			              'TABLE_JOBS'             : 'AccountAssessmentStack-JobHistoryTableE4B293DD-1QRBBBDKUU8G9', 'COMPONENT_TABLE': 'AccountAssessmentStack-DelegatedAdminsTable29E80916-F34FK4FZGFP5', 'SOLUTION_VERSION': 'v1.0.3'}}, 'TracingConfig': {'Mode': 'Active'},
		 'RevisionId'                                                                                                                                                                                                                                      : '677f7ad5-f7d2-44d7-a3dd-c026e022b2fb',
		 'PackageType'                                                                                                                                                                                                                                     : 'Zip', 'Architectures': ['x86_64'],
		 'EphemeralStorage'                                                                                                                                                                                                                                : {'Size': 512},
		 'SnapStart'                                                                                                                                                                                                                                       : {'ApplyOn'           : 'None',
		                                                                                                                                                                                                                                                      'OptimizationStatus': 'Off'}}]
}
# Function response data from the Inventory_Scripts function, and not boto3.
t = [
	{'FunctionName': 'Create_CW_Metrics', 'FunctionArn': 'arn:aws:lambda:us-east-1:111111111111:function:Create_CW_Metrics', 'Role': 'Create_CW_MetricsRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '111111111111', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LandingZoneLocalSNSNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:111111111111:function:LandingZoneLocalSNSNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-10GM1SS21LPJ4', 'Runtime': 'python3.9',
	 'MgmtAccount' : '111122223333', 'AccountId': '111111111111', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-14R9E4I39TMGH', 'FunctionArn': 'arn:aws:lambda:us-east-1:111111111111:function:StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-14R9E4I39TMGH', 'Role': 'StackSet-AWS-Landing-Zone-Baseline-IamP-LambdaRole-1ROC6UIWPU7BM',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '111111111111', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'CloudFormationApply', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:CloudFormationApply', 'Role': 'service-role/myLambdaRunCode_Role', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'Create_CW_Metrics', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:Create_CW_Metrics', 'Role': 'Create_CW_MetricsRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName'   : 'LandingZone', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:LandingZone', 'Role': 'LandingZoneLambdaRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***',
	 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'LandingZoneAddonPublisher', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:LandingZoneAddonPublisher', 'Role': 'LZ-Initiation-PublisherLambdaRole-1U2ELSGH61W55', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '111122223333',
	 'Region'      : 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'LandingZoneDeploymentLambda', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:LandingZoneDeploymentLambda', 'Role': 'LandingZoneDeploymentLambdaRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'LandingZoneHandshakeSMLambda', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:LandingZoneHandshakeSMLambda', 'Role': 'LandingZoneHandshakeSMLambdaRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'LandingZoneLocalSNSNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:LandingZoneLocalSNSNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-1J4CB75JBXNYO', 'Runtime': 'python3.9',
	 'MgmtAccount' : '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'LandingZoneStateMachineLambda', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:LandingZoneStateMachineLambda', 'Role': 'StateMachineLambdaRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'LandingZoneStateMachineTriggerLambda', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:LandingZoneStateMachineTriggerLambda', 'Role': 'StateMachineTriggerLambdaRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '111122223333',
	 'Region'      : 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'SC-111122223333-pp-n6374w-LandingZoneAddOnDeployme-3vcpGQMxeWXT', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:SC-111122223333-pp-n6374w-LandingZoneAddOnDeployme-3vcpGQMxeWXT', 'Role': 'LandingZoneDeploymentLambdaRole', 'Runtime': 'python3.9',
	 'MgmtAccount' : '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-UF2T2MKY3NJF', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-UF2T2MKY3NJF', 'Role': 'StackSet-AWS-Landing-Zone-Baseline-IamP-LambdaRole-RVDISB3T58RV',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'org-dep-checker-OrgDependencyCheckerFunction-LOoXu13rmtpr', 'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:org-dep-checker-OrgDependencyCheckerFunction-LOoXu13rmtpr', 'Role': 'org-dep-checker-OrgDependencyCheckerFunctionRole-Q70Z1POVGX9S',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '111122223333', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***', 'SessionToken': None},
	{'FunctionName': 'Create_CW_Metrics', 'FunctionArn': 'arn:aws:lambda:us-east-1:292902349725:function:Create_CW_Metrics', 'Role': 'Create_CW_MetricsRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '292902349725', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LandingZoneLocalSNSNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:292902349725:function:LandingZoneLocalSNSNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-1B95P1B7Y1U3H', 'Runtime': 'python3.9',
	 'MgmtAccount' : '111122223333', 'AccountId': '292902349725', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-E3EYVN9PTV7I', 'FunctionArn': 'arn:aws:lambda:us-east-1:292902349725:function:StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-E3EYVN9PTV7I', 'Role': 'StackSet-AWS-Landing-Zone-Baseline-IamP-LambdaRole-4TLTYE61OQRU',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '292902349725', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'Create_CW_Metrics', 'FunctionArn': 'arn:aws:lambda:us-east-1:222222222222:function:Create_CW_Metrics', 'Role': 'Create_CW_MetricsRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '222222222222', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LandingZoneLocalSNSNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:222222222222:function:LandingZoneLocalSNSNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-ZB120L4B39DW', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333',
	 'AccountId'   : '222222222222', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-6KP78QBS1J5L', 'FunctionArn': 'arn:aws:lambda:us-east-1:222222222222:function:StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-6KP78QBS1J5L', 'Role': 'StackSet-AWS-Landing-Zone-Baseline-IamP-LambdaRole-YKAMOJLAYNZV',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '222222222222', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'Create_CW_Metrics', 'FunctionArn': 'arn:aws:lambda:us-east-1:333333333333:function:Create_CW_Metrics', 'Role': 'Create_CW_MetricsRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '333333333333', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LandingZoneLocalSNSNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:333333333333:function:LandingZoneLocalSNSNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-1CI5HVHBI7WKR', 'Runtime': 'python3.9',
	 'MgmtAccount' : '111122223333', 'AccountId': '333333333333', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-166N622Y1F1D8', 'FunctionArn': 'arn:aws:lambda:us-east-1:333333333333:function:StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-166N622Y1F1D8', 'Role': 'StackSet-AWS-Landing-Zone-Baseline-IamP-LambdaRole-14NLLL8TQ2AIO',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '333333333333', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'Create_CW_Metrics', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:Create_CW_Metrics', 'Role': 'Create_CW_MetricsRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '444444444444', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'GetStartedLambdaProxyIntegration', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:GetStartedLambdaProxyIntegration', 'Role': 'service-role/GetStartedLambdaBasicExecutionRole', 'Runtime': 'nodejs10.x', 'MgmtAccount': '111122223333', 'AccountId': '444444444444',
	 'Region'      : 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'InvokeCloudFormation', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:InvokeCloudFormation', 'Role': 'service-role/InvokeCloudFormation-role-03z41yeg', 'Runtime': 'nodejs10.x', 'MgmtAccount': '111122223333', 'AccountId': '444444444444', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LambdaAuthorizerExample', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:LambdaAuthorizerExample', 'Role': 'service-role/LambdaAuthorizerExample-role-03sn3n1k', 'Runtime': 'python2.7', 'MgmtAccount': '111122223333', 'AccountId': '444444444444',
	 'Region'      : 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LambdaAuthorizerRequestTypeCustom', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:LambdaAuthorizerRequestTypeCustom', 'Role': 'service-role/LambdaAuthorizerRequestTypeCustom-role-iiyuxrue', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333',
	 'AccountId'   : '444444444444', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LandingZoneLocalSNSNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:LandingZoneLocalSNSNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-1WSZCDKENGDSH', 'Runtime': 'python3.9',
	 'MgmtAccount' : '111122223333', 'AccountId': '444444444444', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'SagemakerInvokerBlazingText', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:SagemakerInvokerBlazingText', 'Role': 'service-role/SagemakerInvokerBlazingText-role-kkbzh050', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '444444444444',
	 'Region'      : 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-A3VSMQU7FRMR', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-A3VSMQU7FRMR', 'Role': 'StackSet-AWS-Landing-Zone-Baseline-IamP-LambdaRole-16O26U382TMXG',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '444444444444', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'Telemetry_LogCleaup', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:Telemetry_LogCleaup', 'Role': 'service-role/Telemetry_LogCleaup-role-aomd82zq', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '444444444444', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'dotnetcorelambda', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:dotnetcorelambda', 'Role': 'service-role/dotnetcorelambda-role-qk445824', 'Runtime': 'dotnetcore2.1', 'MgmtAccount': '111122223333', 'AccountId': '444444444444', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'hellonodejs', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:hellonodejs', 'Role': 'service-role/hellonodejs-role-2nvxxxy7', 'Runtime': 'nodejs8.10', 'MgmtAccount': '111122223333', 'AccountId': '444444444444', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'secretrotationfunction', 'FunctionArn': 'arn:aws:lambda:us-east-1:444444444444:function:secretrotationfunction', 'Role': 'service-role/secretrotationfunction-role-4v03rkfq', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '444444444444',
	 'Region'      : 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'Create_CW_Metrics', 'FunctionArn': 'arn:aws:lambda:us-east-1:555555555555:function:Create_CW_Metrics', 'Role': 'Create_CW_MetricsRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '555555555555', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LandingZoneLocalSNSNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:555555555555:function:LandingZoneLocalSNSNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-WCIU8QEBAZGA', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333',
	 'AccountId'   : '555555555555', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-NC3Z57YQ4VF3', 'FunctionArn': 'arn:aws:lambda:us-east-1:555555555555:function:StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-NC3Z57YQ4VF3', 'Role': 'StackSet-AWS-Landing-Zone-Baseline-IamP-LambdaRole-1U8PG0E7R57HS',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '555555555555', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'Create_CW_Metrics', 'FunctionArn': 'arn:aws:lambda:us-east-1:666666666666:function:Create_CW_Metrics', 'Role': 'Create_CW_MetricsRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '666666666666', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LandingZoneLocalSNSNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:666666666666:function:LandingZoneLocalSNSNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-E599EO74LGXA', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333',
	 'AccountId'   : '666666666666', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-HRX910NRFLLR', 'FunctionArn': 'arn:aws:lambda:us-east-1:666666666666:function:StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-HRX910NRFLLR', 'Role': 'StackSet-AWS-Landing-Zone-Baseline-IamP-LambdaRole-JSXKBH9MQ0CV',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '666666666666', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'Create_CW_Metrics', 'FunctionArn': 'arn:aws:lambda:us-east-1:777777777777:function:Create_CW_Metrics', 'Role': 'Create_CW_MetricsRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '777777777777', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LandingZoneLocalSNSNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:777777777777:function:LandingZoneLocalSNSNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-1UVK1I2XFTK92', 'Runtime': 'python3.9',
	 'MgmtAccount' : '111122223333', 'AccountId': '777777777777', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-9SUEVBGP134A', 'FunctionArn': 'arn:aws:lambda:us-east-1:777777777777:function:StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-9SUEVBGP134A', 'Role': 'StackSet-AWS-Landing-Zone-Baseline-IamP-LambdaRole-1SVZOOUOCKDFR',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '777777777777', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'Create_CW_Metrics', 'FunctionArn': 'arn:aws:lambda:us-east-1:888888888888:function:Create_CW_Metrics', 'Role': 'Create_CW_MetricsRole', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '888888888888', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LandingZoneGuardDutyNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:888888888888:function:LandingZoneGuardDutyNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-1LL63QEBS7M0O', 'Runtime': 'python3.9',
	 'MgmtAccount' : '111122223333', 'AccountId': '888888888888', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'LandingZoneLocalSNSNotificationForwarder', 'FunctionArn': 'arn:aws:lambda:us-east-1:888888888888:function:LandingZoneLocalSNSNotificationForwarder', 'Role': 'StackSet-AWS-Landing-Zone-ForwardSnsNotificationLa-7STAM9IH9WC1', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333',
	 'AccountId'   : '888888888888', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-8PPP3LFKM4C4', 'FunctionArn': 'arn:aws:lambda:us-east-1:888888888888:function:StackSet-AWS-Landing-Zone-IamPasswordPolicyCustomR-8PPP3LFKM4C4', 'Role': 'StackSet-AWS-Landing-Zone-Baseline-IamP-LambdaRole-RG7FX3KV68EL',
	 'Runtime'     : 'python3.8', 'MgmtAccount': '111122223333', 'AccountId': '888888888888', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'CheckPipelineStatus', 'FunctionArn': 'arn:aws:lambda:us-east-1:999999999999:function:CheckPipelineStatus', 'Role': 'adf-lambda-role', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '999999999999', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'PipelinesCreateInitialCommitFunction', 'FunctionArn': 'arn:aws:lambda:us-east-1:999999999999:function:PipelinesCreateInitialCommitFunction', 'Role': 'adf-global-base-deploymen-InitialCommitHandlerRole-21R8IK57XL0X', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333',
	 'AccountId'   : '999999999999', 'Region': 'us-east-1', 'AccessKeyId': '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'SendSlackNotification', 'FunctionArn': 'arn:aws:lambda:us-east-1:999999999999:function:SendSlackNotification', 'Role': 'adf-lambda-role', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '999999999999', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'},
	{'FunctionName': 'UpdateCrossAccountIAM', 'FunctionArn': 'arn:aws:lambda:us-east-1:999999999999:function:UpdateCrossAccountIAM', 'Role': 'adf-lambda-role', 'Runtime': 'python3.9', 'MgmtAccount': '111122223333', 'AccountId': '999999999999', 'Region': 'us-east-1',
	 'AccessKeyId' : '***AccessKeyIdHere***', 'SecretAccessKey': '***SecretAccessKeyHere***',
	 'SessionToken': '***SessionTokenHere***'}]



# Generate a test function to test out the "all_my_functions" function that I've imported



@pytest.mark.parametrize(
	"parameters,test_value",
	[
		(function_parameters1, function_response_data),
		# (RootOnlyParams, ),
		# str(1993),
		# json.dumps({"SecretString": "my-secret"}),
		# json.dumps([2, 3, 5, 7, 11, 13, 17, 19]),
		# KeyError("How dare you touch my secret!"),
		# ValueError("Oh my goodness you even have the guts to repeat it!!!"),
	],
)
def test_all_my_functions(parameters, test_value, mocker):
	"""
	Description:
	@param parameters: the expected parameters into the function
	@param test_value: the expected response from the call being mocked
	@param mocker: the mock object
	@return:
	"""
	CredentialList = parameters['CredentialList']
	main_op = 'check_for_functions'
	pFragments = parameters['pFragments']
	verbose = parameters['pverbose']
	_amend_make_api_call(main_op, test_value, mocker)

	if isinstance(test_value, Exception):
		print("Expected Error...")
		with pytest.raises(type(test_value)) as error:
			all_my_functions(CredentialList, pFragments, verbose)
		result = error
	else:
		result = all_my_functions(CredentialList, pFragments, verbose)

	print("Result:", result)
	print()
