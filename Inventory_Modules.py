
def get_ec2_regions(fkey):
	import boto3, pprint, logging
	session_ec2=boto3.Session()
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
			logging.info('Have %s | Looking for %s',y,x)
			if y.find(x) >=0:
				logging.info('Found %s',y)
				RegionNames2.append(y)
	return(RegionNames2)

def get_profiles(fSkipProfiles,fprofiles="all"):
	'''
	We assume that the user of this function wants all profiles.
	If they provide a list of profile strings (in fprofiles), then we compare those strings to the full list of profiles we have, and return those profiles that contain the strings they sent.
	'''
	import boto3, logging
	from botocore.exceptions import ClientError

	my_Session=boto3.Session()
	my_profiles=my_Session._session.available_profiles
	if "all" in fprofiles or "ALL" in fprofiles:
		return(my_profiles)
	ProfileList=[]
	for x in fprofiles:
		for y in my_profiles:
			logging.info('Have %s| Looking for %s',y,x)
			if y.find(x) >= 0:
				logging.info('Found profile %s',y)
				ProfileList.append(y)
	return(ProfileList)

def find_profile_instances(fProfile,fRegion):

	import boto3
	session_ec2=boto3.Session(profile_name=fProfile, region_name=fRegion)
	instance_info=session_ec2.client('ec2')
	instances=instance_info.describe_instances()
	return(instances)

def find_if_org_root(fProfile):

	org_acct_number=find_org_attr(fProfile)
	acct_number=find_account_number(fProfile)
	if org_acct_number['Organization']['MasterAccountId']==acct_number:
		return(True)
	else:
		return(False)

def find_if_lz(fProfile):
	import boto3

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('s3')
	response=client_org.list_buckets()
	for bucket in response['Buckets']:
		if "aws-landing-zone-configuration" in bucket['Name']:
				return(True)
	return(False)

def find_acct_email(fOrgRootProfile,fAccountId):
	import boto3

	session_org = boto3.Session(profile_name=fOrgRootProfile)
	client_org = session_org.client('organizations')
	email_addr=client_org.describe_account(AccountId=fAccountId)['Account']['Email']
	# email_addr=response['Account']['Email']
	return (email_addr)

def find_org_attr(fProfile):
	import boto3

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_organization()['Organization']
	return (response)

def find_org_attr2(fProfile):
	import boto3
	## Unused... and renamed
	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_organization()
	root_org=response['Organization']['MasterAccountId']
	org_id=response['Organization']['Id']
	return (root_org,org_id)

def find_child_accounts2(fProfile):
	"""
	This is an example of the list response from this call:
		[{'AccountEmail': 'EmailAddr1@example.com', 'AccountId': 'xxxxxxxxxxxx'},
		 {'AccountEmail': 'EmailAddr2@example.com', 'AccountId': 'yyyyyyyyyyyy'},
		 {'AccountEmail': 'EmailAddr3@example.com', 'AccountId': 'zzzzzzzzzzzz'}]
	This can be convenient for appending and removing.
	"""
	import boto3, logging
	# Renamed since I'm using the one below instead.
	child_accounts=[]
	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.list_accounts()
	theresmore=True
	while theresmore:
		for account in response['Accounts']:
			logging.warning("Account ID: %s | Account Email: %s" % (account['Id'],account['Email']))
			child_accounts.append({
				'AccountId':account['Id'],
				'AccountEmail':account['Email']
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
	from botocore.exceptions import ClientError, NoCredentialsError

	child_accounts={}
	session_org = boto3.Session(profile_name=fProfile)
	theresmore=False
	try:
		client_org = session_org.client('organizations')
		response=client_org.list_accounts()
		theresmore=True
	except ClientError as my_Error:
		logging.warning("Profile %s doesn't represent an Org Root account",fProfile)
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

def find_account_number(fProfile):

	import boto3
	session_sts = boto3.Session(profile_name=fProfile)
	client_sts = session_sts.client('sts')
	response=client_sts.get_caller_identity()['Account']
	return (response)

def RemoveCoreAccounts(MainList,AccountsToRemove):

	import logging, pprint
	"""
	MainList is expected to come through looking like this:
		[{'AccountEmail': 'paulbaye+LZ2@amazon.com', 'AccountId': '911769525492'},
		{'AccountEmail': 'Paulbaye+LZ2Log@amazon.com', 'AccountId': '785529286764'},
			< ... >
		{'AccountEmail': 'paulbaye+LZ2SS@amazon.com', 'AccountId': '728530570730'},
	 	{'AccountEmail': 'paulbaye+Demo2@amazon.com', 'AccountId': '906348505515'}]
	AccountsToRemove is simply a list of accounts you don't want to screw with. It might look like this:
		['911769525492','906348505515']
	"""

	NewCA=[]
	# pprint.pprint(AccountsToRemove)
	for i in range(len(MainList)):
		if MainList[i]['AccountId'] in AccountsToRemove:
			logging.info("Comparing %s to above",str(MainList[i]['AccountId']))
			continue
		else:
			logging.info("Account %s was allowed",str(MainList[i]['AccountId']))
			NewCA.append(MainList[i])
	return(NewCA)

"""
Above - Generic functions
Below - Specific functions to specific features
"""
def find_users(ocredentials):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
	"""
	import boto3, logging, pprint
	logging.warning("Key ID #: %s ",str(ocredentials['AccessKeyId']))
	session_iam=boto3.Session(
				aws_access_key_id = ocredentials['AccessKeyId'],
				aws_secret_access_key = ocredentials['SecretAccessKey'],
				aws_session_token = ocredentials['SessionToken']
				)
	user_info=session_iam.client('iam')
	users=user_info.list_users()['Users']
	return(users)

def find_if_Isengard_registered(ocredentials):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
	"""
	import boto3, logging, pprint
	logging.warning("Key ID #: %s ",str(ocredentials['AccessKeyId']))
	session_iam=boto3.Session(
				aws_access_key_id = ocredentials['AccessKeyId'],
				aws_secret_access_key = ocredentials['SecretAccessKey'],
				aws_session_token = ocredentials['SessionToken']
				)
	iam_info=session_iam.client('iam')
	roles=iam_info.list_roles()['Roles']
	for y in range(len(roles)):
		if roles[y]['RoleName']=='IsengardRole-DO-NOT-DELETE':
			return(True)
	return(False)

def find_if_LZ_Acct(ocredentials):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['ParentAccountNumber'] holds the AWS Account Number
	"""
	import boto3, logging, pprint
	from botocore.exceptions import ClientError

	logging.warning("Key ID #: %s ",str(ocredentials['AccessKeyId']))
	session_aws=boto3.Session(
				aws_access_key_id = ocredentials['AccessKeyId'],
				aws_secret_access_key = ocredentials['SecretAccessKey'],
				aws_session_token = ocredentials['SessionToken']
				)
	iam_info=session_aws.client('iam')
	try:
		roles=iam_info.list_roles()['Roles']
		AccessSuccess=True
	except ClientError as my_Error:
		if str(my_Error).find("AccessDenied") > 0:
			print("Authorization Failure for account {}".format(ocredentials['ParentAccountNumber']))
		AccessSuccess=False
	if AccessSuccess:
		for y in range(len(roles)):
			if roles[y]['RoleName']=='AWSCloudFormationStackSetExecutionRole':
				return(True)
		return(False)
	else:
		return(False)


def find_profile_vpcs(fProfile,fRegion):

	import boto3
	session_ec2=boto3.Session(profile_name=fProfile, region_name=fRegion)
	vpc_info=session_ec2.client('ec2')
	vpcs=vpc_info.describe_vpcs()
	if len(vpcs['Vpcs']) == 1 and vpcs['Vpcs'][0]['IsDefault'] == True and not ('Tags' in vpcs['Vpcs'][0]):
		return()
	else:
		return(vpcs)
	# return(vpcs)

def get_child_access(fRootProfile,fRegion,fChildAccount,fRole='AWSCloudFormationStackSetExecutionRole'):
	import boto3, logging

	session_sts=boto3.Session(profile_name=fRootProfile)
	sts_session = boto3.Session(profile_name=fRootProfile)
	sts_client = sts_session.client('sts',region_name=fRegion)
	role_arn = 'arn:aws:iam::'+fChildAccount+':role/'+fRole
	account_credentials = sts_client.assume_role(
		RoleArn=role_arn,
		RoleSessionName="Find-ChildAccount-Things")['Credentials']
	session_aws=boto3.Session(
		aws_access_key_id=account_credentials['AccessKeyId'],
		aws_secret_access_key=account_credentials['SecretAccessKey'],
		aws_session_token=account_credentials['SessionToken'],
		region_name=fRegion)
	return(session_aws)

def find_gd_detectors(fProfile,fRegion):

	import boto3
	session=boto3.Session(profile_name=fProfile, region_name=fRegion)
	object_info=session.client('guardduty')
	object=object_info.list_detectors()
	return(object)
	# return(vpcs)

def del_gd_detectors(fProfile,fRegion,fDetectorId):
	import boto3
	session=boto3.Session(profile_name=fProfile, region_name=fRegion)
	object_info=session.client('guardduty')
	object=object_info.delete_detector(DetectorId=fDetectorId)
	return(object)

def find_profile_functions(fProfile,fRegion):

	import boto3
	session_lambda=boto3.Session(profile_name=fProfile, region_name=fRegion)
	lambda_info=session_lambda.client('lambda')
	functions=lambda_info.list_functions()
	return(functions)

def find_load_balancers(fProfile,fRegion,fStackFragment,fStatus):

	import boto3, logging, pprint
	logging.warning("Profile: %s | Region: %s | Fragment: %s | Status: %s",fProfile, fRegion, fStackFragment,fStatus)
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
				logging.warning("Found lb %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", load_balancer['LoadBalancerName'], fProfile, fRegion, fStackFragment, fStatus)
				load_balancer_Copy.append(load_balancer)
	elif (fStatus=='active' or fStatus=='ACTIVE'):
		for load_balancer in load_balancers['LoadBalancers']:
			if fStackFragment in load_balancer['LoadBalancerName']:
				logging.warning("Found lb %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", load_balancer['LoadBalancerName'], fProfile, fRegion, fStackFragment, fStatus)
				load_balancer_Copy.append(load_balancer)
	return(load_balancer_Copy)

def find_stacks(fprofile,fRegion,fStackFragment,fStatus="active"):
	"""
	fprofile is an string holding the name of the profile you're connecting to:
	fRegion is a string
	fStackFragment is a list
	fStatus is a string
	"""
	import boto3, logging, pprint
	logging.warning("Profile: %s | Region: %s | Fragment: %s | Status: %s",fprofile, fRegion, fStackFragment,fStatus)
	session_cfn=boto3.Session(profile_name=fprofile, region_name=fRegion)
	stack_info=session_cfn.client('cloudformation')
	stacksCopy=[]
	if (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='Active') and not (fStackFragment=='All' or fStackFragment=='ALL'  or fStackFragment=='all'):
		# Send back stacks that are active, check the fragment further down.
		stacks=stack_info.list_stacks(StackStatusFilter=["CREATE_COMPLETE","DELETE_FAILED","UPDATE_COMPLETE","UPDATE_ROLLBACK_COMPLETE","DELETE_IN_PROGRESS"])
		logging.warning("1 - Found %s stacks. Looking for fragment %s",len(stacks),fStackFragment)
		for stack in stacks['StackSummaries']:
			if fStackFragment in stack['StackName']:
				# Check the fragment now - only send back those that match
				logging.warning("Found stack %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], fprofile, fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	elif (fStackFragment=='all' or fStackFragment=='ALL' or fStackFragment=='All') and (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='Active'):
		# Send back all stacks regardless of fragment, check the status further down.
		stacks=stack_info.list_stacks(StackStatusFilter=["CREATE_COMPLETE","DELETE_FAILED","UPDATE_COMPLETE","UPDATE_ROLLBACK_COMPLETE"])
		logging.warning("2 - Found %s stacks.",len(stacks))
		for stack in stacks['StackSummaries']:
			# if fStatus in stack['StackStatus']:
			# Check the status now - only send back those that match a single status
			# I don't see this happening unless someone wants Stacks in a "Deleted" or "Rollback" type status
			logging.warning("Found stack %s in Profile: %s in Region: %s regardless of fragment and Status: %s", stack['StackName'], fprofile, fRegion, fStatus)
			stacksCopy.append(stack)
	elif (fStackFragment=='all' or fStackFragment=='ALL' or fStackFragment=='All') and (fStatus=='all' or fStatus=='ALL' or fStatus=='All'):
		# Send back all stacks.
		stacks=stack_info.list_stacks()
		logging.warning("3 - Looking for ALL the stacks in Profile: %s in Region: %s", fProfile, fRegion)
		return(stacks['StackSummaries'])
	elif not (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='Active'):
		# Send back stacks that match the single status, check the fragment further down.
		try:
			stacks=stack_info.list_stacks(StackStatusFilter=[fStatus])
		except Exception as e:
			print(e)
		for stack in stacks['StackSummaries']:
			if fStackFragment in stack['StackName'] and fStatus in stack['StackStatus']:
				# Check the fragment now - only send back those that match
				logging.warning("Found stack %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], fProfile, fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	return(stacksCopy)

def delete_stack(fprofile,fRegion,fStackName,**kwargs):
	"""
	fprofile is an string holding the name of the profile you're connecting to:
	fRegion is a string
	fStackName is a string
	RetainResources should be a boolean
	ResourcesToRetain should be a list
	"""
	import boto3, logging, pprint
	if "RetainResources" in kwargs:
		RetainResources = True
		ResourcesToRetain = kwargs['ResourcesToRetain']
	else:
		RetainResources = False
	session_cfn=boto3.Session(profile_name=fprofile, region_name=fRegion)
	client_cfn=session_cfn.client('cloudformation')
	if RetainResources:
		logging.warning("Profile: %s | Region: %s | StackName: %s",fprofile, fRegion, fStackName)
		logging.warning("	Retaining Resources: %s",ResourcesToRetain)
		response=client_cfn.delete_stack(StackName=fStackName,RetainResources=ResourcesToRetain)
	else:
		logging.warning("Profile: %s | Region: %s | StackName: %s",fprofile, fRegion, fStackName)
		response=client_cfn.delete_stack(StackName=fStackName)
	return(response)

def delete_stack2(ocredentials,fRegion,fStackName,**kwargs):
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
	import boto3, logging, pprint
	if "RetainResources" in kwargs:
		RetainResources = True
		ResourcesToRetain = kwargs['ResourcesToRetain']
	else:
		RetainResources = False
	session_cfn=boto3.Session(region_name=fRegion,
				aws_access_key_id = ocredentials['AccessKeyId'],
				aws_secret_access_key = ocredentials['SecretAccessKey'],
				aws_session_token = ocredentials['SessionToken']
				)
	client_cfn=session_cfn.client('cloudformation')
	if RetainResources:
		logging.warning("Account: %s | Region: %s | StackName: %s",ocredentials['AccountNumber'], fRegion, fStackName)
		logging.warning("	Retaining Resources: %s",ResourcesToRetain)
		response=client_cfn.delete_stack(StackName=fStackName,RetainResources=ResourcesToRetain)
	else:
		logging.warning("Account: %s | Region: %s | StackName: %s",ocredentials['AccountNumber'], fRegion, fStackName)
		response=client_cfn.delete_stack(StackName=fStackName)
	return(response)

def find_stacks_in_acct(ocredentials,fRegion,fStackFragment,fStatus="active"):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the AccountId

	fRegion is a string
	fStackFragment is a list
	"""
	import boto3, logging, pprint
	logging.warning("AccessKeyId:")
	logging.warning("Acct ID #: %s | Region: %s | Fragment: %s | Status: %s",str(ocredentials['AccountNumber']), fRegion, fStackFragment,fStatus)
	session_cfn=boto3.Session(region_name=fRegion,
				aws_access_key_id = ocredentials['AccessKeyId'],
				aws_secret_access_key = ocredentials['SecretAccessKey'],
				aws_session_token = ocredentials['SessionToken']
				)
	stack_info=session_cfn.client('cloudformation')
	stacksCopy=[]
	if (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='Active') and not (fStackFragment=='all' or fStackFragment=='ALL' or fStackFragment=='All'):
		# Send back stacks that are active, check the fragment further down.
		stacks=stack_info.list_stacks(StackStatusFilter=["CREATE_COMPLETE","UPDATE_COMPLETE","UPDATE_ROLLBACK_COMPLETE"])
		for stack in stacks['StackSummaries']:
			if fStackFragment in stack['StackName']:
				# Check the fragment now - only send back those that match
				logging.warning("1-Found stack %s in Account: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], ocredentials['AccountNumber'], fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	elif (fStackFragment=='all' or fStackFragment=='ALL' or fStackFragment=='All') and (fStatus=='all' or fStatus=='ALL' or fStatus=='All'):
		# Send back all stacks.
		stacks=stack_info.list_stacks()
		logging.warning("4-Found %s the stacks in Account: %s in Region: %s", len(stacks), ocredentials['AccessKeyId'], fRegion)
		return(stacks['StackSummaries'])
	elif (fStackFragment=='all' or fStackFragment=='ALL' or fStackFragment=='All') and (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='Active'):
		# Send back all stacks regardless of fragment, check the status further down.
		stacks=stack_info.list_stacks(StackStatusFilter=["CREATE_COMPLETE","UPDATE_COMPLETE","UPDATE_ROLLBACK_COMPLETE"])
		for stack in stacks['StackSummaries']:
			logging.warning("2-Found stack %s in Account: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], ocredentials['AccountNumber'], fRegion, fStackFragment, fStatus)
			stacksCopy.append(stack)
			# logging.warning("StackStatus: %s | My status: %s", stack['StackStatus'], fStatus)
	elif not (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='Active'):
		# Send back stacks that match the single status, check the fragment further down.
		try:
			stacks=stack_info.list_stacks(StackStatusFilter=[fStatus])
		except Exception as e:
			print(e)
		for stack in stacks['StackSummaries']:
			if fStackFragment in stack['StackName'] and fStatus in stack['StackStatus']:
				# Check the fragment now - only send back those that match
				logging.warning("5-Found stack %s in Account: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], ocredentials['AccountNumber'], fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	return(stacksCopy)

def find_saml_components_in_acct(ocredentials,fRegion):
	"""
	ocredentials is an object with the following structure:
		- ['AccessKeyId'] holds the AWS_ACCESS_KEY
		- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
		- ['SessionToken'] holds the AWS_SESSION_TOKEN
		- ['AccountNumber'] holds the AccountId

	fRegion is a string
	"""
	import boto3, logging, pprint
	logging.warning("Acct ID #: %s | Region: %s ",str(ocredentials['AccountNumber']), fRegion)
	session_aws=boto3.Session(region_name=fRegion,
				aws_access_key_id = ocredentials['AccessKeyId'],
				aws_secret_access_key = ocredentials['SecretAccessKey'],
				aws_session_token = ocredentials['SessionToken']
				)
	iam_info=session_aws.client('iam')
	saml_providers=iam_info.list_saml_providers()['SAMLProviderList']
	return(saml_providers)

def find_stacksets(fProfile,fRegion,fStackFragment):
	"""
	fProfile is a string
	fRegion is a string
	fStackFragment is a list
	"""
	import boto3, logging, pprint

	logging.info("Profile: %s | Region: %s | Fragment: %s",fProfile, fRegion, fStackFragment)
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	stack_info=session_cfn.client('cloudformation')
	stacksets=stack_info.list_stack_sets(Status='ACTIVE')
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

def find_stacksets2(facct_creds,fRegion,faccount,fStackFragment=""):
	"""
	facct_creds is an object which contains the credentials for the account
	fRegion is a string
	fStackFragment is a string
	"""
	import boto3, logging, pprint

	logging.info("Account: %s | Region: %s | Fragment: %s",faccount, fRegion, fStackFragment)
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


def delete_stackset(fProfile,fRegion,fStackSetName):
	"""
	fProfile is a string holding the name of the profile you're connecting to:
	fRegion is a string
	fStackSetName is a string
	"""
	import boto3, logging, pprint
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn=session_cfn.client('cloudformation')
	logging.warning("Profile: %s | Region: %s | StackSetName: %s",fProfile, fRegion, fStackSetName)
	response=client_cfn.delete_stack_set(StackSetName=fStackSetName)
	return(response)

def find_stack_instances(fProfile,fRegion,fStackSetName):
	"""
	fProfile is a string
	fRegion is a string
	fStackSetName is a string
	"""
	import boto3, logging, pprint

	import logging, boto3

	logging.warning("Profile: %s | Region: %s | StackSetName: %s",fProfile, fRegion, fStackSetName)
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	stack_info=session_cfn.client('cloudformation')
	stack_instances=stack_info.list_stack_instances(StackSetName=fStackSetName)
	stack_instances_list=stack_instances['Summaries']
	while 'NextToken' in stack_instances.keys(): # Get all instnce names
		stack_instances=stack_info.list_stack_instances(StackSetName=fStackSetName,NextToken=stack_instances['NextToken'])
		stack_instances_list.append(stack_instances['Summaries'])
	return(stack_instances_list)

def delete_stack_instances(fProfile,fRegion,lAccounts,lRegions,fStackSetName,fOperationName="StackDelete"):
	"""
	fProfile is the Root Profile that owns the stackset
	fRegion is the region where the stackset resides
	lAccounts is a list of accounts
	lRegion is a list of regions
	fStackSetName is a string
	fOperationName is a string (to identify the operation)
	"""
	import boto3, logging, pprint

	logging.warning("Deleting %s StackSetName over %s accounts across %s regions" % (fStackSetName,len(lAccounts),len(lRegions)))
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	client_cfn=session_cfn.client('cloudformation')
	response = client_cfn.delete_stack_instances(
		StackSetName=fStackSetName,
		Accounts=lAccounts,
		Regions=lRegions,
		RetainStacks=False,
		OperationId=fOperationName
	)
