
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

def find_profile_instances(fProfile,fRegion):

	import boto3
	session_ec2=boto3.Session(profile_name=fProfile, region_name=fRegion)
	instance_info=session_ec2.client('ec2')
	instances=instance_info.describe_instances()
	return(instances)

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


def find_stacks(fProfile,fRegion,fStackFragment,fStatus):

	import boto3, logging, pprint
	logging.info("Profile: %s | Region: %s | Fragment: %s | Status: %s",fProfile, fRegion, fStackFragment,fStatus)
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	stack_info=session_cfn.client('cloudformation')
	stacks=stack_info.list_stacks()
	stacksCopy=[]
	if (fStackFragment=='all' or fStackFragment=='ALL') and (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='all' or fStatus=='ALL'):
		logging.info("Found all the stacks in Profile: %s in Region: %s with Fragment: %s and Status: %s", fProfile, fRegion, fStackFragment, fStatus)
		return(stacks['StackSummaries'])
	elif (fStackFragment=='all' or fStackFragment=='ALL'):
		for stack in stacks['StackSummaries']:
			if fStatus in stack['StackStatus']:
				logging.info("Found stack %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], fProfile, fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	elif (fStatus=='active' or fStatus=='ACTIVE'):
		for stack in stacks['StackSummaries']:
			if fStackFragment in stack['StackName']:
				logging.info("Found stack %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], fProfile, fRegion, fStackFragment, fStatus)
				stacksCopy.append(stack)
	return(stacksCopy)

def find_stacksets(fProfile,fRegion,fStackFragment,fStatus):

	import boto3, logging, pprint
	logging.info("Profile: %s | Region: %s | Fragment: %s | Status: %s",fProfile, fRegion, fStackFragment,fStatus)
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	stack_info=session_cfn.client('cloudformation')
	stacksets=stack_info.list_stack_sets(Status='ACTIVE')
	stacksetsCopy=[]
	if (fStackFragment=='all' or fStackFragment=='ALL') and (fStatus=='active' or fStatus=='ACTIVE' or fStatus=='all' or fStatus=='ALL'):
		logging.info("Found all the stacksets in Profile: %s in Region: %s with Fragment: %s and Status: %s", fProfile, fRegion, fStackFragment, fStatus)
		return(stacksets['Summaries'])
	elif (fStackFragment=='all' or fStackFragment=='ALL'):
		for stack in stacksets['Summaries']:
			if fStatus in stack['Status']:
				logging.info("Found stackset %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackSetName'], fProfile, fRegion, fStackFragment, fStatus)
				stacksetsCopy.append(stack)
	elif (fStatus=='active' or fStatus=='ACTIVE'):
		for stack in stacksets['Summaries']:
			if fStackFragment in stack['StackSetName']:
				logging.info("Found stackset %s in Profile: %s in Region: %s with Fragment: %s and Status: %s", stack['StackSetName'], fProfile, fRegion, fStackFragment, fStatus)
				stacksetsCopy.append(stack)
	return(stacksetsCopy)

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

def find_org_root(fProfile):
	import boto3

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_organization()
	return(response['Organization']['MasterAccountId'])

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
	response=client_org.describe_account(AccountId=fAccountId)
	email_addr=response['Account']['Email']
	return (email_addr)

def find_org_attr(fProfile):
	import boto3

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_organization()['Organization']
	# root_org=response['Organization']['MasterAccountId']
	# org_id=response['Organization']['Id']
	# return {'root_org':root_org,'org_id':org_id}
	return (response)

def find_org_attr2(fProfile):
	import boto3
	## Unused... and renamed
	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_organization()
	root_org=response['Organization']['MasterAccountId']
	org_id=response['Organization']['Id']
	# return {'root_org':root_org,'org_id':org_id}
	return (root_org,org_id)

def find_child_accounts(fProfile):
	import boto3

	child_accounts=[]
	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.list_accounts()
	for account in response['Accounts']:
		child_accounts.append(account['Id'])
	return (child_accounts)

def find_account_number(fProfile):

	import boto3
	session_sts = boto3.Session(profile_name=fProfile)
	client_sts = session_sts.client('sts')
	response=client_sts.get_caller_identity()['Account']
	return (response)

def get_profiles(fprofiles,flevel,fSkipProfiles):

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
	# try:
	# 	for profile in fSkipProfiles:
	# 		ProfileList.remove(profile)
	# except ClientError as my_Error:
	# 	pass
	# except ValueError as my_Error:
	# 	logging.error('Error found: %s',my_Error)
	# 	pass
	return(ProfileList)

	# RegionNames=[]
	# for x in range(len(regions['Regions'])):
	# 	RegionNames.append(regions['Regions'][x]['RegionName'])
	# if "all" in fkey or "ALL" in fkey:
	# 	return(RegionNames)
	# RegionNames2=[]
	# for x in fkey:
	# 	for y in RegionNames:
	# 		logging.info('Have %s| Looking for %s',y,x)
	# 		# print("Have:",y,"| Looking for:",x)
	# 		if y.find(x) >=0:
	# 			logging.info('Found %s',y)
	# 			# print("Found it")
	# 			RegionNames2.append(y)
	# # pprint.pprint(RegionNames2)
	# return(RegionNames2)
