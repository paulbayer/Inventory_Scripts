from botocore import client
from botocore import session
import pytest

ERASE_LINE = '\x1b[2K'


def _amend_create_boto3_session(test_data, mocker):
	orig = session.Session.create_client

	def amend_create_client(
			self,
			service_name,
			region_name=None,
			api_version=None,
			use_ssl=True,
			verify=None,
			endpoint_url=None,
			aws_access_key_id=None,
			aws_secret_access_key=None,
			aws_session_token=None,
			config=None,
	):
		# Intercept boto3 Session, in hopes of sending back a client that includes the Account Number
		# if aws_access_key_id == '*****AccessKeyHere*****':
		print(test_data['FunctionName'])
		if aws_access_key_id == 'MeantToFail':
			print(f"Failed Access Key: {aws_access_key_id}")
			return()
		else:
			print(f"Not Failed Access Key: {aws_access_key_id}")
			return_response = orig(self,
			                       service_name,
			                       region_name,
			                       api_version,
			                       use_ssl,
			                       verify,
			                       endpoint_url,
			                       aws_access_key_id,
			                       aws_secret_access_key,
			                       aws_session_token,
			                       config)
			return (return_response)

	mocker.patch('botocore.session.Session.create_client', new=amend_create_client)
	print()


def _amend_make_api_call_orig(test_key, test_value, mocker):
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

		return_response = orig(self, operation_name, kwargs)
		print(f"Operation Name passed through: {operation_name}\n"
		      f"Key name: {test_key}\n"
		      f"kwargs: {kwargs}\n"
		      f"Actual return response: {return_response}")
		return return_response

	mocker.patch('botocore.client.BaseClient._make_api_call', new=amend_make_api_call)


def _amend_make_api_call(meta_key_dict, test_dict, mocker):
	orig = client.BaseClient._make_api_call

	def amend_make_api_call(self, operation_name, kwargs):
		# Intercept boto3 operations for <secretsmanager.get_secret_value>. Optionally, you can also
		# check on the argument <SecretId> and control how you want the response would be. This is
		# a very flexible solution as you have full control over the whole process of fetching a
		# secret.
		for op_name in test_dict:
			test_value = op_name['test_result']
			region = self.meta.region_name
			if operation_name == op_name['operation_name']:
				if isinstance(test_value, Exception):
					# Implied break and exit of the function here...
					raise test_value
				print(f"Operation Name mocked: {operation_name}\n"
				      f"Function Name: {meta_key_dict['FunctionName']}\n"
				      f"kwargs: {kwargs}\n"
				      f"mocked return_response: {op_name['test_result']}")
				return op_name['test_result']
		try:
			print(f"Trying: Operation Name passed through: {operation_name}\n"
			      f"Key Name: {meta_key_dict['FunctionName']}\n"
			      f"kwargs: {kwargs}\n")
			return_response = orig(self, operation_name, kwargs)
			print(f"Actual return_response: {return_response}")
		except Exception as my_Error:
			raise ConnectionError("Operation Failed")
		return return_response

	mocker.patch('botocore.client.BaseClient._make_api_call', new=amend_make_api_call)


def _amend_make_api_call_specific(meta_key_dict, test_dict, mocker):
	orig = client.BaseClient._make_api_call

	def amend_make_api_call(self, operation_name, kwargs):
		# Intercept boto3 operations for <secretsmanager.get_secret_value>. Optionally, you can also
		# check on the argument <SecretId> and control how you want the response would be. This is
		# a very flexible solution as you have full control over the whole process of fetching a
		# secret.
		# This goes through the operations in the dictionary and checks for each operation, whether it matches the operation we're patching right now.
		for op_name in test_dict:
			if operation_name == op_name['operation_name']:
				# We are able to capture the region from the API call, and use that to differentiate data to return
				region = self.meta.region_name
				# For the various sets of return data that we have...
				test_value = None
				for set_of_result_data in op_name['test_result']:
					# Check to see which set of return data matches the region we're calling for now...
					if set_of_result_data['Region'] == region:
						test_value = set_of_result_data['mocked_response']
						break
				if test_value is not None and isinstance(test_value, Exception):
					# Implied break and exit of the function here...
					print("Expected Error...")
					raise test_value
				elif test_value is None:
					print(f"No test data offered for this credentials in region {region}")
					continue
				print(f"Operation Name mocked: {operation_name}\n"
				      f"Function Name: {meta_key_dict['FunctionName']}\n"
				      f"kwargs: {kwargs}\n"
				      f"mocked return_response: {test_value}")
				return test_value

		print(f"Operation Name passed through: {operation_name}\n"
		      f"Function Name: {meta_key_dict['FunctionName']}\n"
		      f"kwargs: {kwargs}\n")
		return_response = orig(self, operation_name, kwargs)
		print(f"Actual return_response: {return_response}")
		return return_response

	mocker.patch('botocore.client.BaseClient._make_api_call', new=amend_make_api_call)
# mocker.patch('botocore.session', new=amend_make_api_call)
