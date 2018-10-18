
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
			logging.info('Have %s| Looking for %s',y,x)
			# print("Have:",y,"| Looking for:",x)
			if y.find(x) >=0:
				logging.info('Found %s',y)
				# print("Found it")
				RegionNames2.append(y)
	# pprint.pprint(RegionNames2)
	return(RegionNames2)
		# if x.find(fkey) >= 0:
		# 	print("Add:",x,"to list")
		# 	RegionNames2.append(x)
			# RegionNames.remove(x)

def find_profile_instances(fProfile,fRegion):

	import boto3
	session_ec2=boto3.Session(profile_name=fProfile, region_name=fRegion)
	instance_info=session_ec2.client('ec2')
	instances=instance_info.describe_instances()
	return(instances)

def find_stacks(fProfile,fRegion,fStackFragment):

	import boto3
	session_cfn=boto3.Session(profile_name=fProfile, region_name=fRegion)
	stack_info=session_cfn.client('cloudformation')
	stacks=stack_info.list_stacks()
	stacksets=stack_info.list_stack_sets
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

def find_org_root(fProfile):

	import boto3
	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('organizations')
	response=client_org.describe_organization()
	# root_org=response['Organization']['MasterAccountId']
	# org_id=response['Organization']['Id']
	return (response['Organization'])

def find_if_lz(fProfile):
	import boto3

	session_org = boto3.Session(profile_name=fProfile)
	client_org = session_org.client('ec2')
	response=client_org.describe_vpcs(
		Filters=[
        {
            'Name': 'tag:AWS_Solutions',
            'Values': [
                'LandingZoneStackSet',
            ]
        }
    	]
	)
	for vpc in response['Vpcs']:
		for tag in vpc['Tags']:
			if tag['Key']=="AWS_Solutions":
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
	response=client_org.describe_organization()
	root_org=response['Organization']['MasterAccountId']
	org_id=response['Organization']['Id']
	# return {'root_org':root_org,'org_id':org_id}
	return (root_org,org_id)

def find_child_accounts(fProfile):

	import boto3
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
	response=client_sts.get_caller_identity()
	acct_num=response['Account']
	return (acct_num)

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
	try:
		for profile in fSkipProfiles:
			ProfileList.remove(profile)
	except ClientError as my_Error:
		pass
	except ValueError as my_Error:
		logging.error('Error found: %s',my_Error)
		pass
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
