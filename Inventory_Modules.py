
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

def get_profiles(fprofiles,fSkipProfiles):

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

def find_profile_functions(fProfile,fRegion):

	import boto3
	session_lambda=boto3.Session(profile_name=fProfile, region_name=fRegion)
	lambda_info=session_lambda.client('lambda')
	functions=lambda_info.list_functions()
	return(functions)

def find_load_balancers(fProfile,fRegion,fStackFragment,fStatus):

	import boto3, logging, pprint
	logging.info("Profile: %s | Region: %s | Fragment: %s | Status: %s",fProfile, fRegion, fStackFragment,fStatus)
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	lb_info=session_cfn.client('elbv2')
	load_balancers=lb_info.describe_load_balancers()
	load_balancers_Copy=[]
	if (fStackFragment=='all' or fStackFragment=='ALL') and (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='all' or fStatus=='ALL'):
		logging.info("Found all the lbs in Profile: %s in Region: %s with Fragment: %s and Status: %s", fProfile, fRegion, fStackFragment, fStatus)
		return(load_balancers['LoadBalancers'])
	elif (fStackFragment=='all' or fStackFragment=='ALL'):
		for load_balancer in load_balancers['LoadBalancers']:
			if fStatus in load_balancer['State']['Code']:
				logging.info("Found lb %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", load_balancer['LoadBalancerName'], fProfile, fRegion, fStackFragment, fStatus)
				load_balancer_Copy.append(load_balancer)
	elif (fStatus=='active' or fStatus=='ACTIVE'):
		for load_balancer in load_balancers['LoadBalancers']:
			if fStackFragment in load_balancer['LoadBalancerName']:
				logging.info("Found lb %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", load_balancer['LoadBalancerName'], fProfile, fRegion, fStackFragment, fStatus)
				load_balancer_Copy.append(load_balancer)
	return(load_balancer_Copy)

'''
ocredentials is an object with the following structure:
	- ['AccessKeyId'] holds the AWS_ACCESS_KEY
	- ['SecretAccessKey'] holds the AWS_SECRET_ACCESS_KEY
	- ['SessionToken'] holds the AWS_SESSION_TOKEN
fRegion is a string
fStackFragment is a list
'''
def find_stacks_in_acct(ocredentials,fRegion,fStackFragment,fStatus="active"):

	import boto3, logging, pprint
	logging.info("Key ID #: %s | Region: %s | Fragment: %s | Status: %s",str(ocredentials['AccessKeyId']), fRegion, fStackFragment,fStatus)
	session_cfn=boto3.Session(region_name=fRegion,
				aws_access_key_id = ocredentials['AccessKeyId'],
				aws_secret_access_key = ocredentials['SecretAccessKey'],
				aws_session_token = ocredentials['SessionToken']
				)
	stack_info=session_cfn.client('cloudformation')
	stacksCopy=[]
	if (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='Active'):
		# Send back stacks that are active, check the fragment further down.
		stacks=stack_info.list_stacks(StackStatusFilter=["CREATE_COMPLETE","UPDATE_COMPLETE","UPDATE_ROLLBACK_COMPLETE"])
		for stack in stacks['StackSummaries']:
			if fStackFragment in stack['StackName']:
				# Check the fragment now - only send back those that match
				logging.info("Found stack %s in AccessKeyId: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], ocredentials['AccessKeyId'], fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	elif (fStackFragment=='all' or fStackFragment=='ALL' or fStackFragment=='All'):
		# Send back all stacks regardless of fragment, check the status further down.
		stacks=stack_info.list_stacks()
		for stack in stacks['StackSummaries']:
			if fStatus in stack['StackStatus']:
				# Check the status now - only send back those that match a single status
				# I don't see this happening unless someone wants Stacks in a "Deleted" or "Rollback" type status
				logging.info("Found stack %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], fProfile, fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	elif (fStackFragment=='all' or fStackFragment=='ALL' or fStackFragment=='All') and (fStatus=='all' or fStatus=='ALL' or fStatus=='All'):
		# Send back all stacks.
		stacks=stack_info.list_stacks()
		logging.info("Found all the stacks in Profile: %s in Region: %s", fProfile, fRegion)
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
				logging.info("Found stack %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], fProfile, fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	return(stacksCopy)

'''
fProfile is a string
fRegion is a string
fStackFragment is a list
'''
def find_stacksets(fProfile,fRegion,fStackFragment):
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
	# 			logging.info("Found stackset %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackSetName'], fProfile, fRegion, fStackFragment, fStatus)
	# 			stacksetsCopy.append(stack)
	else:
		for stack in stacksets['Summaries']:
			for stackfrag in fStackFragment:
				if stackfrag in stack['StackSetName']:
					logging.info("Found stackset %s in Profile: %s in Region: %s with Fragment: %s", stack['StackSetName'], fProfile, fRegion, stackfrag)
					stacksetsCopy.append(stack)
	return(stacksetsCopy)

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
	email_addr=client_org.describe_account(AccountId=fAccountId)
	# email_addr=response['Account']['Email']
	return (email_addr['Account']['Email'])

def find_org_attr(fProfile):
	import boto3

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_organization()['Organization']
	return (response)
<<<<<<< HEAD

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
	import boto3
	# Renamed since I'm using the one below instead.
	child_accounts=[]
	child_emails=[]
	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.list_accounts()
	for account in response['Accounts']:
		child_accounts.append(account['Id'])
		child_emails.append(account['Email'])
	return (child_accounts,child_emails)

def find_child_accounts(fProfile):
	import boto3
=======
'''
This is an example of the dictionary response from this call:
	{
	    "Organization": {
	        "Id": "o-5zb7j55cba",
	        "Arn": "arn:aws:organizations::693014690250:organization/o-5zb7j55cba",
	        "FeatureSet": "ALL",
	        "MasterAccountArn": "arn:aws:organizations::693014690250:account/o-5zb7j55cba/693014690250",
	        "MasterAccountId": "693014690250",
	        "MasterAccountEmail": "paulbaye+50@amazon.com",
	        "AvailablePolicyTypes": [
	            {
	                "Type": "SERVICE_CONTROL_POLICY",
	                "Status": "ENABLED"
	            }
	        ]
	    }
	}
Typically your client call will use the result of "response['Organization']['MasterAccountId']" or something like that, depending on which attribute you're interested in.
'''

def find_child_accounts(fProfile="default"):
	import boto3, logging
	from botocore.exceptions import ClientError, NoCredentialsError
>>>>>>> mainline

	child_accounts={}
	session_org = boto3.Session(profile_name=fProfile)
	try:
		client_org = session_org.client('organizations')
		response=client_org.list_accounts()
	except ClientError as my_Error:
		logging.info("Profile %s doesn't represent an Org Root account",fProfile)
		# print("Failed on %s",my_Error)
		return()
	for account in response['Accounts']:
		# Create a key/value pair with the AccountID:AccountEmail
		child_accounts[account['Id']]=account['Email']
	return (child_accounts)

def find_account_number(fProfile):

	import boto3
	session_sts = boto3.Session(profile_name=fProfile)
	client_sts = session_sts.client('sts')
	response=client_sts.get_caller_identity()['Account']
	return (response)
