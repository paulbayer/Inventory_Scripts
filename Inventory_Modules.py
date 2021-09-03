

def get_regions(fkey, fprofile="default"):
	import boto3
	import logging

	session_ec2 = boto3.Session(profile_name=fprofile)
	region_info = session_ec2.client('ec2')
	regions = region_info.describe_regions()
	RegionNames = []
	for x in range(len(regions['Regions'])):
		RegionNames.append(regions['Regions'][x]['RegionName'])
	if "all" in fkey or "ALL" in fkey:
		return (RegionNames)
	RegionNames2 = []
	for x in fkey:
		for y in RegionNames:
			logging.info('Have %s | Looking for %s', y, x)
			if y.find(x) >= 0:
				logging.info('Found %s', y)
				RegionNames2.append(y)
	return (RegionNames2)

def get_regions2(faws_acct, fregion_list=None):
	import logging

	session_ec2 = faws_acct.session
	region_info = session_ec2.client('ec2')
	regions = region_info.describe_regions()
	RegionNames = [region_name['RegionName'] for region_name in regions['Regions']]
	if  fregion_list is None or "all" in fregion_list or "ALL" in fregion_list or "All" in fregion_list:
		return (RegionNames)
	RegionNames2 = []
	for x in fregion_list:
		for y in RegionNames:
			logging.info(f"Have {y} | Looking for {x}")
			if y.find(x) >= 0:
				logging.info(f"Found {y}")
				RegionNames2.append(y)
	return (RegionNames2)


def get_ec2_regions(fkey=['all'], fprofile=None):
	import boto3
	import logging

	session_ec2 = boto3.Session()
	region_info = session_ec2.client('ec2')
	regions = region_info.describe_regions(Filters=[
		{'Name': 'opt-in-status', 'Values': ['opt-in-not-required', 'opted-in']}])
	RegionNames = []
	for x in range(len(regions['Regions'])):
		RegionNames.append(regions['Regions'][x]['RegionName'])
	if "all" in fkey or "ALL" in fkey or 'All' in fkey:
		return (RegionNames)
	RegionNames2 = []
	for x in fkey:
		for y in RegionNames:
			logging.info('Have %s | Looking for %s', y, x)
			if y.find(x) >= 0:
				logging.info('Found %s', y)
				RegionNames2.append(y)
	return (RegionNames2)


def get_ec2_regions2(fSessionObject, fkey=None):
	import boto3
	import logging

	session_ec2 = fSessionObject.session
	region_info = session_ec2.client('ec2')
	regions = region_info.describe_regions(Filters=[
		{'Name': 'opt-in-status', 'Values': ['opt-in-not-required', 'opted-in']}])
	RegionNames = []
	for x in range(len(regions['Regions'])):
		RegionNames.append(regions['Regions'][x]['RegionName'])
	if "all" in fkey or "ALL" in fkey or 'All' in fkey or fkey is None:
		return (RegionNames)
	RegionNames2 = []
	for x in fkey:
		for y in RegionNames:
			logging.info('Have %s | Looking for %s', y, x)
			if y.find(x) >= 0:
				logging.info('Found %s', y)
				RegionNames2.append(y)
	return (RegionNames2)


def get_service_regions(service, fkey=None):
	"""
	Parameters:
		service = the AWS service we're trying to get regions for. This is useful since not all services are supported in all regions.
		fkey = A *list* of string fragments of what region we're looking for.
			If not supplied, then we send back all regions for that service.
			If they send "us-" (for example), we would send back only those regions which matched that fragment.
			This is good for focusing a search on only those regions you're searching within.
	"""
	import boto3
	import logging

	s = boto3.Session()
	regions = s.get_available_regions(service, partition_name='aws', allow_non_regional=False)
	if fkey is None or ('all' in fkey or 'All' in fkey or 'ALL' in fkey):
		return (regions)
	RegionNames = []
	for x in fkey:
		for y in regions:
			logging.info('Have %s | Looking for %s', y, x)
			if y.find(x) >= 0:
				logging.info('Found %s', y)
				RegionNames.append(y)
	return (RegionNames)


def validate_region(fSessionObject, fRegion=None):
	import logging

	session_region = fSessionObject.session
	client_region = session_region.client('ec2')
	if fRegion is None:
		logging.info(f"No region supplied. Defaulting to 'us-east-1'")
		fRegion = 'us-east-1'
	region_info = client_region.describe_regions(Filters=[{'Name': 'region-name', 'Values': [fRegion]}])['Regions']
	if len(region_info) == 0:
		message = f"'{fRegion}' is not a valid region name for this account"
		logging.error(message)
		result = {'Result': False, 'Message': message}
		return(result)
	else:
		message = f"'{fRegion}' is a valid region name for this account"
		logging.error(message)
		result = {'Result': True, 'Message': message}
		return(result)


def get_profiles(fSkipProfiles=None, fprofiles=None):
	"""
	We assume that the user of this function wants all profiles.
	If they provide a list of profile strings (in fprofiles), then we compare those strings to the full list of profiles we have, and return those profiles that contain the strings they sent.
	"""
	import boto3
	import logging

	# TODO: We don't actually use this anywhere in the script. We should.
	if fSkipProfiles is None:
		fSkipProfiles = ['default']
	if fprofiles is None:
		fprofiles = ['all']
	my_Session = boto3.Session()
	my_profiles = my_Session._session.available_profiles
	if "all" in fprofiles or "ALL" in fprofiles:
		return (my_profiles)
	ProfileList = []
	for x in fprofiles:
		for y in my_profiles:
			logging.info('Have %s| Looking for %s', y, x)
			if y.find(x) >= 0:
				logging.info('Found profile %s', y)
				ProfileList.append(y)
	return (ProfileList)


def get_profiles2(fSkipProfiles=[None], fprofiles=[None]):
	"""
	We assume that the user of this function wants all profiles.
	If they provide a list of profile strings (in fprofiles), then we compare those strings to the full list of profiles we have, and return those profiles that contain the strings they sent.
	"""
	import boto3

	my_Session = boto3.Session()
	my_profiles = my_Session._session.available_profiles
	if "all" in fprofiles or "ALL" in fprofiles or fprofiles is None:
		my_profiles = list(set(my_profiles) - set(fSkipProfiles))
	else:
		my_profiles = list(set(fprofiles) - set(fSkipProfiles))
	return (my_profiles)


def get_parent_profiles(fprofiles=None, fSkipProfiles=None):
	"""
	This function should only return profiles from Payer Accounts.
	If they provide a list of profile strings (in fprofiles), then we compare those
	strings to the full list of profiles we have, and return those profiles that
	contain the strings AND are Payer Accounts.
	"""
	import boto3
	import logging

	from botocore.exceptions import ClientError

	ERASE_LINE = '\x1b[2K'
	if fSkipProfiles is None:
		fSkipProfiles = ['default']
	if fprofiles is None:
		fprofiles = ['all']
	my_Session = boto3.Session()
	my_profiles = my_Session._session.available_profiles
	logging.info("Profile string sent: %s", fprofiles)
	if "all" in fprofiles or "ALL" in fprofiles or "All" in fprofiles:
		my_profiles = list(set(my_profiles) - set(fSkipProfiles))
		logging.info("my_profiles %s:", my_profiles)
	else:
		my_profiles = list(set(fprofiles) - set(fSkipProfiles))
	my_profiles2 = []
	NumOfProfiles = len(my_profiles)
	for profile in my_profiles:
		print(ERASE_LINE, f"Checking {profile} Profile - {NumOfProfiles} more profiles to go", end='\r')
		logging.warning("Finding whether %s is a root profile", profile)
		try:
			AcctResult = find_if_org_root(profile)
		except ClientError as my_Error:
			print(my_Error)
			continue
		NumOfProfiles -= 1
		if AcctResult in ['Root', 'StandAlone']:
			logging.warning("%s is a %s Profile", profile, AcctResult)
			my_profiles2.append(profile)
		else:
			logging.warning("%s is a %s Profile", profile, AcctResult)
	return (my_profiles2)


# def find_if_org_root(fProfile):
# 	import logging
#
# 	logging.info("Finding if %s is an ORG root", fProfile)
# 	org_acct_number = find_account_attr(fProfile)
# 	logging.info(f"Profile {fProfile}'s Account Number is {org_acct_number['AccountNumber']}")
# 	logging.info(f"Profile {fProfile}'s Org Account Number is {org_acct_number['MasterAccountId']}")
# 	# acct_number = find_account_number(fProfile)
# 	return (org_acct_number['AccountType'])
# 	# if org_acct_number['MasterAccountId'] == acct_number:
# 	# 	logging.info("%s is a Root account", fProfile)
# 	# 	return ('Root')
# 	# elif org_acct_number['MasterAccountId'] == 'StandAlone':
# 	# 	logging.info("%s is a Standalone account", fProfile)
# 	# 	return ('StandAlone')
# 	# else:
# 	# 	logging.info("%s is a Child account", fProfile)
# 	# 	return ('Child')


def find_if_alz(fProfile):
	import boto3

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('s3')
	bucket_list = client_org.list_buckets()
	response = dict()
	response['BucketName'] = None
	response['ALZ'] = False
	for bucket in bucket_list['Buckets']:
		if "aws-landing-zone-configuration" in bucket['Name']:
			response['BucketName'] = bucket['Name']
			response['ALZ'] = True
			response['Region'] = find_bucket_location(fProfile, bucket['Name'])
	return (response)


def find_bucket_location(fProfile, fBucketname):
	import boto3
	import logging
	from botocore.exceptions import ClientError

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('s3')
	try:
		response = client_org.get_bucket_location(Bucket=fBucketname)
	except ClientError as my_Error:
		if str(my_Error).find("AccessDenied") > 0:
			logging.error(f"Authorization Failure for profile {fProfile}")
		return (None)
	if response['LocationConstraint'] is None:
		location = 'us-east-1'
	else:
		location = response['LocationConstraint']
	return (location)


def find_acct_email(fOrgRootProfile, fAccountId):
	import boto3
	"""
	This function *unfortunately* only works with organization accounts.
	"""

	session_org = boto3.Session(profile_name=fOrgRootProfile)
	client_org = session_org.client('organizations')
	email_addr = client_org.describe_account(AccountId=fAccountId)['Account']['Email']
	# email_addr = response['Account']['Email']
	return (email_addr)


def find_account_number(fProfile=None):
	import boto3
	import logging
	from botocore.exceptions import ClientError, CredentialRetrievalError, InvalidConfigError

	response = '123456789012'   # This is the Failure response
	try:
		# logging.info("Looking for profile %s", fProfile)
		if fProfile is None:
			sts_session = boto3.Session()
		else:
			sts_session = boto3.Session(profile_name=fProfile)
		client_sts = sts_session.client('sts')
		response = client_sts.get_caller_identity()['Account']
	except ClientError as my_Error:
		if str(my_Error).find("UnrecognizedClientException") > 0:
			logging.error("%s: Security Issue", fProfile)
			pass
		elif str(my_Error).find("InvalidClientTokenId") > 0:
			logging.error("%s: Security Token is bad - probably a bad entry in config", fProfile)
			pass
	except CredentialRetrievalError as my_Error:
		if str(my_Error).find("CredentialRetrievalError") > 0:
			logging.error("%s: Some custom process isn't working", fProfile)
			pass
	except InvalidConfigError as my_Error:
		if str(my_Error).find("InvalidConfigError") > 0:
			logging.error("%s: profile is invalid. Probably due to a config profile based on a credential that doesn't work", fProfile)
			pass
	except:
		logging.error("Other kind of failure for profile %s", fProfile)
		# print(my_Error)
		pass
	return (response)


def find_calling_identity(fProfile):
	import boto3
	import logging
	from botocore.exceptions import ClientError

	try:
		session_sts = boto3.Session(profile_name=fProfile)
		logging.info("Getting creds used within profile %s", fProfile)
		client_sts = session_sts.client('sts')
		response = client_sts.get_caller_identity()
		creds = {'Arn': response['Arn'], 'AccountId': response['Account'],
				 'Short': response['Arn'][response['Arn'].rfind(':') + 1:]}
	except ClientError as my_Error:
		if str(my_Error).find("UnrecognizedClientException") > 0:
			print(f"{fProfile}: Security Issue")
		elif str(my_Error).find("InvalidClientTokenId") > 0:
			print(f"{fProfile}: Security Token is bad - probably a bad entry in config")
		else:
			print(f"Other kind of failure for profile {fProfile}")
			print(my_Error)
		creds = "Failure"
	return (creds)


def find_account_attr(fSessionObject):
	import boto3
	import logging
	from botocore.exceptions import ClientError, CredentialRetrievalError

	"""
	In the case of an Org Root or Child account, I use the response directly from the AWS SDK.
	You can find the output format here: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/organizations.html#Organizations.Client.describe_organization
	"""
	FailResponse = {'AccountType': 'Unknown', 'AccountNumber': 'None', 'Id': 'None', 'MasterAccountId': 'None'}
	client_org = fSessionObject.session.client('organizations')
	try:
		response = client_org.describe_organization()['Organization']
		my_acct_number = find_account_number(fProfile)
		response['Id'] = my_acct_number
		response['AccountNumber'] = my_acct_number
		if response['MasterAccountId'] == my_acct_number:
			response['AccountType'] = 'Root'
		else:
			response['AccountType'] = 'Child'
		return (response)
	except ClientError as my_Error:
		if str(my_Error).find("UnrecognizedClientException") > 0:
			logging.error(f"Security Issue with: {fProfile}")
		elif str(my_Error).find("AWSOrganizationsNotInUseException") > 0:
			logging.error(f"{fProfile}: Account isn't a part of an Organization")  # Stand-alone account
			my_acct_number = find_account_number(fProfile)
			FailResponse['AccountType'] = 'StandAlone'
			FailResponse['Id'] = my_acct_number
			FailResponse['AccountNumber'] = my_acct_number
		elif str(my_Error).find("InvalidClientTokenId") > 0:
			logging.error(f"{fProfile}: Security Token is bad - probably a bad entry in config")
		elif str(my_Error).find("AccessDenied") > 0:
			logging.error(f"{fProfile}: Access Denied for profile")
		pass
	except CredentialRetrievalError as my_Error:
		print(f"{fProfile}: Failure pulling or updating credentials")
		print(my_Error)
		pass
	except:
		print("Other kind of failure")
		pass
	return (FailResponse)


# def find_child_accounts2(fProfile):
# 	"""
# 	This is an example of the list response from this call:
# 		[
# 		{'ParentProfile':'<profile name>', 'AccountId': 'xxxxxxxxxxxx', 'AccountEmail': 'EmailAddr1@example.com', 'AccountStatus': 'ACTIVE'},
# 		{'ParentProfile':'<profile name>', 'AccountId': 'yyyyyyyyyyyy', 'AccountEmail': 'EmailAddr2@example.com', 'AccountStatus': 'ACTIVE'},
# 		{'ParentProfile':'<profile name>', 'AccountId': 'zzzzzzzzzzzz', 'AccountEmail': 'EmailAddr3@example.com', 'AccountStatus': 'SUSPENDED'}
# 		]
# 	This can be convenient for appending and removing.
# 	"""
# 	import boto3
# 	import logging
# 	from botocore.exceptions import ClientError
#
# 	child_accounts = []
# 	org_root = find_if_org_root(fProfile)
# 	if org_root.lower() == 'root':
# 		try:
# 			session_org = boto3.Session(profile_name=fProfile)
# 			client_org = session_org.client('organizations')
# 			response = client_org.list_accounts()
# 			theresmore = True
# 			while theresmore:
# 				for account in response['Accounts']:
# 					logging.warning(f"Profile: {fProfile} | Account ID: {account['Id']} | Account Email: {account['Email']}")
# 					child_accounts.append({'ParentProfile': fProfile,
# 					                       'AccountId': account['Id'],
# 					                       'AccountEmail': account['Email'],
# 					                       'AccountStatus': account['Status']})
# 				if 'NextToken' in response.keys():
# 					theresmore = True
# 					response = client_org.list_accounts(NextToken=response['NextToken'])
# 				else:
# 					theresmore = False
# 			return (child_accounts)
# 		except ClientError as my_Error:
# 			logging.warning(f"Profile {fProfile} doesn't represent an Org Root account")
# 			logging.debug(my_Error)
# 			return()
# 	elif org_root.lower() in ['standalone', 'child']:
# 		accountID = find_account_number(fProfile)
# 		child_accounts.append({'ParentProfile': fProfile,
# 		                       'AccountId': accountID,
# 		                       'AccountEmail': 'NotAnOrgRoot@example.com',
# 		                       # We know the account is ACTIVE because if it was SUSPENDED, we wouldn't have gotten a valid response from the org_root check
# 		                       'AccountStatus': 'ACTIVE'})
# 		return (child_accounts)
# 	else:
# 		logging.warning(f"Profile {fProfile} doesn't represent an Org Root account")
# 		# logging.debug(my_Error)
# 		return()
#
#
# def find_child_accounts(fProfile="default"):
# 	"""
# 	This call returns a dictionary response, unlike the "find_child_accounts2" function (above) which returns a list.
# 	Our dictionary call looks like this where the 'xxxxxxxxxxxx' represents the 12 digit Account ID:
# 		{'xxxxxxxxxxxx': 'EmailAddr1@example.com',
# 		 'yyyyyyyyyyyy': 'EmailAddr2@example.com',
# 		 'zzzzzzzzzzzz': 'EmailAddr3@example.com'}
# 	This is convenient because it is easily sortable.
# 	"""
# 	import boto3
# 	import logging
# 	from botocore.exceptions import ClientError
#
# 	child_accounts = {}
# 	session_org = boto3.Session(profile_name=fProfile)
# 	theresmore = False
# 	try:
# 		client_org = session_org.client('organizations')
# 		response = client_org.list_accounts()
# 		theresmore = True
# 	except ClientError as my_Error:
# 		logging.warning(f"Profile {fProfile} doesn't represent an Org Root account")
# 		return ()
# 	while theresmore:
# 		for account in response['Accounts']:
# 			# Create a key/value pair with the AccountID:AccountEmail
# 			child_accounts[account['Id']] = account['Email']
# 		if 'NextToken' in response.keys():
# 			theresmore = True
# 			response = client_org.list_accounts(NextToken=response['NextToken'])
# 		else:
# 			theresmore = False
# 	return (child_accounts)


def RemoveCoreAccounts(MainList, AccountsToRemove=None):
	import logging
	"""
	MainList is expected to come through looking like this:
		[{'AccountEmail': 'User+LZ@example.com', 'AccountId': '0123xxxx8912'},
		{'AccountEmail': 'User+LZ_Log@example.com', 'AccountId': '1234xxxx9012'},
			< ... >
		{'AccountEmail': 'User+LZ_SS@example.com', 'AccountId': '9876xxxx1000'},
		{'AccountEmail': 'User+Demo@example.com', 'AccountId': '9638xxxx012'}]
	AccountsToRemove is simply a list of accounts you don't want to screw with. It might look like this:
		['9876xxxx1000', '9638xxxx1012']
	"""

	if AccountsToRemove is None:
		AccountsToRemove = []
	NewCA = []
	for i in range(len(MainList)):
		if MainList[i]['AccountId'] in AccountsToRemove:
			logging.info("Comparing %s to above", str(MainList[i]['AccountId']))
			continue
		else:
			logging.info("Account %s was allowed", str(MainList[i]['AccountId']))
			NewCA.append(MainList[i])
	return (NewCA)


# def get_child_access(fRootProfile, fRegion, fChildAccount, fRoleList = None):
# 	"""
# 	- fRootProfile is a string
# 	- rRegion expects a string representing one of the AWS regions ('us-east-1', 'eu-west-1', etc.)
# 	- fChildAccount expects an AWS account number (ostensibly of a Child Account)
# 	- fRoleList expects a list of roles to try, but defaults to a list of typical roles, in case you don't provide
#
# 	The response object is a Session object within boto3
# 	"""
# 	import boto3, logging
# 	from botocore.exceptions import ClientError
#
# 	if fRoleList == None:
# 		fRoleList = ['AWSCloudFormationStackSetExecutionRole', 'AWSControlTowerExecution', 'OrganizationAccountAccessRole',
# 	             'DevAccess']
# 	sts_session = boto3.Session(profile_name = fRootProfile)
# 	sts_client = sts_session.client('sts', region_name = fRegion)
# 	for role in fRoleList:
# 		try:
# 			role_arn='arn:aws:iam::'+fChildAccount+':role/'+role
# 			account_credentials = sts_client.assume_role(
# 				RoleArn = role_arn,
# 				RoleSessionName="Find-ChildAccount-Things")['Credentials']
# 			session_aws = boto3.Session(
# 				aws_access_key_id = account_credentials['AccessKeyId'],
# 				aws_secret_access_key = account_credentials['SecretAccessKey'],
# 				aws_session_token = account_credentials['SessionToken'],
# 				region_name = fRegion)
# 			return(session_aws)
# 		except ClientError as my_Error:
# 			if my_Error.response['Error']['Code'] == 'ClientError':
# 				logging.info(my_Error)
# 			return_string="{} failed. Try Again".format(str(fRoleList))
# 			continue
# 	return(return_string)


def get_child_access2(fRootProfile, fChildAccount, fRegion='us-east-1', fRoleList=None):
	"""
	- fRootProfile is a string
	- fChildAccount expects an AWS account number (ostensibly of a Child Account)
	- rRegion expects a string representing one of the AWS regions ('us-east-1', 'eu-west-1', etc.)
	- fRoleList expects a list of roles to try, but defaults to a list of typical roles, in case you don't provide

	The first response object is a dict with account_credentials to pass onto other functions
	The min response object is the rolename that worked to gain access to the target account

	The format of the account credentials dict is here:
	account_credentials = {'Profile': fRootProfile,
							'AccessKeyId': '',
							'SecretAccessKey': None,
							'SessionToken': None,
							'AccountNumber': None}
	"""
	import boto3
	import logging
	from botocore.exceptions import ClientError

	if not isinstance(fChildAccount, str):  # Make sure the passed in account number is a string
		fChildAccount = str(fChildAccount)
	ParentAccountId = find_account_number(fRootProfile)
	sts_session = boto3.Session(profile_name=fRootProfile)
	sts_client = sts_session.client('sts', region_name=fRegion)
	if fChildAccount == ParentAccountId:
		explain_string = ("We're trying to get access to either the Root Account (which we already have access "
		                  "to via the profile)	or we're trying to gain access to a Standalone account. "
		                  "In either of these cases, we should just use the profile passed in, "
		                  "instead of trying to do anything fancy.")
		logging.info(explain_string)
		# TODO: Wrap this in a try/except loop
		account_credentials = sts_client.get_session_token()['Credentials']
		account_credentials['AccountNumber'] = fChildAccount
		account_credentials['Profile'] = fRootProfile
		return (account_credentials, 'Check Profile')
	if fRoleList is None:
		fRoleList = ['AWSCloudFormationStackSetExecutionRole', 'AWSControlTowerExecution',
					 'OrganizationAccountAccessRole', 'AdministratorAccess', 'Owner']
	# Initializing the "Negative Use Case" string, returning the whole list instead of only the last role it tried.
	# This way the operator knows that NONE of the roles supplied worked.
	return_string = "{} failed. Try Again".format(str(fRoleList))

	account_credentials = {'Profile': fRootProfile,
	                       'AccessKeyId': None,
	                       'SecretAccessKey': None,
	                       'SessionToken': None,
						   'AccountNumber': None}
	for role in fRoleList:
		try:
			logging.info("Trying to access account %s using %s profile assuming role: %s", fChildAccount, fRootProfile, role)
			role_arn = f"arn:aws:iam::{fChildAccount}:role/{role}"
			account_credentials = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="Find-ChildAccount-Things")['Credentials']
			# If we were successful up to this point, then we'll short-cut everything and just return the credentials that worked
			account_credentials['Profile'] = fRootProfile
			account_credentials['AccountNumber'] = fChildAccount
			return (account_credentials, role)
		except ClientError as my_Error:
			if my_Error.response['Error']['Code'] == 'ClientError':
				logging.info(my_Error)
			continue
	# Returns a dict object since that's what's expected
	# It will only get to the part below if the child isn't accessed properly using the roles already defined
	return (account_credentials, return_string)


def get_child_access3(fAccountObject, fChildAccount, fRegion='us-east-1', fRoleList=None):
	"""
	- fAccountObject is a custom class (account_class.aws_acct_access)
	- fChildAccount expects an AWS account number (ostensibly of a Child Account)
	- rRegion expects a string representing one of the AWS regions ('us-east-1', 'eu-west-1', etc.)
	- fRoleList expects a list of roles to try, but defaults to a list of typical roles, in case you don't provide

	The first response object is a dict with account_credentials to pass onto other functions

	The format of the account credentials dict is here:
	account_credentials = {'ParentAcctId': ParentAccountId,
							'AccessKeyId': None,
							'SecretAccessKey': None,
							'SessionToken': None,
							'AccountNumber': None,
							'Role': Role that worked to get in}
	"""
	import logging
	from botocore.exceptions import ClientError

	if not isinstance(fChildAccount, str):  # Make sure the passed in account number is a string
		fChildAccount = str(fChildAccount)
	org_status = fAccountObject.AccountType
	ParentAccountId = fAccountObject.acct_number
	sts_client = fAccountObject.session.client('sts')
	if fChildAccount == ParentAccountId:
		explain_string = (f"We're trying to get access to either the Root Account (which we already have access "
		                  f"to via the profile) or we're trying to gain access to a Standalone account. "
		                  f"In either of these cases, we should just use the profile passed in, "
		                  f"instead of trying to do anything fancy.")
		logging.info(explain_string)
		# TODO: Wrap this in a try/except loop on the off-chance that the class doesn't work properly
		account_credentials = {'ParentAcctId': ParentAccountId,
		                       'OrgType': org_status,
		                       'AccessKeyId': fAccountObject.creds.access_key,
		                       'SecretAccessKey': fAccountObject.creds.secret_key,
		                       'SessionToken': fAccountObject.creds.token,
		                       'AccountNumber': fChildAccount,
		                       'AccountId': fChildAccount,
		                       'Role': 'Use Profile'}
		return (account_credentials)
	if fRoleList is None:
		fRoleList = ['AWSCloudFormationStackSetExecutionRole', 'AWSControlTowerExecution',
					 'OrganizationAccountAccessRole', 'AdministratorAccess', 'Owner']
	# Initializing the "Negative Use Case" string, returning the whole list instead of only the last role it tried.
	# This way the operator knows that NONE of the roles supplied worked.
	return_string = "{} failed. Try Again".format(str(fRoleList))
	account_credentials = {'ParentAcctId': ParentAccountId,
	                       'OrgType': org_status,
	                       'AccessKeyId': None,
	                       'SecretAccessKey': None,
	                       'SessionToken': None,
						   'AccountNumber': None,
						   'AccountId': None,
						   'Role': None}
	for role in fRoleList:
		try:
			if fAccountObject.session.profile_name:
				logging.info(f"Trying to access account {fChildAccount} using parent profile: {fAccountObject.session.profile_name} assuming role: {role}")
			else:
				logging.info(f"Trying to access account {fChildAccount} using account number {fAccountObject.acct_number} assuming role: {role}")
			role_arn = f"arn:aws:iam::{fChildAccount}:role/{role}"
			account_credentials = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="Test-ChildAccount-Access")['Credentials']
			# If we were successful up to this point, then we'll short-cut everything and just return the credentials that worked
			logging.info(f"The credentials for account {fChildAccount} using parent account {fAccountObject.acct_number} and role name {role} worked")
			account_credentials['ParentAcctId'] = ParentAccountId
			account_credentials['OrgType'] = org_status
			account_credentials['AccountNumber'] = fChildAccount
			account_credentials['AccountId'] = fChildAccount
			account_credentials['Role'] = role
			return (account_credentials)
		except ClientError as my_Error:
			logging.info(my_Error)
			continue
	# Returns a dict object since that's what's expected
	# It will only get to the part below if the child isn't accessed properly using the roles already defined
	account_credentials['AccessError'] = True
	return (account_credentials)


def enable_drift_on_stacks(ocredentials, fRegion, fStackName):
	import boto3
	import logging

	session_cfn = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
		'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'], region_name=fRegion)
	client_cfn = session_cfn.client('cloudformation')
	logging.warning("Enabling drift detection on Stack %s in Account %s in region %s", fStackName,
					ocredentials['AccountNumber'], fRegion)
	response = client_cfn.detect_stack_drift(StackName=fStackName)
	return (response)  # There is no response to send back


"""
Above - Generic functions
Below - Specific functions to specific features
"""


def find_sns_topics(ocredentials, fRegion, fTopicFrag=None):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number

	Returns:
		List of Topic ARNs found that match the fragment sent
"""
	import boto3
	import logging
	if fTopicFrag is None:
		fTopicFrag = ['all']
	session_sns = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'],
	                            aws_secret_access_key=ocredentials['SecretAccessKey'],
	                            aws_session_token=ocredentials['SessionToken'],
	                            region_name=fRegion)
	client_sns = session_sns.client('sns')
	# TODO: Enable pagination
	response = client_sns.list_topics()
	TopicList = []
	for item in response['Topics']:
		TopicList.append(item['TopicArn'])
	if 'all' in fTopicFrag:
		logging.warning("Looking for all SNS Topics in account %s from Region %s",
						ocredentials['AccountNumber'],
						fRegion
		                )
		logging.info("Topic Arns Returned: %s", TopicList)
		logging.warning("We found %s SNS Topics", len(TopicList))
		return (TopicList)
	else:
		logging.warning(f"Looking for specific SNS Topics in account {ocredentials['AccountNumber']} from Region {fRegion}")
		topic_list2 = []
		for item in fTopicFrag:
			for topic in TopicList:
				logging.info(f"Have {topic} | Looking for {item}")
				if topic.find(item) >= 0:
					logging.error(f"Found {topic}")
					topic_list2.append(topic)
		logging.warning("We found %s SNS Topics", len(topic_list2))
		return (topic_list2)


def find_role_names(ocredentials, fRegion, fRoleNameFrag=None):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number

	Returns:
		List of Role Names found that match the fragment list sent
	"""
	import boto3
	import logging
	if fRoleNameFrag is None:
		fRoleNameFrag = ['all']
	session_iam = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'],
	                            aws_secret_access_key=ocredentials['SecretAccessKey'],
	                            aws_session_token=ocredentials['SessionToken'],
	                            region_name=fRegion)
	client_iam = session_iam.client('iam')
	# TODO: Enable pagination
	response = client_iam.list_roles()['Roles']
	RoleNameList = []
	for item in response:
		RoleNameList.append(item['RoleName'])
	if 'all' in fRoleNameFrag:
		logging.warning(f"Looking for all RoleNames in account {ocredentials['AccountNumber']} from Region {fRegion}")
		logging.info(f"RoleName Arns Returned: {RoleNameList}", )
		logging.warning(f"We found {len(RoleNameList)} RoleNames")
		return (RoleNameList)
	else:
		logging.warning(f"Looking for specific RoleNames in account {ocredentials['AccountNumber']} from Region {fRegion}")
		RoleNameList2 = []
		for item in fRoleNameFrag:
			for RoleName in RoleNameList:
				logging.info('Have %s | Looking for %s', RoleName, item)
				if RoleName.find(item) >= 0:
					logging.warning('Found %s', RoleName)
					RoleNameList2.append(RoleName)
		logging.warning("We found %s Roles", len(RoleNameList2))
		return (RoleNameList2)


def find_cw_log_group_names(ocredentials, fRegion, fCWLogGroupFrag=None):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number

	Returns:
		List of CloudWatch Log Group Names found that match the fragment list
"""
	import boto3
	import logging
	if fCWLogGroupFrag is None:
		fCWLogGroupFrag = ['all']
	session_cw = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'],
							   aws_secret_access_key=ocredentials['SecretAccessKey'],
							   aws_session_token=ocredentials['SessionToken'],
							   region_name=fRegion)
	client_cw = session_cw.client('logs')
	# TODO: Enable pagination # Defaults to 50
	CWLogGroupList = []
	FirstTime = True
	response = {}
	while 'nextToken' in response.keys() or FirstTime:
		FirstTime = False
		response = client_cw.describe_log_groups()
		for item in response['logGroups']:
			CWLogGroupList.append(item['logGroupName'])
	if 'all' in fCWLogGroupFrag:
		logging.warning("Looking for all Log Group names in account %s from Region %s",
						ocredentials['AccountNumber'], fRegion)
		logging.info("Log Group Names Returned: %s", CWLogGroupList)
		logging.warning(f"We found {len(CWLogGroupList)} Log Group names")
		return (CWLogGroupList)
	else:
		logging.warning(f"Looking for specific Log Group names in account {ocredentials['AccountNumber']} from Region {fRegion}")
		CWLogGroupList2 = []
		for item in fCWLogGroupFrag:
			for logGroupName in CWLogGroupList:
				logging.info(f"Have {logGroupName} | Looking for {item}")
				if logGroupName.find(item) >= 0:
					logging.warning(f"Found {logGroupName}")
					CWLogGroupList2.append(logGroupName)
		logging.warning(f"We found {len(CWLogGroupList2)} Log Groups")
		return (CWLogGroupList2)


def find_account_vpcs(ocredentials, fRegion, defaultOnly=False):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	"""
	import boto3
	import logging

	session_vpc = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
		'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'], region_name=fRegion)
	client_vpc = session_vpc.client('ec2')
	if defaultOnly:
		logging.warning("Looking for default VPCs in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
		logging.info("defaultOnly: %s", str(defaultOnly))
		response = client_vpc.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
	else:
		logging.warning("Looking for all VPCs in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
		logging.info("defaultOnly: %s", str(defaultOnly))
		response = client_vpc.describe_vpcs()
	# TODO: Enable pagination
	logging.warning("We found %s VPCs", len(response['Vpcs']))
	return (response)


def find_config_recorders(ocredentials, fRegion):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number

	Returned object looks like:
	{
		"ConfigurationRecorders": [
			{
				"name": "AWS-Landing-Zone-BaselineConfigRecorder",
				"roleARN": "arn:aws:iam::123456789012:role/AWS-Landing-Zone-ConfigRecorderRole",
				"recordingGroup": {
					"allSupported": true,
					"includeGlobalResourceTypes": true,
					"resourceTypes": []
				}
			}
		]
	}

	Pagination isn't an issue here since only one config recorder per account / region is allowed.
	"""
	import boto3
	import logging
	session_cfg = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
		'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'], region_name=fRegion)
	client_cfg = session_cfg.client('config')
	logging.warning("Looking for Config Recorders in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
	response = client_cfg.describe_configuration_recorders()
	# logging.info(response)
	return (response)


def del_config_recorder(ocredentials, fRegion, fConfig_recorder_name):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	fRegion = region
	fConfig_recorder_name = Config Recorder Name
	"""
	import boto3
	import logging
	session_cfg = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
		'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'], region_name=fRegion)
	client_cfg = session_cfg.client('config')
	logging.error("Deleting Config Recorder %s from Region %s in account %s", fConfig_recorder_name, fRegion,
				  ocredentials['AccountNumber'])
	response = client_cfg.delete_configuration_recorder(ConfigurationRecorderName=fConfig_recorder_name)
	return (response)  # There is no response to send back


def find_delivery_channels(ocredentials, fRegion):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number

	Returned object looks like:
	{
		'DeliveryChannels': [
		{
			'name': 'string',
			's3BucketName': 'string',
			's3KeyPrefix': 'string',
			'snsTopicARN': 'string',
			'configSnapshotDeliveryProperties': {
				'deliveryFrequency': 'One_Hour'|'Three_Hours'|'Six_Hours'|'Twelve_Hours'|'TwentyFour_Hours'
			}
		},
		]
	}

	Pagination isn't an issue here since delivery channels are limited to only one / account / region
	"""
	import boto3
	import logging

	session_cfg = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
		'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'], region_name=fRegion)
	client_cfg = session_cfg.client('config')
	logging.warning("Looking for Delivery Channels in account %s from Region %s",
					ocredentials['AccountNumber'], fRegion)

	response = client_cfg.describe_delivery_channels()
	return (response)


def del_delivery_channel(ocredentials, fRegion, fDelivery_channel_name):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	rRegion = region
	fDelivery_channel_name = delivery channel name
	"""
	import boto3
	import logging

	session_cfg = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
		'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'], region_name=fRegion)
	client_cfg = session_cfg.client('config')
	logging.error("Deleting Delivery Channel %s from Region %s in account %s", fDelivery_channel_name, fRegion,
				  ocredentials['AccountNumber'])
	response = client_cfg.delete_delivery_channels(DeliveryChannelName=fDelivery_channel_name)
	return (response)


def find_cloudtrails(ocredentials, fRegion, fCloudTrailnames=None):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	fRegion = region
	fCloudTrailnames = List of CloudTrail names we're looking for (null value returns all cloud trails)

	Returned Object looks like this:
	{
		'trailList': [
			{
				'Name': 'string',
				'S3BucketName': 'string',
				'S3KeyPrefix': 'string',
				'SnsTopicName': 'string',
				'SnsTopicARN': 'string',
				'IncludeGlobalServiceEvents': True|False,
				'IsMultiRegionTrail': True|False,
				'HomeRegion': 'string',
				'TrailARN': 'string',
				'LogFileValidationEnabled': True|False,
				'CloudWatchLogsLogGroupArn': 'string',
				'CloudWatchLogsRoleArn': 'string',
				'KmsKeyId': 'string',
				'HasCustomEventSelectors': True|False,
				'HasInsightSelectors': True|False,
				'IsOrganizationTrail': True|False
			},
		]
	}
	CTtrails = Inventory_Modules.find_cloudtrails(account_creds, 'us-east-1', ['AWS-Landing-Zone-BaselineCloudTrail'])
	"""
	import boto3
	import logging
	from botocore.exceptions import ClientError

	session_ct = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'],
	                           aws_secret_access_key=ocredentials['SecretAccessKey'],
	                           aws_session_token=ocredentials['SessionToken'],
	                           region_name=fRegion)
	client_ct = session_ct.client('cloudtrail')
	logging.info(f"Looking for CloudTrail trails in account {ocredentials['AccountNumber']} from Region {fRegion}")
	fullresponse = []
	if fCloudTrailnames is None or len(fCloudTrailnames) == 0:  # Therefore - they're really looking for a list of trails
		try:
			response = client_ct.list_trails()
			fullresponse = response['Trails']
			if 'NextToken' in response.keys():
				while 'NextToken' in response.keys():
					response = client_ct.list_trails(NextToken=response['NextToken'])
					fullresponse.extend(response['Trails'])
		except ClientError as my_Error:
			logging.error(my_Error)
			fullresponse = f"{trailname} didn't work. Try Again"
		return(fullresponse)
	else:
		#  TODO: This doesn't work... Needs to be fixed.
		#  TODO: The reason this doesn't work is because the user submits a *list* of names, but the function exits after only one match, so the min match is never found.
		# They've provided a list of trails and want specific info about them
		for trailname in fCloudTrailnames:
			response = f"{trailname} didn't work. Try Again"
			try:
				response = client_ct.describe_trails(trailNameList=[trailname])
				fullresponse.extend(response['trailList'])
			except ClientError as my_Error:
				if str(my_Error).find("InvalidTrailNameException") > 0:
					logging.error("Bad CloudTrail name provided")
				# TODO: This is also wrong, since it belongs outside this try (remember - this is a list)
				# TODO: But since the top part is broken, I'm leaving this broken too.
		return(fullresponse)


def del_cloudtrails(ocredentials, fRegion, fCloudTrail):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	fRegion = region
	fCloudTrail = CloudTrail we're deleting
	"""
	import boto3
	import logging

	session_ct = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
		'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'], region_name=fRegion)
	client_ct = session_ct.client('cloudtrail')
	logging.info("Deleting CloudTrail %s in account %s from Region %s", fCloudTrail,
				 ocredentials['AccountNumber'], fRegion)
	response = client_ct.delete_trail(Name=fCloudTrail)
	return (response)


def find_gd_invites(ocredentials, fRegion):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	fRegion = region
	"""
	import boto3
	import logging

	from botocore.exceptions import ClientError

	session_gd = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
		'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'], region_name=fRegion)
	client_gd = session_gd.client('guardduty')
	logging.info("Looking for GuardDuty invitations in account %s from Region %s",
				 ocredentials['AccountNumber'], fRegion)
	try:
		response = client_gd.list_invitations()
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(ocredentials['AccountNumber'] + ": Authorization Failure for account {}".format(
				ocredentials['AccountNumber']))
		if str(my_Error).find("security token included in the request is invalid") > 0:
			print("Account #:" + ocredentials[
				'AccountNumber'] + f" - It's likely that the region you're trying ({fRegion}) isn't enabled for your account")
		else:
			print(my_Error)
		response = {'Invitations': []}
	return (response)


def delete_gd_invites(ocredentials, fRegion, fAccountId):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	fRegion = region
	"""
	import boto3
	import logging

	from botocore.exceptions import ClientError

	session_gd = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
		'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'], region_name=fRegion)
	client_gd = session_gd.client('guardduty')
	logging.info("Looking for GuardDuty invitations in account %s in Region %s",
				 ocredentials['AccountNumber'], fRegion)
	try:
		response = client_gd.delete_invitations(AccountIds=[fAccountId])
		return (response['Invitations'])
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(f"{ocredentials['AccountNumber']}: Authorization Failure for account {ocredentials['AccountNumber']}")
		if str(my_Error).find("security token included in the request is invalid") > 0:
			print(f"Account #:{ocredentials['AccountNumber']} - It's likely that the region you're trying ({fRegion}) isn't enabled for your account")
		else:
			print(my_Error)


def find_account_instances(ocredentials, fRegion='us-east-1'):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
		- ['Profile'] can hold the profile, instead of the session credentials
	"""
	import boto3
	import logging

	if 'Profile' in ocredentials.keys() and ocredentials['Profile'] is not None:
		ProfileAccountNumber = find_account_number(ocredentials['Profile'])
		logging.info(f"Profile: {ocredentials['Profile']} | Profile Account Number: {ProfileAccountNumber} | Account Number passed in: {ocredentials['AccountNumber']}")
		if ProfileAccountNumber == ocredentials['AccountNumber']:
			session_ec2 = boto3.Session(profile_name=ocredentials['Profile'], region_name=fRegion)
		else:
			session_ec2 = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'],
										aws_secret_access_key=ocredentials['SecretAccessKey'],
										aws_session_token=ocredentials['SessionToken'],
										region_name=fRegion)
	else:
		session_ec2 = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
			'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'], region_name=fRegion)
	instance_info = session_ec2.client('ec2')
	logging.warning("Looking for instances in account # %s in region %s", ocredentials['AccountNumber'], fRegion)
	instances = instance_info.describe_instances()
	AllInstances = instances
	while 'NextToken' in instances.keys():
		instances = instance_info.describe_instances(NextToken=instances['NextToken'])
		AllInstances['Reservations'].extend(instances['Reservations'])
	return (AllInstances)


def find_users(ocredentials):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
	"""
	import boto3
	import logging

	logging.warning("Key ID #: %s ", str(ocredentials['AccessKeyId']))
	session_iam = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'], aws_secret_access_key=ocredentials[
		'SecretAccessKey'], aws_session_token=ocredentials['SessionToken'])
	user_info = session_iam.client('iam')
	users = user_info.list_users()['Users']
	# TODO: Consider pagination here
	return (users)


def find_profile_vpcs(fProfile, fRegion, fDefaultOnly):
	import boto3
	session_ec2 = boto3.Session(profile_name=fProfile, region_name=fRegion)
	vpc_info = session_ec2.client('ec2')
	if fDefaultOnly:
		vpcs = vpc_info.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
	else:
		vpcs = vpc_info.describe_vpcs()
	return (vpcs)


def find_profile_functions(fProfile, fRegion):
	import boto3
	session_lambda = boto3.Session(profile_name=fProfile, region_name=fRegion)
	lambda_info = session_lambda.client('lambda')
	functions = lambda_info.list_functions()
	return (functions)


def find_lambda_functions(ocredentials, fRegion, fSearchStrings):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the AccountId
	fRegion is a string
	fSearchString is a list of strings
	"""
	import boto3
	import logging
	session_lambda = boto3.Session(region_name=fRegion, aws_access_key_id=ocredentials[
		'AccessKeyId'], aws_secret_access_key=ocredentials['SecretAccessKey'], aws_session_token=ocredentials[
		'SessionToken'])
	client_lambda = session_lambda.client('lambda')
	functions = client_lambda.list_functions()['Functions']
	functions2 = []
	for i in range(len(functions)):
		for searchitem in fSearchStrings:
			if searchitem in functions[i]['FunctionName']:
				logging.warning(f"Found function {functions[i]['FunctionName']}")
				functions2.append({'FunctionName': functions[i]['FunctionName'],
								   'FunctionArn': functions[i]['FunctionArn'], 'Role': functions[i]['Role']})
	return (functions2)


def get_lambda_code_url(fprofile, fregion, fFunctionName):
	import boto3
	session_lambda = boto3.Session(profile_name=fprofile, region_name=fregion)
	client_lambda = session_lambda.client('lambda')
	code_url = client_lambda.get_function(FunctionName=fFunctionName)['Code']['Location']
	return (code_url)


def find_private_hosted_zones(fProfile, fRegion):
	import boto3
	session_r53 = boto3.Session(profile_name=fProfile, region_name=fRegion)
	phz_info = session_r53.client('route53')
	hosted_zones = phz_info.list_hosted_zones()
	return (hosted_zones)


def find_private_hosted_zones2(ocredentials, fRegion):
	import boto3
	session_r53 = boto3.Session(region_name=fRegion, aws_access_key_id=ocredentials[
		'AccessKeyId'], aws_secret_access_key=ocredentials['SecretAccessKey'], aws_session_token=ocredentials[
		'SessionToken'])
	phz_info = session_r53.client('route53')
	hosted_zones = phz_info.list_hosted_zones()
	return (hosted_zones)


def find_load_balancers(fProfile, fRegion, fStackFragment='all', fStatus='all'):
	import boto3
	import logging

	logging.warning("Profile: %s | Region: %s | Fragment: %s | Status: %s", fProfile, fRegion, fStackFragment, fStatus)
	session_cfn = boto3.Session(profile_name=fProfile, region_name=fRegion)
	lb_info = session_cfn.client('elbv2')
	load_balancers = lb_info.describe_load_balancers()
	load_balancers_Copy = []
	if fStackFragment.lower() == 'all' and (fStatus.lower() == 'active' or fStatus.lower() == 'all'):
		logging.warning("Found all the lbs in Profile: %s in Region: %s with Fragment: %s and Status: %s", fProfile, fRegion, fStackFragment, fStatus)
		return (load_balancers['LoadBalancers'])
	elif (fStackFragment.lower() == 'all'):
		for load_balancer in load_balancers['LoadBalancers']:
			if fStatus in load_balancer['State']['Code']:
				logging.warning("Found lb %s in Profile: %s in Region: %s with Fragment: %s and Status: %s",
								load_balancers['LoadBalancerName'], fProfile, fRegion, fStackFragment, fStatus)
				load_balancers_Copy.append(load_balancer)
	elif fStatus.lower() == 'active':
		for load_balancer in load_balancers['LoadBalancers']:
			if fStackFragment in load_balancer['LoadBalancerName']:
				logging.warning("Found lb %s in Profile: %s in Region: %s with Fragment: %s and Status: %s",
								load_balancers['LoadBalancerName'], fProfile, fRegion, fStackFragment, fStatus)
				load_balancers_Copy.append(load_balancer)
	return (load_balancers_Copy)


def find_stacks(fProfile, fRegion, fStackFragment="all", fStatus="active"):
	"""
	fProfile refers to the name of the profile you're connecting to:
	fRegion refers to  the region you're connecting to
	fStackFragment is a string fragment to match to filter stacks by name
	fStatus is a string describing the status of the stacks you want to find

	There should be (4) use-cases here:
	1. All active stacks, but only the ones that match the fragment sent via parameter.
	2. All active stacks, regardless of name or status. For that - you could supply only the first two parameters
	3. All stacks, regardless of name or status. Only the stacks that match the status you've provided.
		For that - you would provide 'all' as the 3rd parameter and 4th parameter.
	4. Only those stacks that match the string fragment you've sent, and that match the status you've sent.

	Returns a dict that looks like this:
		'StackId':
		'StackName':
		'TemplateDescription':
		'CreationTime': {
			'day':
			'fold':
			'hour':
			'max':
			'microsecond':
			'min':
			'minute':
			'month':
			'resolution':
			'min':
			'tzinfo':
			'year':
		}
		'StackStatus':
		'DriftInformation': {
			'StackDriftStatus': ['NOT_CHECKED']
		}

	"""
	import boto3
	import logging

	logging.warning("Profile: %s | Region: %s | Fragment: %s | Status: %s", fProfile, fRegion, fStackFragment, fStatus)
	session_cfn = boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn = session_cfn.client('cloudformation')
	response = client_cfn.describe_stacks()
	AllStacks = response['Stacks']
	logging.info("Found %s stacks this time around", len(response['Stacks']))
	while 'NextToken' in response.keys():
		response = client_cfn.describe_stacks()
		AllStacks.extend(response['Stacks'])
		logging.info("Found %s stacks this time around", len(response['Stacks']))
	logging.info("Done with loops and found a total of %s stacks", len(AllStacks))
	stacksCopy = []
	stacks = dict()
	if fStatus.lower() == 'active' and not fStackFragment.lower() == 'all':
		# Send back stacks that are active, check the fragment further down.
		# stacks = client_cfn.list_stacks(StackStatusFilter=["CREATE_COMPLETE", "DELETE_FAILED", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE", "DELETE_IN_PROGRESS"])
		logging.warning("1 - Found %s stacks. Looking for fragment %s", len(AllStacks), fStackFragment)
		for stack in AllStacks:
			if fStackFragment in stack['StackName']:
				# Check the fragment now - only send back those that match
				logging.warning("Found stack %s in Profile: %s in Region: %s with Fragment: %s and Status: %s",
								stack['StackName'], fProfile, fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	elif fStatus.lower() == 'active' and fStackFragment.lower() == 'all':
		# Send back all stacks regardless of fragment, check the status further down.
		# TODO: This section needs paging
		stacks = client_cfn.list_stacks(StackStatusFilter=["CREATE_COMPLETE", "DELETE_FAILED", "UPDATE_COMPLETE",
														   "UPDATE_ROLLBACK_COMPLETE"])
		logging.warning("2 - Found ALL %s stacks in 'active' status.", len(stacks['StackSummaries']))
		for stack in stacks['StackSummaries']:
			# if fStatus in stack['StackStatus']:
			# Check the status now - only send back those that match a single status
			# I don't see this happening unless someone wants Stacks in a "Deleted" or "Rollback" type status
			logging.warning("Found stack %s in Profile: %s in Region: %s regardless of fragment and Status: %s",
							stack['StackName'], fProfile, fRegion, fStatus)
			stacksCopy.append(stack)
	elif fStatus.lower() == 'all' and fStackFragment.lower() == 'all':
		# Send back all stacks.
		# TODO: Need paging here
		stacks = client_cfn.list_stacks()
		logging.warning("3 - Found ALL %s stacks in ALL statuses", len(stacks['StackSummaries']))
		return (stacks['StackSummaries'])
	elif not fStatus.lower() == 'active':
		try:
			# TODO: Need paging here
			stacks = client_cfn.list_stacks()
			# TODO: The logic in this script to actually filter on the status is missing.
			# stacks = client_cfn.list_stacks(stackstatusfilter = [''])
			# The valid parameters to use here:
			# StackStatusFilter = [
			#   'CREATE_IN_PROGRESS'
			# | 'CREATE_FAILED'
			# | 'CREATE_COMPLETE'
			# | 'ROLLBACK_IN_PROGRESS'
			# | 'ROLLBACK_FAILED'
			# | 'ROLLBACK_COMPLETE'
			# | 'DELETE_IN_PROGRESS'
			# | 'DELETE_FAILED'
			# | 'DELETE_COMPLETE'
			# | 'UPDATE_IN_PROGRESS'
			# | 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS'
			# | 'UPDATE_COMPLETE'
			# | 'UPDATE_ROLLBACK_IN_PROGRESS'
			# | 'UPDATE_ROLLBACK_FAILED'
			# | 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS'
			# | 'UPDATE_ROLLBACK_COMPLETE'
			# | 'REVIEW_IN_PROGRESS'
			# | 'IMPORT_IN_PROGRESS'
			# | 'IMPORT_COMPLETE'
			# | 'IMPORT_ROLLBACK_IN_PROGRESS'
			# | 'IMPORT_ROLLBACK_FAILED'
			# | 'IMPORT_ROLLBACK_COMPLETE', ]
			logging.warning("4 - Found %s stacks ", len(stacks['StackSummaries']))
		except Exception as e:
			print(e)
		if 'StackSummaries' in stacks.keys():
			for stack in stacks['StackSummaries']:
				if fStackFragment in stack['StackName']:
					# Check the fragment now - only send back those that match
					logging.warning("Found stack %s in Profile: %s in Region: %s with Fragment: %s and Status: %s",
									stack['StackName'], fProfile, fRegion, fStackFragment, stack['StackStatus'])
					stacksCopy.append(stack)
	return (stacksCopy)


def delete_stack(fprofile, fRegion, fStackName, **kwargs):
	"""
	fprofile is an string holding the name of the profile you're connecting to:
	fRegion is a string
	fStackName is a string
	RetainResources should be a boolean
	ResourcesToRetain should be a list
	"""
	import boto3
	import logging
	RetainResources = False
	ResourcesToRetain = []
	if "RetainResources" in kwargs:
		RetainResources = True
		ResourcesToRetain = kwargs['ResourcesToRetain']
	session_cfn = boto3.Session(profile_name=fprofile, region_name=fRegion)
	client_cfn = session_cfn.client('cloudformation')
	if RetainResources:
		logging.warning("Profile: %s | Region: %s | StackName: %s", fprofile, fRegion, fStackName)
		logging.warning("	Retaining Resources: %s", ResourcesToRetain)
		response = client_cfn.delete_stack(StackName=fStackName, RetainResources=ResourcesToRetain)
	else:
		logging.warning("Profile: %s | Region: %s | StackName: %s", fprofile, fRegion, fStackName)
		response = client_cfn.delete_stack(StackName=fStackName)
	return (response)


def delete_stack2(ocredentials, fRegion, fStackName, **kwargs):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the AccountId
	fRegion is a string
	fStackName is a string
	RetainResources should be a boolean
	ResourcesToRetain should be a list
	"""
	import boto3
	import logging
	RetainResources = False
	ResourcesToRetain = []
	if "RetainResources" in kwargs:
		RetainResources = True
		ResourcesToRetain = kwargs['ResourcesToRetain']
	session_cfn = boto3.Session(region_name=fRegion,
								aws_access_key_id=ocredentials['AccessKeyId'],
								aws_secret_access_key=ocredentials['SecretAccessKey'],
								aws_session_token=ocredentials['SessionToken'])
	client_cfn = session_cfn.client('cloudformation')
	if RetainResources:
		logging.warning("Account: %s | Region: %s | StackName: %s", ocredentials['AccountNumber'], fRegion, fStackName)
		logging.warning("	Retaining Resources: %s", ResourcesToRetain)
		response = client_cfn.delete_stack(StackName=fStackName, RetainResources=ResourcesToRetain)
	else:
		logging.warning("Account: %s | Region: %s | StackName: %s",
						ocredentials['AccountNumber'],
						fRegion,
						fStackName)
		response = client_cfn.delete_stack(StackName=fStackName)
	return (response)


def find_stacks_in_acct(ocredentials, fRegion, fStackFragment="all", fStatus="active"):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the AccountId

	fRegion is a string
	fStackFragment is a string - default to "all"
	fStatus is a string - default to "active"
	"""
	import boto3
	import logging
	logging.error("Acct ID #: %s | Region: %s | Fragment: %s | Status: %s", str(
		ocredentials['AccountNumber']), fRegion, fStackFragment, fStatus)
	session_cfn = boto3.Session(region_name=fRegion,
								aws_access_key_id=ocredentials['AccessKeyId'],
								aws_secret_access_key=ocredentials['SecretAccessKey'],
								aws_session_token=ocredentials['SessionToken'])
	client_cfn = session_cfn.client('cloudformation')
	stacks = dict()
	stacksCopy = []
	if fStatus.lower() == 'active' and not fStackFragment.lower() == 'all':
		# Send back stacks that are active, check the fragment further down.
		stacks = client_cfn.list_stacks(StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE",
														   "UPDATE_ROLLBACK_COMPLETE"])
		for stack in stacks['StackSummaries']:
			if fStackFragment in stack['StackName']:
				# Check the fragment now - only send back those that match
				logging.error("1-Found stack %s in Account: %s in Region: %s with Fragment: %s and Status: %s",
							  stack['StackName'],
							  ocredentials['AccountNumber'],
							  fRegion,
							  fStackFragment,
							  fStatus)
				stacksCopy.append(stack)
	elif fStackFragment.lower() == 'all' and fStatus.lower() == 'all':
		# Send back all stacks.
		# TODO: Need paging here
		stacks = client_cfn.list_stacks()
		logging.error("4-Found %s the stacks in Account: %s in Region: %s",
					  len(stacks),
					  ocredentials['AccessKeyId'],
					  fRegion)
		return (stacks['StackSummaries'])
	elif fStackFragment.lower() == 'all' and fStatus.lower() == 'active':
		# Send back all stacks regardless of fragment, check the status further down.
		# TODO: Need paging here
		stacks = client_cfn.list_stacks(StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE",
														   "UPDATE_ROLLBACK_COMPLETE"])
		for stack in stacks['StackSummaries']:
			logging.error("2-Found stack %s in Account: %s in Region: %s with Fragment: %s and Status: %s",
						  stack['StackName'],
						  ocredentials['AccountNumber'],
						  fRegion,
						  fStackFragment,
						  fStatus)
			stacksCopy.append(stack)  # logging.warning("StackStatus: %s | My status: %s", stack['StackStatus'], fStatus)
	elif not fStatus.lower() == 'active':
		# Send back stacks that match the single status, check the fragment further down.
		try:
			logging.warning("Looking for Status: %s", fStatus)
			# TODO: Need paging here
			stacks = client_cfn.list_stacks(StackStatusFilter=[fStatus])
		except Exception as e:
			print(e)
		if 'StackSummaries' in stacks.keys():
			for stack in stacks['StackSummaries']:
				if fStackFragment in stack['StackName'] and fStatus in stack['StackStatus']:
					# Check the fragment now - only send back those that match
					logging.error("5-Found stack %s in Account: %s in Region: %s with Fragment: %s and Status: %s",
								  stack['StackName'],
								  ocredentials['AccountNumber'],
								  fRegion,
								  fStackFragment,
								  fStatus)
					stacksCopy.append(stack)
	return (stacksCopy)


def find_saml_components_in_acct(ocredentials, fRegion):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the AccountId

	fRegion is a string
	"""
	import boto3
	import logging
	logging.error("Acct ID #: %s | Region: %s ", str(ocredentials['AccountNumber']), fRegion)
	session_aws = boto3.Session(region_name=fRegion, aws_access_key_id=ocredentials[
		'AccessKeyId'], aws_secret_access_key=ocredentials['SecretAccessKey'], aws_session_token=ocredentials[
		'SessionToken'])
	iam_info = session_aws.client('iam')
	saml_providers = iam_info.list_saml_providers()['SAMLProviderList']
	return (saml_providers)


def find_stacksets(ocredentials, fRegion, fStackFragment=None, fstatus=None):
	"""
	credentials is a dictionary containing the credentials for a given account
	fRegion is a string
	fStackFragment is a list

	Returns a list that looks like this:
	[
	{'DriftStatus': 'NOT_CHECKED',
	 'StackSetId': 'AWS-Landing-Zone-GuardDutyMaster:48ce0116-2d67-45e2-9141-6c0bfd555363',
	 'StackSetName': 'AWS-Landing-Zone-GuardDutyMaster',
	 'Status': 'ACTIVE'
	},
	{'DriftStatus': 'NOT_CHECKED',
	 'StackSetId': 'AWS-Landing-Zone-GuardDutyMaster:48ce0116-2d67-45e2-9141-6c0bfd555363',
	 'StackSetName': 'AWS-Landing-Zone-GuardDutyMaster',
	 'Status': 'ACTIVE'
	},
	]
	"""
	import boto3
	import logging

	logging.info(f"Account ID: {ocredentials['AccountId']} | Region: {fRegion} | Fragment: {fStackFragment} | Status: {fstatus}")
	session_aws = boto3.Session(region_name=fRegion,
	                            aws_access_key_id=ocredentials['AccessKeyId'],
	                            aws_secret_access_key=ocredentials['SecretAccessKey'],
	                            aws_session_token=ocredentials['SessionToken'])
	client_cfn = session_aws.client('cloudformation')
	#TODO: Need to enable paging here
	if fstatus is None or fstatus.lower == 'active':
		logging.info(f"Looking for stack sets in account {ocredentials['AccountId']} matching fragment {fStackFragment} with status {fstatus}")
		stacksets = client_cfn.list_stack_sets(Status='ACTIVE')
	elif fstatus.upper() == 'DELETED':
		logging.info(f"Looking for stack sets in account {ocredentials['AccountId']} matching fragment {fStackFragment} with status {fstatus}")
		stacksets = client_cfn.list_stack_sets(Status=fstatus.upper())
	else:
		print("We shouldn't get to this point")
	stacksetsCopy = []
	if 'all' in fStackFragment or 'ALL' in fStackFragment or 'All' in fStackFragment or fStackFragment is None:
		logging.info(f"Found all the stacksets in Account: {ocredentials['AccountNumber']} in Region: {fRegion} with Fragment: {fStackFragment}")
		return (stacksets['Summaries'])
	else:
		for stack in stacksets['Summaries']:
			for stackfrag in fStackFragment:
				if stackfrag in stack['StackSetName']:
					logging.warning(f"Found stackset {stack['StackSetName']} in account: {ocredentials['AccountId']} in Region: {fRegion} with Fragment: {stackfrag}")
					stacksetsCopy.append(stack)
	return (stacksetsCopy)


def find_stacksets2(faws_acct, fRegion='us-east-1', fStackFragment=['all']):
	"""
	faws_acct is a class containing the account information
	fRegion is a string
	fStackFragment is a list of strings
	"""
	import logging
	from urllib3.exceptions import NewConnectionError
	from botocore.exceptions import EndpointConnectionError

	# Logging Settings
	LOGGER = logging.getLogger()
	logging.getLogger("boto3").setLevel(logging.CRITICAL)
	logging.getLogger("botocore").setLevel(logging.CRITICAL)
	logging.getLogger("urllib3").setLevel(logging.CRITICAL)
	# Set Log Level

	result = validate_region(faws_acct, fRegion)
	if not result['Result']:
		return(result['Message'])
	else:
		logging.info(result['Message'])
	logging.info(f"Account: {faws_acct.acct_number} | Region: {fRegion} | Fragment: {fStackFragment}")
	session_aws = faws_acct.session
	client_cfn = session_aws.client('cloudformation', region_name=fRegion)

	try:
		stacksets_prelim = client_cfn.list_stack_sets(Status='ACTIVE')
	except EndpointConnectionError as my_error:
		logging.info(f"Likely that the region passed in wasn't correct. Please check and try again.")
		return("Region Endpoint Failure")
	stacksets = stacksets_prelim['Summaries']
	while 'NextToken' in stacksets_prelim.keys():  # Get all instance names
		stacksets_prelim = client_cfn.list_stack_sets(Status='ACTIVE', NextToken=stacksets_prelim['NextToken'])
		stacksets.extend(stacksets_prelim['Summaries'])

	stacksetsCopy = []
	# Because fStackFragment is a list, I need to write it this way
	if 'all' in fStackFragment or 'ALL' in fStackFragment or 'All' in fStackFragment:
		logging.info(f"Found all the stacksets in account: {faws_acct.acct_number} in Region: {fRegion} with Fragment: {fStackFragment}")
		return (stacksets)
	else:
		for stack in stacksets:
			for fragment in fStackFragment:
				if fragment in stack['StackSetName']:
					logging.warning(f"Found stackset {stack['StackSetName']} in Account: {faws_acct.acct_number} in Region: {fRegion} with Fragment: {fragment}")
					stacksetsCopy.append(stack)
	return (stacksetsCopy)


def delete_stackset(fProfile, fRegion, fStackSetName):
	"""
	fProfile is a string holding the name of the profile you're connecting to:
	fRegion is a string
	fStackSetName is a string
	"""
	import boto3
	import logging

	session_cfn = boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn = session_cfn.client('cloudformation')
	logging.warning("Profile: %s | Region: %s | StackSetName: %s", fProfile, fRegion, fStackSetName)
	response = client_cfn.delete_stack_set(StackSetName=fStackSetName)
	return (response)


def find_stack_instances(fProfile, fRegion, fStackSetName, fStatus='CURRENT'):
	"""
	fProfile is a string
	fRegion is a string
	fStackSetName is a string
	fStatus is a string, but isn't currently used.
	TODO: Decide whether to use fStatus, or not
	"""
	import boto3
	import logging

	logging.warning("Profile: %s | Region: %s | StackSetName: %s", fProfile, fRegion, fStackSetName)
	session_cfn = boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn = session_cfn.client('cloudformation')
	stack_instances = client_cfn.list_stack_instances(StackSetName=fStackSetName)
	stack_instances_list = stack_instances['Summaries']
	while 'NextToken' in stack_instances.keys():  # Get all instance names
		stack_instances = client_cfn.list_stack_instances(StackSetName=fStackSetName,
		                                                  NextToken=stack_instances['NextToken'])
		stack_instances_list.extend(stack_instances['Summaries'])
	return (stack_instances_list)


def find_stack_instances2(faws_acct, fRegion, fStackSetName, fStatus='CURRENT'):
	"""
	faws_acct is a custom class containing the credentials
	fRegion is a string
	fStackSetName is a string
	fStatus is a string, but isn't currently used.
	TODO: Decide whether to use fStatus, or not
	"""
	import boto3
	import logging

	logging.warning(f"Account: {faws_acct.acct_number} | Region: {fRegion} | StackSetName: {fStackSetName}")
	session_cfn = faws_acct.session
	result = validate_region(faws_acct, fRegion)
	if not result['Result']:
		return(result['Message'])
	client_cfn = session_cfn.client('cloudformation', region_name=fRegion)
	stack_instances = client_cfn.list_stack_instances(StackSetName=fStackSetName)
	stack_instances_list = stack_instances['Summaries']
	while 'NextToken' in stack_instances.keys():  # Get all instance names
		stack_instances = client_cfn.list_stack_instances(StackSetName=fStackSetName,
		                                                  NextToken=stack_instances['NextToken'])
		stack_instances_list.extend(stack_instances['Summaries'])
	return (stack_instances_list)


def delete_stack_instances(fProfile, fRegion, lAccounts, lRegions, fStackSetName, fRetainStacks=False, fOperationName="StackDelete"):
	"""
	fProfile is the Root Profile that owns the stackset
	fRegion is the region where the stackset resides
	lAccounts is a list of accounts
	lRegion is a list of regions
	fStackSetName is a string
	fOperationName is a string (to identify the operation)
	"""
	import boto3
	import logging

	logging.warning(f"Deleting {fStackSetName} stackset over {len(lAccounts)} accounts across {len(lRegions)} regions")
	session_cfn = boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn = session_cfn.client('cloudformation')
	response = client_cfn.delete_stack_instances(StackSetName=fStackSetName, Accounts=lAccounts, Regions=lRegions, RetainStacks=fRetainStacks, OperationId=fOperationName)
	return (response)  # There is no response to send back


def delete_stack_instances2(fAccountObject, fRegion, lAccounts, lRegions, fStackSetName, fRetainStacks=False, fOperationName="StackDelete"):
	"""
	fProfile is the Root Profile that owns the stackset
	fRegion is the region where the stackset resides
	lAccounts is a list of accounts
	lRegion is a list of regions
	fStackSetName is a string
	fOperationName is a string (to identify the operation)
	"""
	import logging

	result = validate_region(faws_acct, fRegion)
	if not result['Result']:
		return(result['Message'])
	else:
		logging.info(result['Message'])

	logging.warning(f"Deleting {fStackSetName} stackset over {len(lAccounts)} accounts across {len(lRegions)} regions")
	session_cfn = fAccountObject.session
	client_cfn = session_cfn.client('cloudformation')
	response = client_cfn.delete_stack_instances(StackSetName=fStackSetName,
	                                             Accounts=lAccounts,
	                                             Regions=lRegions,
	                                             RetainStacks=fRetainStacks,
	                                             OperationPreferences={
		                                             'RegionConcurrencyType'     : 'PARALLEL',
		                                             'FailureTolerancePercentage': 100,
		                                             'MaxConcurrentPercentage'   : 100
		                                             },
	                                             OperationId=fOperationName)
	return(response)  # The response will be the Operation ID of the delete operation


def find_sc_products(fProfile, fRegion, fStatus="ERROR", flimit=100):
	"""
	fProfile is the Root Profile that owns the Account we're interrogating
	fRegion is the region we're interrogating
	fStatus is the status of SC products we're looking for. Defaults to "ERROR"
	flimit is the max number of products to find. This is used for debugging, mainly

	Returned list looks like this:
	[
		{
			"Arn": "string",
			"CreatedTime": number,
			"Id": "string",
			"IdempotencyToken": "string",
			"LastRecordId": "string",
			"Name": "string",
			"PhysicalId": "string",
			"ProductId": "string",
			"ProvisioningArtifactId": "string",
			"Status": "string",
			"StatusMessage": "string",
			"Tags": [
				{
					"Key": "string",
					"Value": "string"
				}
			],
			"Type": "string",
			"UserArn": "string",
			"UserArnSession": "string"
		}
	]
	"""
	import boto3

	response2 = []
	session_sc = boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_sc = session_sc.client('servicecatalog')
	if fStatus.lower() == 'all':
		response = client_sc.search_provisioned_products(PageSize=flimit)
		while 'NextPageToken' in response.keys():
			response2.extend(response['ProvisionedProducts'])
			response = client_sc.search_provisioned_products(PageToken=response['NextPageToken'], PageSize=flimit)
	else:  # We filter down to only the statuses asked for
		response = client_sc.search_provisioned_products(PageSize=flimit, Filters={
			'SearchQuery': [f"status:{fStatus}"]})
		while 'NextPageToken' in response.keys():
			response2.extend(response['ProvisionedProducts'])
			response = client_sc.search_provisioned_products(PageSize=flimit, Filters={
				'SearchQuery': [f"status:{fStatus}"]}, PageToken=response['NextPageToken'])
	response2.extend(response['ProvisionedProducts'])
	return (response2)


def find_ssm_parameters(fProfile, fRegion):
	"""
	fProfile is the Root Profile that owns the stackset
	fRegion is the region where the stackset resides

	Return Value is a list that looks like this:
	[
		{
			'Description': 'Contains the Local SNS Topic Arn for Landing Zone',
			'LastModifiedDate': datetime.datetime(2020, 2, 7, 12, 50, 2, 373000, tzinfo = tzlocal()),
			'LastModifiedUser': 'arn:aws:sts::517713657778:assumed-role/AWSCloudFormationStackSetExecutionRole/16b4abdd-1d1f-4aeb-8930-3e65dcef6bab',
			'Name': '/org/member/local_sns_arn',
			'Policies': [],
			'Tier': 'Standard',
			'Type': 'String',
			'Version': 1
		},
	]
	"""
	import boto3
	import logging
	from botocore.exceptions import ClientError
	ERASE_LINE = '\x1b[2K'

	logging.warning("Finding ssm parameters for profile %s in Region %s", fProfile, fRegion)
	session_ssm = boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_ssm = session_ssm.client('ssm')
	response = {}
	response2 = []
	TotalParameters = 0
	try:
		response = client_ssm.describe_parameters(MaxResults=50)
	except ClientError as my_Error:
		print(my_Error)
	TotalParameters = TotalParameters + len(response['Parameters'])
	logging.warning("Found another %s parameters, bringing the total up to %s", len(
		response['Parameters']), TotalParameters)
	for i in range(len(response['Parameters'])):
		response2.append(response['Parameters'][i])
	while 'NextToken' in response.keys():
		response = client_ssm.describe_parameters(MaxResults=50, NextToken=response['NextToken'])
		TotalParameters = TotalParameters + len(response['Parameters'])
		logging.warning("Found another %s parameters, bringing the total up to %s", len(
			response['Parameters']), TotalParameters)
		for i in range(len(response['Parameters'])):
			response2.append(response['Parameters'][i])
		if (len(response2) % 500 == 0) and (logging.getLogger().getEffectiveLevel() > 30):
			print(ERASE_LINE, "Sorry this is taking a while - we've already found {} parameters!".format(len(response2)), end="\r")

	print()
	logging.error("Found %s parameters", len(response2))
	return (response2)
