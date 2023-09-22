from botocore import client
import pytest

from common_test_data import ListAccountsResponseData, parameters1, function_parameters1, function_response_data, GetCallerIdentity, DescribeRegionsResponseData, DescribeOrganizationsResponseData
from all_my_functions import all_my_functions, fix_my_functions
from Inventory_Modules import get_all_credentials


def _amend_make_api_call(test_key, test_value, test_dict, mocker):
	orig = client.BaseClient._make_api_call

	def amend_make_api_call(self, operation_name, kwargs):
		# Intercept boto3 operations for <secretsmanager.get_secret_value>. Optionally, you can also
		# check on the argument <SecretId> and control how you want the response would be. This is
		# a very flexible solution as you have full control over the whole process of fetching a
		# secret.
		for op_name in test_dict:
			if operation_name == op_name['operation_name']:
				if isinstance(test_value, Exception):
					raise test_value
				# Implied break and exit of the function here...
				print(f"Operation Name mocked: {operation_name}\n"
				      f"Key Name: {test_key}\n"
				      f"kwargs: {kwargs}\n"
				      f"mocked return_response: {op_name['test_result']}")
				return op_name['test_result']
			# elif operation_name == 'ListAccounts':
			# 	if isinstance(test_value, Exception):
			# 		raise test_value
			# 	# Implied break and exit of the function here...
			# 	print(f"Operation Name mocked: {operation_name}\n"
			# 	      f"Key Name: {test_key}\n"
			# 	      f"kwargs: {kwargs}\n"
			# 	      f"mocked return_response: {test_value}")
			# 	return test_value
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


"""
Pass in the parameters as dictionary with operation names and what test results I should get back
"""
xxx = 'PassThrough'
get_all_credentials_test_result_dict = [
	{'operation_name': 'GetCallerIdentity',
	 'test_result'   : GetCallerIdentity},
	{'operation_name': 'DescribeOrganization',
	 'test_result'   : DescribeOrganizationsResponseData},
	# {'operation_name': 'AssumeRole',
	#  'test_result'   : xxx},
	{'operation_name': 'ListAccounts',
	 'test_result'   : ListAccountsResponseData},
	{'operation_name': 'DescribeRegions',
	 'test_result'   : DescribeRegionsResponseData}
]
get_all_my_functions_test_result_dict = [
	{'operation_name': 'ListFunctions',
	 'test_result'   : function_response_data}, ]


@pytest.mark.parametrize(
	"parameters,test_value",
	[
		(parameters1, ListAccountsResponseData),
		# (RootOnlyParams, list_accounts_test_data1),
		# str(1993),
		# json.dumps({"SecretString": "my-secret"}),
		# json.dumps([2, 3, 5, 7, 11, 13, 17, 19]),
		# KeyError("How dare you touch my secret!"),
		# ValueError("Oh my goodness you even have the guts to repeat it!!!"),
	],
)
def test_get_all_credentials(parameters, test_value, mocker):
	pProfiles = parameters['pProfiles']
	pRegionList = parameters['pRegionList']
	pSkipProfiles = parameters['pSkipProfiles']
	pSkipAccounts = parameters['pSkipAccounts']
	pAccountList = parameters['pAccountList']
	pTiming = parameters['pTiming']
	pRootOnly = parameters['pRootOnly']
	pRoleList = parameters['pRoleList']
	main_op = "Get Credentials"
	_amend_make_api_call(main_op, test_value, get_all_credentials_test_result_dict, mocker)

	if isinstance(test_value, Exception):
		print("Expected Error...")
		with pytest.raises(type(test_value)) as error:
			get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccountList, pRegionList, pRoleList)
		result = error
	else:
		result = get_all_credentials(pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccountList, pRegionList, pRoleList)


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
	_amend_make_api_call(main_op, test_value, get_all_my_functions_test_result_dict, mocker)

	if isinstance(test_value, Exception):
		print("Expected Error...")
		with pytest.raises(type(test_value)) as error:
			all_my_functions(CredentialList, pFragments, verbose)
		result = error
	else:
		result = all_my_functions(CredentialList, pFragments, verbose)

	print("Result:", result)
	print()
