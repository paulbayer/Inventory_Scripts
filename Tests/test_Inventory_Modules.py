from botocore import client
from boto3 import client as b3_client
import pytest
from unittest.mock import patch
from datetime import datetime
from dateutil.tz import tzutc, tzlocal
from Inventory_Modules import get_all_credentials, get_credentials_for_accounts_in_org

# This requires a default method of authentication be already setup
# aws_acct = aws_acct_access()
#### Create data ####
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
	'pverbose'     : 20}

get_caller_identity_response_data = {'UserId': 'AIDAEXAMPLEVUHYO6', 'Account': '111122223333', 'Arn': 'arn:aws:iam::111122223333:user/Paul'}

# Below is 10 Credentials
list_account_response_data = {'Accounts' : [
	{'Id'             : '111122223333', 'Arn': 'arn:aws:organizations::111122223333:account/o-00orgid00/111122223333', 'Email': 'paulbaye+LZRoot@amazon.com', 'Name': 'LZRoot2', 'Status': 'ACTIVE', 'JoinedMethod': 'INVITED',
	 'JoinedTimestamp': datetime(2018, 7, 19, 23, 32, 57, 676000, tzinfo=tzlocal())},
	{'Id'             : '666666666666', 'Arn': 'arn:aws:organizations::111122223333:account/o-00orgid00/666666666666', 'Email': 'paulbaye+LZ_SS@amazon.com', 'Name': 'shared-services', 'Status': 'ACTIVE', 'JoinedMethod': 'CREATED',
	 'JoinedTimestamp': datetime(2018, 10, 30, 17, 23, 31, 965000, tzinfo=tzlocal())},
	{'Id'             : '444444444444', 'Arn': 'arn:aws:organizations::111122223333:account/o-00orgid00/444444444444', 'Email': 'paulbaye+LZ_Demo3@amazon.com', 'Name': 'Test-Demo3', 'Status': 'ACTIVE', 'JoinedMethod': 'INVITED',
	 'JoinedTimestamp': datetime(2020, 9, 8, 18, 32, 1, 416000, tzinfo=tzlocal())},
	{'Id'             : '555555555555', 'Arn': 'arn:aws:organizations::111122223333:account/o-00orgid00/555555555555', 'Email': 'paulbaye+LZ_Sec@amazon.com', 'Name': 'security', 'Status': 'ACTIVE', 'JoinedMethod': 'CREATED',
	 'JoinedTimestamp': datetime(2018, 10, 30, 17, 12, 14, 78000, tzinfo=tzlocal())},
	{'Id'             : '888888888888', 'Arn': 'arn:aws:organizations::111122223333:account/o-00orgid00/888888888888', 'Email': 'paulbaye+LZ4-Log@amazon.com', 'Name': 'logging', 'Status': 'ACTIVE', 'JoinedMethod': 'INVITED',
	 'JoinedTimestamp': datetime(2021, 2, 17, 15, 10, 24, 597000, tzinfo=tzlocal())},
	{'Id'             : '222222222222', 'Arn': 'arn:aws:organizations::111122223333:account/o-00orgid00/222222222222', 'Email': 'paulbaye+LZ4-SS@amazon.com', 'Name': 'shared-services', 'Status': 'ACTIVE', 'JoinedMethod': 'INVITED',
	 'JoinedTimestamp': datetime(2021, 2, 17, 15, 10, 46, 390000, tzinfo=tzlocal())},
	{'Id'             : '111111111111', 'Arn': 'arn:aws:organizations::111122223333:account/o-00orgid00/111111111111', 'Email': 'paulbaye+Demo1@amazon.com', 'Name': 'Demo-Acct-1', 'Status': 'ACTIVE', 'JoinedMethod': 'CREATED',
	 'JoinedTimestamp': datetime(2018, 12, 4, 0, 37, 35, 851000, tzinfo=tzlocal())},
	{'Id'             : '999999999999', 'Arn': 'arn:aws:organizations::111122223333:account/o-00orgid00/999999999999', 'Email': 'paulbaye+LZ_Demo23@amazon.com', 'Name': 'Test-Demo23', 'Status': 'ACTIVE', 'JoinedMethod': 'CREATED',
	 'JoinedTimestamp': datetime(2020, 7, 23, 18, 16, 52, 900000, tzinfo=tzlocal())},
	{'Id'             : '777777777777', 'Arn': 'arn:aws:organizations::111122223333:account/o-00orgid00/777777777777', 'Email': 'paulbaye+LZ_Log@amazon.com', 'Name': 'logging', 'Status': 'ACTIVE', 'JoinedMethod': 'CREATED',
	 'JoinedTimestamp': datetime(2018, 10, 30, 17, 17, 51, 248000, tzinfo=tzlocal())},
	{'Id'             : '333333333333', 'Arn': 'arn:aws:organizations::111122223333:account/o-00orgid00/333333333333', 'Email': 'paulbaye+LZ2SS@amazon.com', 'Name': 'shared-services', 'Status': 'ACTIVE', 'JoinedMethod': 'CREATED',
	 'JoinedTimestamp': datetime(2018, 10, 26, 23, 27, 11, 350000, tzinfo=tzlocal())}]}
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

def _amend_make_api_call(test_key, test_value, mocker):
	orig = client.BaseClient._make_api_call

	def amend_make_api_call(self, operation_name, kwargs):
		# Intercept boto3 operations for <secretsmanager.get_secret_value>. Optionally, you can also
		# check on the argument <SecretId> and control how you want the response would be. This is
		# a very flexible solution as you have full control over the whole process of fetching a
		# secret.
		if operation_name == 'ListAccounts':
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

# @patch('b3_client("organizations").get_caller_identity()', return_value=get_caller_identity_response_data)
@pytest.mark.parametrize(
	"parameters, account_listing, credentials",
	[
		(parameters1, list_account_response_data, CredentialResponseData),
		# (RootOnlyParams, list_accounts_test_data1),
		# str(1993),
		# json.dumps({"SecretString": "my-secret"}),
		# json.dumps([2, 3, 5, 7, 11, 13, 17, 19]),
		# KeyError("How dare you touch my secret!"),
		# ValueError("Oh my goodness you even have the guts to repeat it!!!"),
	],
)
def test_get_all_credentials(parameters, account_listing, credentials, mocker):
	"""
	Description: This function will test that the "get_credentials" call works properly. This should probably be commonized, but I'm still learning...
	@param parameters: The parameters that would normally be passed to this function to test
	@param account_listing: The parameters that this function should be given as part of the mock
	@param mocker: The object that holds the mock call being made
	@return: Returns a list object containing Credentials for every account and region passed in
	Calls made:
		OperationName: DescribeRegions (It does this to validate the region passed in)
		OperationName: GetCallerIdentity (This is where it determines the [real] account number of the profile it was given)
		OperationName: DescribeOrganization (This is where it figures out that this profile is a Root account, and therefore has children)
		OperationName: ListAccounts (Since this account has children, it does a ListAccounts and finds those children)
		OperationName: AssumeRole (as many times as there are Child Accounts * regions)

	"""
	pProfiles = parameters['pProfiles']
	pRegionList = parameters['pRegionList']
	pSkipProfiles = parameters['pSkipProfiles']
	pSkipAccounts = parameters['pSkipAccounts']
	pAccountList = parameters['pAccountList']
	pTiming = parameters['pTiming']
	pRootOnly = parameters['pRootOnly']
	pRoleList = parameters['pRoleList']
	main_op = 'check_for_credentials'
	_amend_make_api_call(main_op, account_listing, mocker)
	# _amend_make_api_call(main_op, credentials, mocker)

	if isinstance(account_listing, Exception):
		print("Expected Error...")
		with pytest.raises(type(account_listing)) as error:
			get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccountList, pRegionList, pRoleList)
		result = error
	else:
		result = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccountList, pRegionList, pRoleList)

	print("Result:", result)
	print()

#
# class TestGetRegions(TestCase):
#
# 	def test_get_regions3(self):
# 		regions = get_regions3(aws_acct, 'us-east-1')
# 		self.assertIn('us-east-1', regions)
# 		self.assertNotIn('us', regions)
# 		# self.fail()
#
#
# def test_list_objects():
#
# 	s3 = aws_acct.session.create_client('s3')
#
# 	response = {
# 	    "Owner": {
# 	        "ID": "foo",
# 	        "DisplayName": "bar"
# 	    },
# 	    "Buckets": [{
# 	        "CreationDate": datetime.datetime(2016, 1, 20, 22, 9),
# 	        "Name": "baz"
# 	    }]
# 	}
#
#
# 	with Stubber(s3) as stubber:
# 		stubber.add_response('list_buckets', response, {})
# 		service_response = s3.list_buckets()
#
# 	assert service_response == response
#
# def test_get_regions3(faws_acct, fregion_list=None):
# def test_get_ec2_regions(fprofile=None, fregion_list=None):
# def test_get_ec2_regions3(faws_acct, fkey=None):
# def test_get_service_regions(service, fkey=None, fprofile=None, ocredentials=None, faws_acct=None):
# def test_validate_region3(faws_acct, fRegion=None):
# def test_get_profiles(fSkipProfiles=None, fprofiles=None):
# def test_find_in(list_to_search, list_to_find=None):
# def test_find_bucket_location(fProfile, fBucketname):
# def test_find_acct_email(fOrgRootProfile, fAccountId):
# def test_find_account_number(fProfile=None):
# def test_find_calling_identity(fProfile):
# def test_RemoveCoreAccounts(MainList, AccountsToRemove=None):
# def test_make_creds(faws_acct):
# def test_get_child_access(fRootProfile, fChildAccount, fRegion='us-east-1', fRoleList=None):
# def test_get_child_access3(faws_acct, fChildAccount, fRegion='us-east-1', fRoleList=None):
# def test_enable_drift_on_stacks2(ocredentials, fRegion, fStackName):
# def test_enable_drift_on_stack_set(ocredentials, fRegion, fStackSetName):
# def test_find_sns_topics2(ocredentials, fRegion, fTopicFrag=None):
# def test_find_role_names2(ocredentials, fRegion, fRoleNameFrag=None):
# def test_find_cw_log_group_names2(ocredentials, fRegion, fCWLogGroupFrag=None):
# def test_find_org_services2(ocredentials, serviceNameList=None):
# def test_disable_org_service2(ocredentials, serviceName=None):
# def test_find_account_vpcs2(ocredentials, defaultOnly=False):
# def test_find_account_vpcs3(faws_acct, fRegion, defaultOnly=False):
# def test_find_config_recorders2(ocredentials, fRegion):
# def test_del_config_recorder2(ocredentials, fRegion, fConfig_recorder_name):
# def test_find_delivery_channels2(ocredentials, fRegion):
# def test_del_delivery_channel2(ocredentials, fRegion, fDelivery_channel_name):
# def test_del_config_recorder_or_delivery_channel2(deletion_item):
# def test_find_cloudtrails2(ocredentials, fRegion, fCloudTrailnames=None):
# def test_del_cloudtrails2(ocredentials, fRegion, fCloudTrail):
# def test_find_gd_invites2(ocredentials, fRegion):
# def test_delete_gd_invites2(ocredentials, fRegion, fAccountId):
# def test_find_account_instances2(ocredentials, fRegion='us-east-1'):
# def test_find_cw_groups_retention2(ocredentials, fRegion='us-east-1'):
# def test_find_account_rds_instances2(ocredentials, fRegion='us-east-1'):
# def test_find_account_cloudtrail2(ocredentials, fRegion='us-east-1'):
# def test_find_account_subnets2(ocredentials, fRegion='us-east-1', fipaddresses=None):
# def test_find_account_enis2(ocredentials, fRegion=None, fipaddresses=None):
# def test_find_account_volumes2(ocredentials):
# def test_find_account_policies2(ocredentials, fRegion='us-east-1', fFragments=None, fExact=False):
# def test_find_account_policies3(faws_acct, fRegion='us-east-1', fFragments=None):
# def test_find_policy_action(ocredentials, fpolicy, f_action):
# def test_find_users2(ocredentials):
# def test_find_profile_vpcs(fProfile, fRegion, fDefaultOnly):
# def test_find_profile_functions(fProfile, fRegion):
# def test_find_lambda_functions2(ocredentials, fRegion='us-east-1', fSearchStrings=None):
# def test_find_lambda_functions3(faws_acct, fRegion='us-east-1', fSearchStrings=None):
# def test_get_lambda_code_url(fprofile, fregion, fFunctionName):
# def test_find_directories2(ocredentials, fRegion='us-east-1', fSearchStrings=None):
# def test_find_directories3(faws_acct, fRegion='us-east-1', fSearchStrings=None):
# def test_find_private_hosted_zones(fProfile, fRegion):
# def test_find_private_hosted_zones2(ocredentials, fRegion=None):
# def test_find_private_hosted_zones3(faws_acct, fRegion=None):
# def test_find_load_balancers(fProfile, fRegion, fStackFragment='all', fStatus='all'):
# def test_find_load_balancers3(faws_acct, fRegion='us-east-1', fStackFragments=None, fStatus='all'):
# def test_find_stacks(fProfile, fRegion, fStackFragment="all", fStatus="active"):
# def test_find_stacks2(ocredentials, fRegion, fStackFragment=None, fStatus=None):
# def test_find_stacks3(faws_acct, fRegion, fStackFragment="all", fStatus="active"):
# def test_delete_stack(fprofile, fRegion, fStackName, **kwargs):
# def test_delete_stack2(ocredentials, fRegion, fStackName, **kwargs):
# def test_find_stacks_in_acct3(faws_acct, fRegion, fStackFragment="all", fStatus="active"):
# def test_find_saml_components_in_acct2(ocredentials, fRegion):
# def test_find_stacksets2(ocredentials, fRegion='us-east-1', fStackFragment=None, fStatus=None):
# def test_find_stacksets3(faws_acct, fRegion=None, fStackFragment=None, fExact=False):
# def test_delete_stackset(fProfile, fRegion, fStackSetName):
# def test_delete_stackset3(faws_acct, fRegion, fStackSetName):
# def test_find_stack_instances(fProfile, fRegion, fStackSetName, fStatus='CURRENT'):
# def test_find_stack_instances2(ocredentials, fRegion, fStackSetName, fStatus='CURRENT'):
# def test_find_stack_instances3(faws_acct, fRegion, fStackSetName, fStatus='CURRENT'):
# def test_check_stack_set_status3(faws_acct, fStack_set_name, fOperationId=None):
# def test_find_if_stack_set_exists3(faws_acct, fStack_set_name):
# def test_find_sc_products(fProfile, fRegion, fStatus="ERROR", flimit=100):
# def test_find_sc_products3(faws_acct, fStatus="ERROR", flimit=100, fproductId=None):
# def test_find_ssm_parameters(fProfile, fRegion):
# def test_find_ssm_parameters2(ocredentials):
# def test_find_ssm_parameters3(faws_acct, fregion=None):
# def test_display_results(results_list, fdisplay_dict, defaultAction=None, file_to_save=None):
# def test_get_all_credentials(fProfiles=None, fTiming=False, fSkipProfiles=None, fSkipAccounts=None, fRootOnly=False, fAccounts=None, fRegionList=None, RoleList=None):
# def test_get_credentials_for_accounts_in_org(faws_acct, fSkipAccounts=None, fRootOnly=False, accountlist=None, fprofile="default", fregions=None, fRoleNames=None, fTiming=False):
# def test_get_org_accounts_from_profiles(fProfileList, progress_bar=False):

print()