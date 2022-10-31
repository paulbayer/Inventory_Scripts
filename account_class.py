""""
1. Accept either a single profile or multiple profiles
2. Determine if a profile (or multiple profiles) was provided
3. If a single profile was provided - determine whether it's been provided as an org account, or as a single profile
4. If the profile is of a root account and it's supposed to be for the whole Org - **note that**
	Otherwise - treat it like a standalone account (like anything else)
5. If it's a root account, we need to figure out how to find all the child accounts, and the proper roles to access them by
	5a. Find all the child accounts
	5b. Find out if any of those children are SUSPENDED and remove them from the list
	5c. Figure out the right roles to access the children by - which might be a config file, since there might be a mapping for this.
	5d. Once we have a way to access all the children, we can provide account-credentials to access the children by (but likely not the root account itself)
	5e. Call the actual target scripts - with the proper credentials (which might be a profile, or might be a session token)
6. If it's not a root account - then ... just use it as a profile

What does a script need to satisfy credentials? It needs a boto3 session. From the session, everything else can derive... yes?

So if we created a class object that represented the account:
	Attributes:
		AccountID: Its 12 digit account number
		botoClient: Access into the account (profile, or access via a root path)
		MgmntAccessRoles: The role that the root account uses to get access
		AccountStatus: Whether it's ACTIVE or SUSPENDED
		AccountType: Whether it's a root org account, a child account or a standalone account
		ParentProfile: What its parent profile name is, if available
		If it's an Org account:
			ALZ: Whether the Org is running an ALZ
			CT: Whether the Org is running CT
	Functions:
		Which regions and partitions it's enabled for
		(Could all my inventory items be an attribute of this class?)

"""
import boto3
import logging
from botocore.exceptions import ProfileNotFound, ClientError


def _validate_region(faws_prelim_session, fRegion=None):
	import logging
	from botocore.exceptions import CredentialRetrievalError, ClientError

	try:
		client_region = faws_prelim_session.client('ec2')
		all_regions_list = [region_name['RegionName'] for region_name in client_region.describe_regions(AllRegions=True)['Regions']]
	except ClientError as myError:
		message = (f"Access using these credentials didn't work. "
		           f"Error Message: {myError}")
		result = {
			'Success': False,
			'Message': message,
			'Region': fRegion}
		return (result)
	except CredentialRetrievalError as myError:
		message = (f"Error getting access credentials. "
		           f"Error Message: {myError}")
		result = {
			'Success': False,
			'Message': message,
			'Region': fRegion}
		return (result)
	if fRegion is None:  # Why are you trying to validate a region, and then didn't supply a region?
		logging.info(f"No region supplied to check. Defaulting to 'us-east-1'")
		fRegion = 'us-east-1'
	if fRegion in all_regions_list:
		logging.info(f"{fRegion} is a valid region within AWS")
		valid_region = True
	else:
		logging.info(f"{fRegion} is not a valid region within AWS. Maybe check the spelling?")
		valid_region = False
	region_info = client_region.describe_regions(Filters=[{'Name': 'region-name', 'Values': [fRegion]}])['Regions']
	if len(region_info) == 0:
		if valid_region:
			message = f"While '{fRegion}' is a valid AWS region, this account has not opted into this region"
		else:
			message = f"'{fRegion}' is not a valid AWS region name"
		logging.error(message)
		result = {
			'Success': False,
			'Message': message,
			'Region': fRegion}
		return (result)
	else:
		message = f"'{fRegion}' is a valid region for this account"
		logging.info(message)
		result = {
			'Success': True,
			'Message': message,
			'Region': fRegion}
		return (result)


class aws_acct_access:
	"""
	Class takes a boto3 session object as input
	Multiple attributes and functions exist within this class to give you information about the account
	Attributes:
		AccountStatus: Whether the account is Active or Inactive
		acct_number: The account number of the account
		AccountType: Whether the account is a "Root", "Child" or "Standalone" account
		MgmtAccount: If the account is a child, this is its Management Account
		OrgID: The Organization the account belongs to, if it does
		MgmtEmail: The email address of the Management Account, if the account is a "Root" or "Child"
		creds: The credentials used to get into the account
		Region: The region used to authenticate into this account. Important to find out if certain regions are allowed (opted-in).
		ChildAccounts: If the account is a "Root", this is a listing of the child accounts
	"""
	def __init__(self, fProfile=None, fRegion='us-east-1', ocredentials=None):
		logging.basicConfig(format="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s")
		# First thing's first: We need to validate that the region they sent us to use is valid for this account.
		# Otherwise, all hell will break if it's not.
		UsingKeys = False
		UsingSessionToken = False
		account_access_successful = False
		account_and_region_access_successful = False
		if ocredentials is not None and ocredentials['Success']:
			# Trying to instantiate a class, based on passed in credentials
			UsingKeys = True
			UsingSessionToken = False
			if 'SessionToken' in ocredentials:
				# Using a token-based role
				UsingSessionToken = True
				prelim_session = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'],
				                               aws_secret_access_key=ocredentials['SecretAccessKey'],
				                               aws_session_token=ocredentials['SessionToken'],
				                               region_name='us-east-1')
				account_access_successful = True
			else:
				# Not using a token-based role
				prelim_session = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'],
				                               aws_secret_access_key=ocredentials['SecretAccessKey'],
				                               region_name='us-east-1')
				account_access_successful = True
		else:
			# Not trying to use account_key_credentials
			try:
				prelim_session = boto3.Session(profile_name=fProfile, region_name='us-east-1')
				account_access_successful = True
			except ProfileNotFound as my_Error:
				ErrorMessage = (f"The profile {fProfile} wasn't found. Perhaps there was a typo?"
				                f"Error Message: {my_Error}")
				logging.error(ErrorMessage)
				account_access_successful = False
		if account_access_successful:
			try:
				result = _validate_region(prelim_session, fRegion)
				if result['Success'] is True:
					if UsingSessionToken:
						logging.debug("Credentials are using SessionToken")
						self.session = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'],
						                             aws_secret_access_key=ocredentials['SecretAccessKey'],
						                             aws_session_token=ocredentials['SessionToken'],
						                             region_name=result['Region'])
					elif UsingKeys:
						logging.debug("Credentials are using Keys, but no SessionToken")
						self.session = boto3.Session(aws_access_key_id=ocredentials['AccessKeyId'],
						                             aws_secret_access_key=ocredentials['SecretAccessKey'],
						                             region_name=result['Region'])
					else:
						logging.debug("Credentials are using a profile")
						self.session = boto3.Session(profile_name=fProfile, region_name=result['Region'])
					account_and_region_access_successful = True
					self.AccountStatus = 'ACTIVE'
				else:
					logging.error(result['Message'])
					account_and_region_access_successful = False
					self.AccountStatus = 'INACTIVE'
			except ProfileNotFound as my_Error:
				logging.error(f"Profile {fProfile} not found. Please ensure this profile is valid within your system.")
				logging.info(f"Error: {my_Error}")
				account_and_region_access_successful = False

		logging.info(f"Capturing Account Information for profile {fProfile}...")
		if not account_and_region_access_successful:
			logging.error(f"Didn't find information for profile {fProfile} as something failed")
		else:
			logging.info(f"Successfully validated access to account in region {fRegion}")
		if account_and_region_access_successful:
			self.acct_number = self.acct_num()
			self._AccountAttributes = self.find_account_attr()
			logging.info(f"Found {len(self._AccountAttributes)} attributes in this account")
			self.AccountType = self._AccountAttributes['AccountType']
			self.MgmtAccount = self._AccountAttributes['MasterAccountId']
			self.OrgID = self._AccountAttributes['OrgId']
			self.MgmtEmail = self._AccountAttributes['ManagementEmail']
			logging.info(f"Account {self.acct_number} is a {self.AccountType} account")
			self.creds = self.session._session._credentials.get_frozen_credentials()
			if self.AccountType.lower() == 'root':
				logging.info("Enumerating all of the child accounts")
				self.ChildAccounts = self.find_child_accounts()
				logging.debug(f"As acct {self.acct_number} is the root account, we found {len(self.ChildAccounts)} accounts in the Org")

			else:
				self.ChildAccounts = self.find_child_accounts()
		elif fProfile is not None:
			logging.error(f"Profile {fProfile} failed to successfully access an account")
			self.AccountType = 'Unknown'
			self.MgmtAccount = 'Unknown'
			self.OrgID = 'Unknown'
			self.MgmtEmail = 'Unknown'
			self.creds = 'Unknown'
		elif ocredentials is not None:
			logging.error(f"Credentials for access_key {ocredentials['AccountNum']} failed to successfully access an account")
			self.AccountType = 'Unknown'
			self.MgmtAccount = 'Unknown'
			self.OrgID = 'Unknown'
			self.MgmtEmail = 'Unknown'
			self.creds = 'Unknown'

	def acct_num(self):
		"""
		This function returns a string of the account's 12 digit account number
		"""
		import logging
		from botocore.exceptions import ClientError, CredentialRetrievalError

		try:
			aws_session = self.session
			logging.info(f"Accessing session object to find its account number")
			client_sts = aws_session.client('sts')
			response = client_sts.get_caller_identity()
			creds = response['Account']
		except ClientError as my_Error:
			if str(my_Error).find("UnrecognizedClientException") > 0:
				logging.info(f"Security Issue")
				pass
			elif str(my_Error).find("InvalidClientTokenId") > 0:
				logging.info(f"Security Token is bad - probably a bad entry in config")
				pass
			else:
				print(my_Error)
				logging.info(f"Other kind of failure for boto3 access in acct")
				pass
			creds = "Failure"
		except CredentialRetrievalError as my_Error:
			if str(my_Error).find("custom-process") > 0:
				logging.info(f"Profile requires custom authentication")
				pass
			else:
				print(my_Error)
				pass
			creds = "Failure"
		return (creds)

	def find_account_attr(self):
		import logging
		from botocore.exceptions import ClientError, CredentialRetrievalError

		"""
		In the case of an Org Root or Child account, I use the response directly from the AWS SDK. 
		You can find the output format here: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/organizations.html#Organizations.Client.describe_organization
		"""
		function_response = {'AccountType': 'Unknown',
		                     'AccountNumber': None,
		                     'OrgId': None,
		                     'Id': None,
		                     'MasterAccountId': None,
		                     'MgmtAccountId': None,
		                     'ManagementEmail': None}
		try:
			session_org = self.session
			client_org = session_org.client('organizations')
			response = client_org.describe_organization()['Organization']
			function_response['OrgId'] = response['Id']
			function_response['Id'] = self.acct_number
			function_response['AccountNumber'] = self.acct_number
			function_response['MasterAccountId'] = response['MasterAccountId']
			function_response['MgmtAccountId'] = response['MasterAccountId']
			function_response['ManagementEmail'] = response['MasterAccountEmail']
			if response['MasterAccountId'] == self.acct_number:
				function_response['AccountType'] = 'Root'
			else:
				function_response['AccountType'] = 'Child'
			return (function_response)
		except ClientError as my_Error:
			if str(my_Error).find("AWSOrganizationsNotInUseException") > 0:
				function_response['AccountType'] = 'StandAlone'
				function_response['Id'] = self.acct_number
				function_response['OrgId'] = None
				function_response['ManagementEmail'] = 'Email not available'
				function_response['AccountNumber'] = self.acct_number
				function_response['MasterAccountId'] = self.acct_number
				function_response['MgmtAccountId'] = self.acct_number
			elif str(my_Error).find("UnrecognizedClientException") > 0:
				logging.error(f"Security Issue with account {self.acct_number}")
			elif str(my_Error).find("InvalidClientTokenId") > 0:
				logging.error(f"Security Token is bad - probably a bad entry in config for account {self.acct_number}")
			elif str(my_Error).find("AccessDenied") > 0:
				logging.error(f"Access Denied for account {self.acct_number}")
			pass
		except CredentialRetrievalError as my_Error:
			logging.error(f"Failure pulling or updating credentials for {self.acct_number}")
			print(my_Error)
			pass
		except Exception as my_Error:
			print("Other kind of failure")
			print(my_Error)
			pass
		return (function_response)

	def find_child_accounts(self):
		"""
		This is an example of the list response from this call:
			[
			{'MgmtAccount':'<12 digit number>', 'AccountId': 'xxxxxxxxxxxx', 'AccountEmail': 'EmailAddr1@example.com', 'AccountStatus': 'ACTIVE'},
			{'MgmtAccount':'<12 digit number>', 'AccountId': 'yyyyyyyyyyyy', 'AccountEmail': 'EmailAddr2@example.com', 'AccountStatus': 'ACTIVE'},
			{'MgmtAccount':'<12 digit number>', 'AccountId': 'zzzzzzzzzzzz', 'AccountEmail': 'EmailAddr3@example.com', 'AccountStatus': 'SUSPENDED'}
			]
		This can be convenient for appending and removing.
		"""
		import logging
		from botocore.exceptions import ClientError

		child_accounts = []
		if self.find_account_attr()['AccountType'].lower() == 'root':
			try:
				session_org = self.session
				client_org = session_org.client('organizations')
				response = client_org.list_accounts()
				theresmore = True
				logging.info(f"Enumerating Account info for account: {self.acct_number}")
				while theresmore:
					for account in response['Accounts']:
						child_accounts.append({'MgmtAccount': self.acct_number,
						                       'AccountId': account['Id'],
						                       'AccountEmail': account['Email'],
						                       'AccountStatus': account['Status']})
					if 'NextToken' in response:
						theresmore = True
						response = client_org.list_accounts(NextToken=response['NextToken'])
					else:
						theresmore = False
				return (child_accounts)
			except ClientError as my_Error:
				logging.warning(f"Account {self.acct_num()} doesn't represent an Org Root account")
				logging.debug(my_Error)
				return ()
		elif self.find_account_attr()['AccountType'].lower() in ['standalone', 'child']:
			child_accounts.append({'MgmtAccount': self.acct_num(),
			                       'AccountId': self.acct_num(),
			                       'AccountEmail': 'Not an Org Management Account',
			                       # We know the account is ACTIVE because if it was SUSPENDED, we wouldn't have gotten a valid response from the org_root check
			                       'AccountStatus': 'ACTIVE'})
			return (child_accounts)
		else:
			logging.warning(f"Account {self.acct_num()} suffered a crisis of identity")
			return ()

	def __str__(self):
		return(f"Account #{self.acct_number} is a {self.AccountType} account with {len(self.ChildAccounts)-1} child accounts")

	def __repr__(self):
		return(f"Account #{self.acct_number} is a {self.AccountType} account with {len(self.ChildAccounts)-1} child accounts")
