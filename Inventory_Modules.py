
def get_regions(fkey, fprofile="default"):
	import boto3, logging
	session_ec2=boto3.Session(profile_name=fprofile)
	region_info=session_ec2.client('ec2')
	regions=region_info.describe_regions()
	RegionNames=[]
	for x in range(len(regions['Regions'])):
		RegionNames.append(regions['Regions'][x]['RegionName'])
	if "all" in fkey or "ALL" in fkey:
		return(RegionNames)
	RegionNames2=[]
	for x in fkey:
		for y in RegionNames:
			logging.info('Have %s | Looking for %s', y, x)
			if y.find(x) >=0:
				logging.info('Found %s', y)
				RegionNames2.append(y)
	return(RegionNames2)


def get_ec2_regions(fkey, fprofile="default"):
	import boto3, logging
	session_ec2=boto3.Session(profile_name=fprofile)
	region_info=session_ec2.client('ec2')
	regions=region_info.describe_regions(
		Filters=[{
			'Name': 'opt-in-status',
			'Values': ['opt-in-not-required', 'opted-in']
		}]
	)
	RegionNames=[]
	for x in range(len(regions['Regions'])):
		RegionNames.append(regions['Regions'][x]['RegionName'])
	if "all" in fkey or "ALL" in fkey:
		return(RegionNames)
	RegionNames2=[]
	for x in fkey:
		for y in RegionNames:
			logging.info('Have %s | Looking for %s', y, x)
			if y.find(x) >=0:
				logging.info('Found %s', y)
				RegionNames2.append(y)
	return(RegionNames2)


def get_service_regions(service, fkey):
	"""
	Parameters:
		service=the AWS service we're trying to get regions for. This is useful since not all services are supported in all regions.
		fkey=A string fragment of what region we're looking for. If 'all', then we send back all regions for that service. If they send "us-" (for example), we would send back only those regions which matched that fragment. This is good for focusing a search on only those regions you're searching within.
	"""
	import boto3, logging
	s=boto3.Session()
	regions=s.get_available_regions(service, partition_name='aws', allow_non_regional=False)
	if "all" in fkey or "ALL" in fkey:
		return(regions)
	RegionNames=[]
	for x in fkey:
		for y in regions:
			logging.info('Have %s | Looking for %s', y, x)
			if y.find(x) >=0:
				logging.info('Found %s', y)
				RegionNames.append(y)
	return(RegionNames)

"""	# This function is still a work in progress...
def get_valid_service_regions(service, fkey, bValidate=False):
"""
"""
	Parameters:
		service=the AWS service we're trying to get regions for. This is useful since not all services are supported in all regions.
		fkey=A string fragment of what region we're looking for. If 'all', then we send back all regions for that service. If they send "us-" (for example), we would send back only those regions which matched that fragment. This is good for focusing a search on only those regions you're searching within.
		bValidate=this is a Boolean that will determine whether we validate the regions before we send them back.
"""
"""
	import boto3, pprint, logging
	# session=boto3.Session.get_available_regions(service)
	# region_info=session.client(service)
	s=boto3.Session()
	regions=s.get_available_regions(service, partition_name='aws', allow_non_regional=False)
	RegionNames=[]
	for x in range(len(regions)):
		try:
			account_credentials=client_sts.assume_role(
				RoleArn=role_arn, 	# What role_arn can we rely on to be available to us in EVERY account?
				RoleSessionName="Region_Validating")['Credentials']
			logging.info("STS works in region {}".format(region))
			RegionNames.append(regions[x])
		except Exception as e:
			if e.response['Error']['Code'] == 'InvalidClientTokenId':
				logging.error("You probably haven't enabled region %s", regions[x])
	if "all" in fkey or "ALL" in fkey:
		return(RegionNames)
	for x in fkey:
		for y in regions:
			logging.info('Have %s | Looking for %s', y, x)
			if y.find(x) >=0:
				logging.info('Found %s', y)
				RegionNames.append(y)
	return(RegionNames)
"""


def get_profiles(fSkipProfiles=None, fprofiles=None):
	'''
	We assume that the user of this function wants all profiles.
	If they provide a list of profile strings (in fprofiles), then we compare those strings to the full list of profiles we have, and return those profiles that contain the strings they sent.
	'''
	import boto3
	import logging

	if fSkipProfiles==None:
		fSkipProfiles=['default']
	if fprofiles==None:
		fprofiles=['all']
	my_Session=boto3.Session()
	my_profiles=my_Session._session.available_profiles
	if "all" in fprofiles or "ALL" in fprofiles:
		return(my_profiles)
	ProfileList=[]
	for x in fprofiles:
		for y in my_profiles:
			logging.info('Have %s| Looking for %s', y, x)
			if y.find(x) >= 0:
				logging.info('Found profile %s', y)
				ProfileList.append(y)
	return(ProfileList)


def get_profiles2(fSkipProfiles=None, fprofiles=None):
	'''
	We assume that the user of this function wants all profiles.
	If they provide a list of profile strings (in fprofiles), then we compare those strings to the full list of profiles we have, and return those profiles that contain the strings they sent.
	'''
	import boto3

	if fSkipProfiles==None:
		fSkipProfiles=['default']
	if fprofiles==None:
		fprofiles=['all']
	my_Session=boto3.Session()
	my_profiles=my_Session._session.available_profiles
	if "all" in fprofiles or "ALL" in fprofiles:
		my_profiles=list(set(my_profiles)-set(fSkipProfiles))
	else:
		my_profiles=list(set(fprofiles)-set(fSkipProfiles))
	return(my_profiles)


def get_parent_profiles(fprofiles=None, fSkipProfiles=None):
	'''
	This function should only return profiles from Master Payer Accounts.
	If they provide a list of profile strings (in fprofiles), then we compare those
	strings to the full list of profiles we have, and return those profiles that
	contain the strings AND are Master Payer Accounts.
	'''
	import boto3, logging
	from botocore.exceptions import ClientError

	ERASE_LINE='\x1b[2K'
	if fSkipProfiles==None:
		fSkipProfiles=['default']
	if fprofiles==None:
		fprofiles=['all']
	my_Session=boto3.Session()
	my_profiles=my_Session._session.available_profiles
	logging.info("Profile string sent: %s", fprofiles)
	if "all" in fprofiles or "ALL" in fprofiles or "All" in fprofiles:
		my_profiles=list(set(my_profiles)-set(fSkipProfiles))
		logging.info("my_profiles %s:", my_profiles)
	else:
		my_profiles=list(set(fprofiles)-set(fSkipProfiles))
	my_profiles2=[]
	NumOfProfiles=len(my_profiles)
	for profile in my_profiles:
		print(ERASE_LINE, "Checking {} Profile - {} more profiles to go".format(profile, NumOfProfiles), end='\r')
		logging.warning("Finding whether %s is a root profile", profile)
		try:
			AcctResult=find_if_org_root(profile)
		except ClientError as my_Error:
			print(my_Error)
			continue
		NumOfProfiles-=1
		if AcctResult in ['Root', 'StandAlone']:
			logging.warning("%s is a %s Profile", profile, AcctResult)
			my_profiles2.append(profile)
		else:
			logging.warning("%s is a %s Profile", profile, AcctResult)
	return(my_profiles2)


def find_if_org_root(fProfile):

	import logging

	logging.info("Finding if %s is an ORG root", fProfile)
	org_acct_number=find_org_attr(fProfile)
	logging.info("Profile %s's Org Account Number is %s", fProfile, org_acct_number['MasterAccountId'])
	acct_number=find_account_number(fProfile)
	if org_acct_number['MasterAccountId']==acct_number:
		logging.info("%s is a Root account", fProfile)
		return('Root')
	elif org_acct_number['MasterAccountId']=='StandAlone':
		logging.info("%s is a Standalone account", fProfile)
		return('StandAlone')
	else:
		logging.info("%s is a Child account", fProfile)
		return('Child')


def find_if_alz(fProfile):
	import boto3

	session_org=boto3.Session(profile_name=fProfile)
	client_org=session_org.client('s3')
	bucket_list=client_org.list_buckets()
	response={}
	response['BucketName'] = None
	response['ALZ'] = False
	for bucket in bucket_list['Buckets']:
		if "aws-landing-zone-configuration" in bucket['Name']:
				response['BucketName'] = bucket['Name']
				response['ALZ'] = True
				response['Region'] = find_bucket_location(fProfile,bucket['Name'])
	return(response)


def find_bucket_location(fProfile, fBucketname):
	import boto3
	import logging
	from botocore.exceptions import ClientError

	session_org=boto3.Session(profile_name=fProfile)
	client_org=session_org.client('s3')
	try:
		response=client_org.get_bucket_location(
			Bucket=fBucketname
		)
	except ClientError as my_Error:
		if str(my_Error).find("AccessDenied") > 0:
			logging.error("Authorization Failure for profile {}".format(fProfile))
		return(None)
	if response['LocationConstraint'] is None:
		location='us-east-1'
	else:
		location=response['LocationConstraint']
	return(location)


def find_acct_email(fOrgRootProfile, fAccountId):
	import boto3
	"""
	This function *unfortunately* only works with organization accounts.
	"""

	session_org=boto3.Session(profile_name=fOrgRootProfile)
	client_org=session_org.client('organizations')
	email_addr=client_org.describe_account(AccountId=fAccountId)['Account']['Email']
	# email_addr=response['Account']['Email']
	return (email_addr)


def find_account_number(fProfile):
	import boto3, logging
	from botocore.exceptions import ClientError, CredentialRetrievalError, InvalidConfigError

	response='123456789012'
	try:
		session_sts=boto3.Session(profile_name=fProfile)
		logging.info("Looking for profile %s", fProfile)
		client_sts=session_sts.client('sts')
		response=client_sts.get_caller_identity()['Account']
	except ClientError as my_Error:
		if str(my_Error).find("UnrecognizedClientException") > 0:
			print("{}: Security Issue".format(fProfile))
		elif str(my_Error).find("InvalidClientTokenId") > 0:
			print("{}: Security Token is bad - probably a bad entry in config".format(fProfile))
			pass
	except CredentialRetrievalError as my_Error:
		if str(my_Error).find("CredentialRetrievalError") > 0:
			print("{}: Some custom process isn't working".format(fProfile))
			pass
	except InvalidConfigError as my_Error:
		if str(my_Error).find("InvalidConfigError") > 0:
			print("{}: profile is invalid. Probably due to a config profile based on a credential that doesn't work".format(fProfile))
			pass
	except:
		print("Other kind of failure for profile {}".format(fProfile))
		# print(my_Error)
		pass
	return(response)


def find_calling_identity(fProfile):
	import boto3, logging
	from botocore.exceptions import ClientError

	try:
		session_sts=boto3.Session(profile_name=fProfile)
		logging.info("Getting creds used within profile %s", fProfile)
		client_sts=session_sts.client('sts')
		response=client_sts.get_caller_identity()
		creds={}
		creds['Arn']=response['Arn']
		creds['AccountId']=response['Account']
		creds['Short']=response['Arn'][response['Arn'].rfind(':')+1:]
	except ClientError as my_Error:
		if str(my_Error).find("UnrecognizedClientException") > 0:
			print("{}: Security Issue".format(fProfile))
		elif str(my_Error).find("InvalidClientTokenId") > 0:
			print("{}: Security Token is bad - probably a bad entry in config".format(fProfile))
		else:
			print("Other kind of failure for profile {}".format(fProfile))
			print(my_Error)
		creds="Failure"
	return (creds)


def find_org_attr(fProfile):
	import boto3, logging
	from botocore.exceptions import ClientError, CredentialRetrievalError
	"""
	Response is a dict that looks like this:
	{
		'Id': 'o-zzzzzzzzzz',
		'Arn': 'arn:aws:organizations::123456789012:organization/o-zzzzzzzzzz',
		'FeatureSet': 'ALL',
		'MasterAccountArn': 'arn:aws:organizations::123456789012:account/o-zzzzzzzzzz/123456789012',
		'MasterAccountId': '123456789012',
		'MasterAccountEmail': 'xxxxx@yyyy.com',
		'AvailablePolicyTypes': [
			{
				'Type': 'SERVICE_CONTROL_POLICY',
				'Status': 'ENABLED'
			}
		]
	}

	"""
	session_org=boto3.Session(profile_name=fProfile)
	client_org=session_org.client('organizations')
	Success=False
	FailResponse={'MasterAccountId': 'StandAlone', 'Id': 'None'}
	try:
		response=client_org.describe_organization()['Organization']
		Success=True
	except ClientError as my_Error:
		if str(my_Error).find("UnrecognizedClientException") > 0:
			print(fProfile+": Security Issue")
		elif str(my_Error).find("AWSOrganizationsNotInUseException") > 0:
			logging.warning("%s: Account isn't a part of an Organization", fProfile)	# Stand-alone account
			# Need to figure out how to provide the account's own number here as MasterAccountId
		elif str(my_Error).find("InvalidClientTokenId") > 0:
			print(fProfile+": Security Token is bad - probably a bad entry in config")
		pass
	except CredentialRetrievalError as my_Error:
		print(fProfile+": Other kind of failure")
		print(my_Error)
		pass
	except:
		print("Other kind of failure")
		pass
	if Success:
		return (response)
	else:
		return (FailResponse)

def find_org_attr2(fProfile):
	import boto3
	# Unused... and renamed
	session_org=boto3.Session(profile_name=fProfile)
	client_org=session_org.client('organizations')
	response=client_org.describe_organization()
	root_org=response['Organization']['MasterAccountId']
	org_id=response['Organization']['Id']
	return (root_org, org_id)


def find_child_accounts2(fProfile):
	"""
	This is an example of the list response from this call:
		[{'ParentProfile':'LZRoot', 'AccountId': 'xxxxxxxxxxxx', 'AccountEmail': 'EmailAddr1@example.com'},
		 {'ParentProfile':'LZRoot', 'AccountId': 'yyyyyyyyyyyy', 'AccountEmail': 'EmailAddr2@example.com'},
		 {'ParentProfile':'LZRoot', 'AccountId': 'zzzzzzzzzzzz', 'AccountEmail': 'EmailAddr3@example.com'}]
	This can be convenient for appending and removing.
	"""
	import boto3, logging
	from botocore.exceptions import ClientError
	# Renamed since I'm using the one below instead.
	child_accounts=[]
	session_org=boto3.Session(profile_name=fProfile)
	client_org=session_org.client('organizations')
	try:
		response=client_org.list_accounts()
	except ClientError as my_Error:
		logging.warning("Profile %s doesn't represent an Org Root account", fProfile)
		return()
	theresmore=True
	while theresmore:
		for account in response['Accounts']:
			logging.warning("Account ID: %s | Account Email: %s" % (account['Id'], account['Email']))
			child_accounts.append({
				'ParentProfile': fProfile,
				'AccountId': account['Id'],
				'AccountEmail': account['Email'],
				'AccountStatus': account['Status']
			})
		if 'NextToken' in response:
			theresmore=True
			response=client_org.list_accounts(NextToken=response['NextToken'])
		else:
			theresmore=False
	return (child_accounts)


def find_child_accounts(fProfile="default"):
	"""
	This call returns a dictionary response, unlike the "find_child_accounts2" function (above) which returns a list.
	Our dictionary call looks like this:
		{'xxxxxxxxxxxx': 'EmailAddr1@example.com',
		 'yyyyyyyyyyyy': 'EmailAddr2@example.com',
		 'zzzzzzzzzzzz': 'EmailAddr3@example.com'}
	This is convenient because it is easily sortable.
	"""
	import boto3, logging
	from botocore.exceptions import ClientError

	child_accounts={}
	session_org=boto3.Session(profile_name=fProfile)
	theresmore=False
	try:
		client_org=session_org.client('organizations')
		response=client_org.list_accounts()
		theresmore=True
	except ClientError as my_Error:
		logging.warning("Profile %s doesn't represent an Org Root account", fProfile)
		return()
	while theresmore:
		for account in response['Accounts']:
			# Create a key/value pair with the AccountID:AccountEmail
			child_accounts[account['Id']]=account['Email']
		if 'NextToken' in response:
			theresmore=True
			response=client_org.list_accounts(NextToken=response['NextToken'])
		else:
			theresmore=False
	return (child_accounts)


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

	if AccountsToRemove == None:
		AccountsToRemove = []
	NewCA=[]
	for i in range(len(MainList)):
		if MainList[i]['AccountId'] in AccountsToRemove:
			logging.info("Comparing %s to above", str(MainList[i]['AccountId']))
			continue
		else:
			logging.info("Account %s was allowed", str(MainList[i]['AccountId']))
			NewCA.append(MainList[i])
	return(NewCA)


# def get_child_access(fRootProfile, fRegion, fChildAccount, fRoleList=None):
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
# 	sts_session=boto3.Session(profile_name=fRootProfile)
# 	sts_client=sts_session.client('sts', region_name=fRegion)
# 	for role in fRoleList:
# 		try:
# 			role_arn='arn:aws:iam::'+fChildAccount+':role/'+role
# 			account_credentials=sts_client.assume_role(
# 				RoleArn=role_arn,
# 				RoleSessionName="Find-ChildAccount-Things")['Credentials']
# 			session_aws=boto3.Session(
# 				aws_access_key_id=account_credentials['AccessKeyId'],
# 				aws_secret_access_key=account_credentials['SecretAccessKey'],
# 				aws_session_token=account_credentials['SessionToken'],
# 				region_name=fRegion)
# 			return(session_aws)
# 		except ClientError as my_Error:
# 			if my_Error.response['Error']['Code'] == 'ClientError':
# 				logging.info(my_Error)
# 			return_string="{} failed. Try Again".format(str(fRoleList))
# 			continue
# 	return(return_string)


def get_child_access2(fRootProfile, fChildAccount, fRegion='us-east-1',  fRoleList=None):
	"""
	- fRootProfile is a string
	- fChildAccount expects an AWS account number (ostensibly of a Child Account)
	- rRegion expects a string representing one of the AWS regions ('us-east-1', 'eu-west-1', etc.)
	- fRoleList expects a list of roles to try, but defaults to a list of typical roles, in case you don't provide

	The first response object is a dict with account_credentials to pass onto other functions
	The second response object is the rolename that worked to gain access to the target account
	"""
	import boto3
	import logging
	from botocore.exceptions import ClientError

	if fRoleList == None:
		fRoleList = ['AWSCloudFormationStackSetExecutionRole', 'AWSControlTowerExecution', 'OrganizationAccountAccessRole',
	             'AdministratorAccess', 'Owner']
	if not isinstance(fChildAccount, str):  # Make sure the passed in account number is a string
		fChildAccount=str(fChildAccount)
	sts_session=boto3.Session(profile_name=fRootProfile)
	sts_client=sts_session.client('sts', region_name=fRegion)
	account_credentials = {'Profile': None,
	                       'AccessKeyId': None,
	                       'SecretAccessKey': None,
	                       'SessionToken': None,
	                       'AccountNumber': None}
	for role in fRoleList:
		try:
			logging.info("Trying to access account %s using %s profile assuming role: %s", fChildAccount, fRootProfile, role)
			role_arn='arn:aws:iam::'+fChildAccount+':role/'+role
			account_credentials=sts_client.assume_role(
				RoleArn=role_arn,
				RoleSessionName="Find-ChildAccount-Things")['Credentials']
			return(account_credentials, role)
		except ClientError as my_Error:
			if my_Error.response['Error']['Code'] == 'ClientError':
				logging.info(my_Error)
			return_string="{} failed. Try Again".format(str(fRoleList))
			continue
	# Returns a dict object since that's what's expected
	# It will only get to the part below if the child isn't accessed properly using the roles already defined
	return(account_credentials, return_string)


def find_if_Isengard_registered(ocredentials):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
	"""
	import boto3, logging
	logging.warning("Key ID #: %s ", str(ocredentials['AccessKeyId']))
	session_iam=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)
	iam_info=session_iam.client('iam')
	roles=iam_info.list_roles()['Roles']
	for y in range(len(roles)):
		if roles[y]['RoleName']=='IsengardRole-DO-NOT-DELETE':
			return(True)
	return(False)


def enable_drift_on_stacks(ocredentials, fRegion, fStackName):
	import boto3, logging

	session_cfn=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_cfn=session_cfn.client('cloudformation')
	logging.warning("Enabling drift detection on Stack %s in Account %s in region %s", fStackName, ocredentials['AccountNumber'], fRegion)
	response=client_cfn.detect_stack_drift(
		StackName=fStackName
	)

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
	if fTopicFrag == None:
		fTopicFrag = ['all']
	session_sns=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_sns=session_sns.client('sns')
	#TODO: Enable pagination
	response=client_sns.list_topics()
	TopicList=[]
	for item in response['Topics']:
		TopicList.append(item['TopicArn'])
	if 'all' in fTopicFrag:
		logging.warning("Looking for all SNS Topics in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
		logging.info("Topic Arns Returned: %s", TopicList)
		logging.warning("We found %s SNS Topics", len(TopicList))
		return(TopicList)
	else:
		logging.warning("Looking for specific SNS Topics in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
		TopicList2=[]
		for item in fTopicFrag:
			for Topic in TopicList:
				logging.info('Have %s | Looking for %s', Topic, item)
				if Topic.find(item) >=0:
					logging.error('Found %s', Topic)
					TopicList2.append(Topic)
		logging.warning("We found %s SNS Topics", len(TopicList2))
		return(TopicList2)


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

	if fRoleNameFrag==None:
		fRoleNameFrag=['all']
	session_iam=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_iam=session_iam.client('iam')
	#TODO: Enable pagination
	response=client_iam.list_roles()['Roles']
	RoleNameList=[]
	for item in response:
		RoleNameList.append(item['RoleName'])
	if 'all' in fRoleNameFrag:
		logging.warning("Looking for all RoleNames in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
		logging.info("RoleName Arns Returned: %s", RoleNameList)
		logging.warning("We found %s RoleNames", len(RoleNameList))
		return(RoleNameList)
	else:
		logging.warning("Looking for specific RoleNames in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
		RoleNameList2=[]
		for item in fRoleNameFrag:
			for RoleName in RoleNameList:
				logging.info('Have %s | Looking for %s', RoleName, item)
				if RoleName.find(item) >=0:
					logging.error('Found %s', RoleName)
					RoleNameList2.append(RoleName)
		logging.warning("We found %s Roles", len(RoleNameList2))
		return(RoleNameList2)

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

	if fCWLogGroupFrag==None:
		fCWLogGroupFrag=['all']
	session_cw=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_cw=session_cw.client('logs')
	# TODO: Enable pagination # Defaults to 50
	CWLogGroupList=[]
	FirstTime=True
	response={}
	while 'nextToken' in response.keys() or FirstTime:
		FirstTime=False
		response = client_cw.describe_log_groups()
		for item in response['logGroups']:
			CWLogGroupList.append(item['logGroupName'])
	if 'all' in fCWLogGroupFrag:
		logging.warning("Looking for all Log Group names in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
		logging.info("Log Group Names Returned: %s", CWLogGroupList)
		logging.warning("We found %s Log Group names", len(CWLogGroupList))
		return(CWLogGroupList)
	else:
		logging.warning("Looking for specific Log Group names in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
		CWLogGroupList2=[]
		for item in fCWLogGroupFrag:
			for logGroupName in CWLogGroupList:
				logging.info('Have %s | Looking for %s', logGroupName, item)
				if logGroupName.find(item) >=0:
					logging.error('Found %s', logGroupName)
					CWLogGroupList2.append(logGroupName)
		logging.warning("We found %s Log Groups", len(CWLogGroupList2))
		return(CWLogGroupList2)

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

	session_vpc=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_vpc=session_vpc.client('ec2')
	if defaultOnly:
		logging.warning("Looking for default VPCs in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
		logging.info("defaultOnly: %s", str(defaultOnly))
		response=client_vpc.describe_vpcs(
			Filters=[
			{
				'Name': 'isDefault',
				'Values': ['true']
			} ]
		)
	else:
		logging.warning("Looking for all VPCs in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
		logging.info("defaultOnly: %s", str(defaultOnly))
		response=client_vpc.describe_vpcs()
	#TODO: Enable pagination
	logging.warning("We found %s VPCs", len(response['Vpcs']))
	return(response)


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
	session_cfg=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_cfg=session_cfg.client('config')
	logging.warning("Looking for Config Recorders in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
	response=client_cfg.describe_configuration_recorders()
	# logging.info(response)
	return(response)


def del_config_recorder(ocredentials, fRegion, fConfig_recorder_name):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	fRegion=region
	fConfig_recorder_name=Config Recorder Name
	"""
	import boto3
	import logging
	session_cfg=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_cfg=session_cfg.client('config')
	logging.error("Deleting Config Recorder %s from Region %s in account %s", fConfig_recorder_name, fRegion, ocredentials['AccountNumber'])
	response=client_cfg.delete_configuration_recorder(ConfigurationRecorderName=fConfig_recorder_name)
	return(response) # There is no response to send back


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
	import boto3, logging
	session_cfg=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_cfg=session_cfg.client('config')
	logging.warning("Looking for Delivery Channels in account %s from Region %s", ocredentials['AccountNumber'], fRegion)

	response=client_cfg.describe_delivery_channels()
	return(response)


def del_delivery_channel(ocredentials, fRegion, fDelivery_channel_name):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	rRegion=region
	fDelivery_channel_name=delivery channel name
	"""
	import boto3, logging
	session_cfg=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_cfg=session_cfg.client('config')
	logging.error("Deleting Delivery Channel %s from Region %s in account %s", fDelivery_channel_name, fRegion, ocredentials['AccountNumber'])
	response=client_cfg.delete_delivery_channels(DeliveryChannelName=fDelivery_channel_name)
	return(response)


def find_cloudtrails(ocredentials, fRegion, fCloudTrailnames=None):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	fRegion=region
	fCloudTrailnames=List of CloudTrail names we're looking for (null value returns all cloud trails)

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
	"""
	import boto3, logging
	from botocore.exceptions import ClientError

	session_ct=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_ct=session_ct.client('cloudtrail')
	logging.info("Looking for CloudTrail trails in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
	if fCloudTrailnames == None:    # Therefore - they're really looking for a list of trails
		try:
			response=client_ct.list_trails()
			trailname = "Various"
			fullresponse = response['Trails']
			if 'NextToken' in response.keys():
				while 'NextToken' in response.keys():
					response=client_ct.list_trails()
					for i in range(len(response['Trails'])):
						fullresponse.append(response['Trails'][i])
		except ClientError as my_Error:
			if str(my_Error).find("InvalidTrailNameException") > 0:
				logging.error("Bad CloudTrail name provided")
			fullresponse=trailname+" didn't work. Try Again"
		return(fullresponse, trailname)
	else:
		#  TODO: This doesn't work... Needs to be fixed.
		for trailname in fCloudTrailnames:  # They've provided a list of trails and want specific info about them
			try:
				response=client_ct.describe_trails(trailNameList=[trailname])
				if len(response['trailList']) > 0:
					return(response, trailname)
			except ClientError as my_Error:
				if str(my_Error).find("InvalidTrailNameException") > 0:
					logging.error("Bad CloudTrail name provided")
				response=trailname+" didn't work. Try Again"
		return(response, trailname)


def del_cloudtrails(ocredentials, fRegion, fCloudTrail):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	fRegion=region
	fCloudTrail=CloudTrail we're deleting
	"""
	import boto3, logging
	session_ct=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_ct=session_ct.client('cloudtrail')
	logging.info("Deleting CloudTrail %s in account %s from Region %s", fCloudTrail, ocredentials['AccountNumber'], fRegion)
	response=client_ct.delete_trail(Name=fCloudTrail)
	return(response)


def find_gd_invites(ocredentials, fRegion):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	fRegion=region
	"""
	import boto3, logging
	from botocore.exceptions import ClientError

	session_gd=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_gd=session_gd.client('guardduty')
	logging.info("Looking for GuardDuty invitations in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
	try:
		response=client_gd.list_invitations()
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(ocredentials['AccountNumber']+": Authorization Failure for account {}".format(ocredentials['AccountNumber']))
		if str(my_Error).find("security token included in the request is invalid") > 0:
			print("Account #:"+ocredentials['AccountNumber']+" - It's likely that the region you're trying ({}) isn\'t enabled for your account".format(fRegion))
		else:
			print(my_Error)
		response={'Invitations': []}
	return(response)


def delete_gd_invites(ocredentials, fRegion, fAccountId):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
	fRegion=region
	"""
	import boto3, logging
	from botocore.exceptions import ClientError

	session_gd=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken'],
		region_name=fRegion)
	client_gd=session_gd.client('guardduty')
	logging.info("Looking for GuardDuty invitations in account %s from Region %s", ocredentials['AccountNumber'], fRegion)
	try:
		response=client_gd.delete_invitations(
			AccountIds=[fAccountId]
		)
	except ClientError as my_Error:
		if str(my_Error).find("AuthFailure") > 0:
			print(ocredentials['AccountNumber']+": Authorization Failure for account {}".format(ocredentials['AccountNumber']))
		if str(my_Error).find("security token included in the request is invalid") > 0:
			print("Account #:"+ocredentials['AccountNumber']+" - It's likely that the region you're trying ({}) isn\'t enabled for your account".format(fRegion))
		else:
			print(my_Error)
	return(response['Invitations'])


def find_account_instances(ocredentials, fRegion):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the account number
		- ['Profile'] can hold the profile, instead of the session credentials
	"""
	import boto3, logging
	if ocredentials['Profile'] is None:
		session_ec2=boto3.Session(
			aws_access_key_id=ocredentials['AccessKeyId'],
			aws_secret_access_key=ocredentials['SecretAccessKey'],
			aws_session_token=ocredentials['SessionToken'],
			region_name=fRegion)
	else:
		session_ec2=boto3.Session(profile_name=ocredentials['Profile'], region_name=fRegion)
	instance_info=session_ec2.client('ec2')
	logging.warning("Looking in account # %s in region %s", ocredentials['AccountNumber'], fRegion)
	instances=instance_info.describe_instances()
	# TODO: Consider pagination here
	return(instances)


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
	session_iam=boto3.Session(
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)
	user_info=session_iam.client('iam')
	users=user_info.list_users()['Users']
	# TODO: Consider pagination here
	return(users)


def find_profile_vpcs(fProfile, fRegion, fDefaultOnly):

	import boto3

	session_ec2=boto3.Session(profile_name=fProfile, region_name=fRegion)
	vpc_info=session_ec2.client('ec2')
	if fDefaultOnly:
		vpcs=vpc_info.describe_vpcs(Filters=[{
			'Name': 'isDefault',
			'Values': ['true']
		}])
	else:
		vpcs=vpc_info.describe_vpcs()
	# if len(vpcs['Vpcs']) == 1 and vpcs['Vpcs'][0]['IsDefault'] == True and not ('Tags' in vpcs['Vpcs'][0]):
	# 	return()
	# else:
	return(vpcs)

#
# def find_gd_detectors(fProfile, fRegion):
# 	import boto3
#
# 	session=boto3.Session(profile_name=fProfile, region_name=fRegion)
# 	object_info=session.client('guardduty')
# 	object=object_info.list_detectors()
# 	return(object)
# 	# return(vpcs)
#
#
# def del_gd_detectors(fProfile, fRegion, fDetectorId):
# 	import boto3
#
# 	session=boto3.Session(profile_name=fProfile, region_name=fRegion)
# 	object_info=session.client('guardduty')
# 	object=object_info.delete_detector(DetectorId=fDetectorId)
# 	return(object)


def find_profile_functions(fProfile, fRegion):

	import boto3
	session_lambda=boto3.Session(profile_name=fProfile, region_name=fRegion)
	lambda_info=session_lambda.client('lambda')
	functions=lambda_info.list_functions()
	return(functions)


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
	session_lambda=boto3.Session(region_name=fRegion,
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)
	client_lambda=session_lambda.client('lambda')
	functions=client_lambda.list_functions()['Functions']
	functions2=[]
	for i in range(len(functions)):
		for searchitem in fSearchStrings:
			if searchitem in functions[i]['FunctionName']:
				functions2.append({
					'FunctionName' : functions[i]['FunctionName'],
					'FunctionArn' : functions[i]['FunctionArn'],
					'Role' : functions[i]['Role']
				})
	return(functions2)


def get_lambda_code_url(fprofile, fregion, fFunctionName):

	import boto3
	session_lambda=boto3.Session(profile_name=fprofile, region_name=fregion)
	client_lambda=session_lambda.client('lambda')
	code_url=client_lambda.get_function(FunctionName=fFunctionName)['Code']['Location']
	return(code_url)

def find_private_hosted_zones(fProfile, fRegion):

	import boto3
	session_r53=boto3.Session(profile_name=fProfile, region_name=fRegion)
	phz_info=session_r53.client('route53')
	hosted_zones=phz_info.list_hosted_zones()
	return(hosted_zones)

def find_private_hosted_zones2(ocredentials, fRegion):

	import boto3
	session_r53=boto3.Session(region_name=fRegion,
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)
	phz_info=session_r53.client('route53')
	hosted_zones=phz_info.list_hosted_zones()
	return(hosted_zones)


def find_load_balancers(fProfile, fRegion, fStackFragment, fStatus):

	import boto3
	import logging

	logging.warning("Profile: %s | Region: %s | Fragment: %s | Status: %s", fProfile, fRegion, fStackFragment, fStatus)
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	lb_info=session_cfn.client('elbv2')
	load_balancers=lb_info.describe_load_balancers()
	load_balancers_Copy=[]
	if (fStackFragment=='all' or fStackFragment=='ALL') and (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='all' or fStatus=='ALL'):
		logging.warning("Found all the lbs in Profile: %s in Region: %s with Fragment: %s and Status: %s", fProfile, fRegion, fStackFragment, fStatus)
		return(load_balancers['LoadBalancers'])
	elif (fStackFragment=='all' or fStackFragment=='ALL'):
		for load_balancer in load_balancers['LoadBalancers']:
			if fStatus in load_balancer['State']['Code']:
				logging.warning("Found lb %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", load_balancers['LoadBalancerName'], fProfile, fRegion, fStackFragment, fStatus)
				load_balancers_Copy.append(load_balancer)
	elif (fStatus=='active' or fStatus=='ACTIVE'):
		for load_balancer in load_balancers['LoadBalancers']:
			if fStackFragment in load_balancer['LoadBalancerName']:
				logging.warning("Found lb %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", load_balancers['LoadBalancerName'], fProfile, fRegion, fStackFragment, fStatus)
				load_balancers_Copy.append(load_balancer)
	return(load_balancers_Copy)


def find_stacks(fProfile, fRegion, fStackFragment="all", fStatus="active"):
	"""
	fprofile is an string holding the name of the profile you're connecting to:
	fRegion is a string
	fStackFragment is a string
	fStatus is a string

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
			'second':
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
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn=session_cfn.client('cloudformation')
	AllStacks=[]
	response=client_cfn.describe_stacks()
	AllStacks = response['Stacks']
	logging.info("Found %s stacks this time around", len(response['Stacks']))
	while 'NextToken' in response.keys():
		response = client_cfn.describe_stacks()
		AllStacks.append(response['Stacks'])
		logging.info("Found %s stacks this time around", len(response['Stacks']))
	logging.info("Done with loops and found a total of %s stacks", len(AllStacks))
	stacksCopy=[]
	if fStatus.lower()=='active' and not fStackFragment.lower()=='all':
		# Send back stacks that are active, check the fragment further down.
		# stacks=client_cfn.list_stacks(StackStatusFilter=["CREATE_COMPLETE", "DELETE_FAILED", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE", "DELETE_IN_PROGRESS"])
		logging.warning("1 - Found %s stacks. Looking for fragment %s", len(AllStacks), fStackFragment)
		for stack in AllStacks:
			if fStackFragment in stack['StackName']:
				# Check the fragment now - only send back those that match
				logging.warning("Found stack %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], fProfile, fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	elif fStackFragment.lower()=='all' and fStatus.lower()=='active':
		# Send back all stacks regardless of fragment, check the status further down.
		stacks=client_cfn.list_stacks(StackStatusFilter=["CREATE_COMPLETE", "DELETE_FAILED", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"])
		logging.warning("2 - Found ALL %s stacks in 'active' status.", len(stacks['StackSummaries']))
		for stack in stacks['StackSummaries']:
			# if fStatus in stack['StackStatus']:
			# Check the status now - only send back those that match a single status
			# I don't see this happening unless someone wants Stacks in a "Deleted" or "Rollback" type status
			logging.warning("Found stack %s in Profile: %s in Region: %s regardless of fragment and Status: %s", stack['StackName'], fProfile, fRegion, fStatus)
			stacksCopy.append(stack)
	elif fStackFragment.lower()=='all' and fStatus.lower()=='all':
		# Send back all stacks.
		stacks=client_cfn.list_stacks()
		logging.warning("3 - Found ALL %s stacks in ALL statuses", len(stacks['StackSummaries']))
		return(stacks['StackSummaries'])
	elif not fStatus.lower()=='active':
		# Send back stacks that match the single status, check the fragment further down.
		try:
			stacks=client_cfn.list_stacks()
			logging.warning("4 - Found %s stacks ", len(stacks['StackSummaries']))
		except Exception as e:
			print(e)
		for stack in stacks['StackSummaries']:
			# pprint.pprint(stack)
			if fStackFragment in stack['StackName']:
				# Check the fragment now - only send back those that match
				logging.warning("Found stack %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], fProfile, fRegion, fStackFragment, stack['StackStatus'])
				stacksCopy.append(stack)
	return(stacksCopy)


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
	if "RetainResources" in kwargs:
		RetainResources=True
		ResourcesToRetain=kwargs['ResourcesToRetain']
	else:
		RetainResources=False
	session_cfn=boto3.Session(profile_name=fprofile, region_name=fRegion)
	client_cfn=session_cfn.client('cloudformation')
	if RetainResources:
		logging.warning("Profile: %s | Region: %s | StackName: %s", fprofile, fRegion, fStackName)
		logging.warning("	Retaining Resources: %s", ResourcesToRetain)
		response=client_cfn.delete_stack(StackName=fStackName, RetainResources=ResourcesToRetain)
	else:
		logging.warning("Profile: %s | Region: %s | StackName: %s", fprofile, fRegion, fStackName)
		response=client_cfn.delete_stack(StackName=fStackName)
	return(response)


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
	if "RetainResources" in kwargs:
		RetainResources=True
		ResourcesToRetain=kwargs['ResourcesToRetain']
	else:
		RetainResources=False
	session_cfn=boto3.Session(region_name=fRegion,
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)
	client_cfn=session_cfn.client('cloudformation')
	if RetainResources:
		logging.warning("Account: %s | Region: %s | StackName: %s", ocredentials['AccountNumber'], fRegion, fStackName)
		logging.warning("	Retaining Resources: %s", ResourcesToRetain)
		response=client_cfn.delete_stack(StackName=fStackName, RetainResources=ResourcesToRetain)
	else:
		logging.warning("Account: %s | Region: %s | StackName: %s", ocredentials['AccountNumber'], fRegion, fStackName)
		response=client_cfn.delete_stack(StackName=fStackName)
	return(response)


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
	logging.error("Acct ID #: %s | Region: %s | Fragment: %s | Status: %s", str(ocredentials['AccountNumber']), fRegion, fStackFragment, fStatus)
	session_cfn=boto3.Session(region_name=fRegion,
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)
	client_cfn=session_cfn.client('cloudformation')
	stacksCopy=[]
	if fStatus.lower()=='active' and not fStackFragment.lower()=='all':
		# Send back stacks that are active, check the fragment further down.
		stacks=client_cfn.list_stacks(StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"])
		for stack in stacks['StackSummaries']:
			if fStackFragment in stack['StackName']:
				# Check the fragment now - only send back those that match
				logging.error("1-Found stack %s in Account: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], ocredentials['AccountNumber'], fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	elif fStackFragment.lower()=='all' and fStatus.lower()=='all':
		# Send back all stacks.
		stacks=client_cfn.list_stacks()
		logging.error("4-Found %s the stacks in Account: %s in Region: %s", len(stacks), ocredentials['AccessKeyId'], fRegion)
		return(stacks['StackSummaries'])
	elif fStackFragment.lower()=='all' and fStatus.lower()=='active':
		# Send back all stacks regardless of fragment, check the status further down.
		stacks=client_cfn.list_stacks(StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"])
		for stack in stacks['StackSummaries']:
			logging.error("2-Found stack %s in Account: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], ocredentials['AccountNumber'], fRegion, fStackFragment, fStatus)
			stacksCopy.append(stack)
			# logging.warning("StackStatus: %s | My status: %s", stack['StackStatus'], fStatus)
	elif not fStatus.lower()=='active':
		# Send back stacks that match the single status, check the fragment further down.
		try:
			logging.warning("Not looking for active stacks... Looking for Status: %s", fStatus)
			stacks=client_cfn.list_stacks(StackStatusFilter=[fStatus])
		except Exception as e:
			print(e)
		for stack in stacks['StackSummaries']:
			if fStackFragment in stack['StackName'] and fStatus in stack['StackStatus']:
				# Check the fragment now - only send back those that match
				logging.error("5-Found stack %s in Account: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], ocredentials['AccountNumber'], fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	return(stacksCopy)


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
	session_aws=boto3.Session(region_name=fRegion,
		aws_access_key_id=ocredentials['AccessKeyId'],
		aws_secret_access_key=ocredentials['SecretAccessKey'],
		aws_session_token=ocredentials['SessionToken']
	)
	iam_info=session_aws.client('iam')
	saml_providers=iam_info.list_saml_providers()['SAMLProviderList']
	return(saml_providers)


def find_stacksets(fProfile, fRegion, fStackFragment):
	"""
	fProfile is a string
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

	logging.info("Profile: %s | Region: %s | Fragment: %s", fProfile, fRegion, fStackFragment)
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn=session_cfn.client('cloudformation')
	stacksets=client_cfn.list_stack_sets(Status='ACTIVE')
	stacksetsCopy=[]
	# if fStackFragment=='all' or fStackFragment=='ALL':
	if 'all' in fStackFragment or 'ALL' in fStackFragment or 'All' in fStackFragment:
		logging.info("Found all the stacksets in Profile: %s in Region: %s with Fragment: %s", fProfile, fRegion, fStackFragment)
		return(stacksets['Summaries'])
	# elif (fStackFragment=='all' or fStackFragment=='ALL'):
	# 	for stack in stacksets['Summaries']:
	# 		if fStatus in stack['Status']:
	# 			logging.warning("Found stackset %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackSetName'], fProfile, fRegion, fStackFragment, fStatus)
	# 			stacksetsCopy.append(stack)
	else:
		for stack in stacksets['Summaries']:
			for stackfrag in fStackFragment:
				if stackfrag in stack['StackSetName']:
					logging.warning("Found stackset %s in Profile: %s in Region: %s with Fragment: %s", stack['StackSetName'], fProfile, fRegion, stackfrag)
					stacksetsCopy.append(stack)
	return(stacksetsCopy)


def find_stacksets2(facct_creds, fRegion, faccount, fStackFragment=""):
	"""
	facct_creds is an object which contains the credentials for the account
	fRegion is a string
	fStackFragment is a string
	"""
	import boto3
	import logging

	logging.info("Account: %s | Region: %s | Fragment: %s", faccount, fRegion, fStackFragment)
	session_aws=boto3.Session(
		aws_access_key_id=facct_creds['AccessKeyId'],
		aws_secret_access_key=facct_creds['SecretAccessKey'],
		aws_session_token=facct_creds['SessionToken'],
		region_name=fRegion)
	client_cfn=session_aws.client('cloudformation')

	stacksets=client_cfn.list_stack_sets(Status='ACTIVE')
	stacksetsCopy=[]
	# if fStackFragment=='all' or fStackFragment=='ALL':
	if 'all' in fStackFragment or 'ALL' in fStackFragment or 'All' in fStackFragment:
		logging.info("Found all the stacksets in Profile: %s in Region: %s with Fragment: %s", faccount, fRegion, fStackFragment)
		return(stacksets['Summaries'])
	# elif (fStackFragment=='all' or fStackFragment=='ALL'):
	# 	for stack in stacksets['Summaries']:
	# 		if fStatus in stack['Status']:
	# 			logging.warning("Found stackset %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackSetName'], fProfile, fRegion, fStackFragment, fStatus)
	# 			stacksetsCopy.append(stack)
	else:
		for stack in stacksets['Summaries']:
			if fStackFragment in stack['StackSetName']:
				logging.warning("Found stackset %s in Account: %s in Region: %s with Fragment: %s", stack['StackSetName'], faccount, fRegion, fStackFragment)
				stacksetsCopy.append(stack)
	return(stacksetsCopy)


def delete_stackset(fProfile, fRegion, fStackSetName):
	"""
	fProfile is a string holding the name of the profile you're connecting to:
	fRegion is a string
	fStackSetName is a string
	"""
	import boto3
	import logging
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn=session_cfn.client('cloudformation')
	logging.warning("Profile: %s | Region: %s | StackSetName: %s", fProfile, fRegion, fStackSetName)
	response=client_cfn.delete_stack_set(StackSetName=fStackSetName)
	return(response)


def find_stack_instances(fProfile, fRegion, fStackSetName, fStatus='CURRENT'):
	"""
	fProfile is a string
	fRegion is a string
	fStackSetName is a string
	"""
	import boto3
	import logging

	logging.warning("Profile: %s | Region: %s | StackSetName: %s", fProfile, fRegion, fStackSetName)
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn=session_cfn.client('cloudformation')
	stack_instances=client_cfn.list_stack_instances(StackSetName=fStackSetName)
	stack_instances_list=stack_instances['Summaries']
	while 'NextToken' in stack_instances.keys(): # Get all instance names
		stack_instances=client_cfn.list_stack_instances(StackSetName=fStackSetName, NextToken=stack_instances['NextToken'])
		for i in range(len(stack_instances)):
			stack_instances_list.append(stack_instances['Summaries'][i])
	return(stack_instances_list)


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

	logging.warning("Deleting %s stackset over %s accounts across %s regions" % (fStackSetName, len(lAccounts), len(lRegions)))
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn=session_cfn.client('cloudformation')
	response=client_cfn.delete_stack_instances(
		StackSetName=fStackSetName,
		Accounts=lAccounts,
		Regions=lRegions,
		RetainStacks=fRetainStacks,
		OperationId=fOperationName
	)


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

	response2=[]
	session_sc=boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_sc=session_sc.client('servicecatalog')
	if fStatus.lower()=='all':
		response=client_sc.search_provisioned_products(PageSize=flimit)
		while 'NextPageToken' in response.keys():
			response2.extend(response['ProvisionedProducts'])
			response=client_sc.search_provisioned_products(PageToken=response['NextPageToken'],PageSize=flimit)
	else:	# We filter down to only the statuses asked for
		response=client_sc.search_provisioned_products(PageSize=flimit,
			Filters={
				'SearchQuery': ['status:'+fStatus]
			}
		)
		while 'NextPageToken' in response.keys():
			response2.extend(response['ProvisionedProducts'])
			response=client_sc.search_provisioned_products(PageSize=flimit,
				Filters={
					'SearchQuery': ['status:'+fStatus]
				},
				PageToken=response['NextPageToken']
			)
	response2.extend(response['ProvisionedProducts'])
	return(response2)


def find_ssm_parameters(fProfile, fRegion):
	"""
	fProfile is the Root Profile that owns the stackset
	fRegion is the region where the stackset resides

	Return Value is a list that looks like this:
	[
		{
			'Description': 'Contains the Local SNS Topic Arn for Landing Zone',
			'LastModifiedDate': datetime.datetime(2020, 2, 7, 12, 50, 2, 373000, tzinfo=tzlocal()),
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
	ERASE_LINE='\x1b[2K'

	logging.warning("Finding ssm parameters for profile %s in Region %s", fProfile, fRegion)
	session_ssm=boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_ssm=session_ssm.client('ssm')
	response={}
	response2=[]
	TotalParameters=0
	try:
		response=client_ssm.describe_parameters(MaxResults=50)
	except ClientError as my_Error:
		print(my_Error)
	TotalParameters=TotalParameters+len(response['Parameters'])
	logging.warning("Found another %s parameters, bringing the total up to %s", len(response['Parameters']), TotalParameters)
	for i in range(len(response['Parameters'])):
		response2.append(response['Parameters'][i])
	while 'NextToken' in response.keys():
		response=client_ssm.describe_parameters(MaxResults=50, NextToken=response['NextToken'])
		TotalParameters=TotalParameters+len(response['Parameters'])
		logging.warning("Found another %s parameters, bringing the total up to %s", len(response['Parameters']), TotalParameters)
		for i in range(len(response['Parameters'])):
			response2.append(response['Parameters'][i])
		if (len(response2) % 500 == 0) and (logging.getLogger().getEffectiveLevel() > 30):
			print(ERASE_LINE, "Sorry this is taking a while - we've already found {} parameters!".format(len(response2)), end="\r")

	print()
	logging.error("Found %s parameters", len(response2))
	return(response2)
