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
		ChildAccounts: If the account is a "Root", this is a listing of the child accounts
	"""
	def __init__(self, fProfile=None, fRegion='us-east-1'):
		logging.basicConfig(format="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s")

		logging.info(f"Capturing Account Information for profile {fProfile}...")
		self.region = fRegion.lower()
		self.AccountStatus = 'INACTIVE'
		if fProfile is None:
			self.session = boto3.Session(region_name=self.region)
			self.AccountStatus = 'ACTIVE'
		else:
			self.session = boto3.Session(profile_name=fProfile, region_name=self.region)
			self.AccountStatus = 'ACTIVE'
		self.acct_number = self.acct_num()
		if self.acct_number == 'Failure':
			logging.error(f"Didn't find information for profile {fProfile} as something failed")
			account_access_successful = False
		else:
			logging.info(f"Found information for Account {self.acct_number} in profile {fProfile}")
			account_access_successful = True
		if account_access_successful:
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
				# self.creds_dict = None
				# self.acct_number = '123456789012'
				# self.AccountType = None
		else:
			logging.error(f"Profile {fProfile} failed to successfully access an account")
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
		                     'MgmntAccountId': None,
		                     'ManagementEmail': None}
		try:
			session_org = self.session
			client_org = session_org.client('organizations')
			response = client_org.describe_organization()['Organization']
			function_response['OrgId'] = response['Id']
			function_response['Id'] = self.acct_number
			function_response['AccountNumber'] = self.acct_number
			function_response['MasterAccountId'] = response['MasterAccountId']
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
		except:
			print("Other kind of failure")
			pass
		return (function_response)

	def find_child_accounts(self):
		"""
		This is an example of the list response from this call:
			[
			{'MgmntAccount':'<12 digit number>', 'AccountId': 'xxxxxxxxxxxx', 'AccountEmail': 'EmailAddr1@example.com', 'AccountStatus': 'ACTIVE'},
			{'MgmntAccount':'<12 digit number>', 'AccountId': 'yyyyyyyyyyyy', 'AccountEmail': 'EmailAddr2@example.com', 'AccountStatus': 'ACTIVE'},
			{'MgmntAccount':'<12 digit number>', 'AccountId': 'zzzzzzzzzzzz', 'AccountEmail': 'EmailAddr3@example.com', 'AccountStatus': 'SUSPENDED'}
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
						child_accounts.append({'MgmntAccount': self.acct_number,
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
			child_accounts.append({'MgmntAccount': self.acct_num(),
			                       'AccountId': self.acct_num(),
			                       'AccountEmail': 'Not an Org Management Account',
			                       # We know the account is ACTIVE because if it was SUSPENDED, we wouldn't have gotten a valid response from the org_root check
			                       'AccountStatus': 'ACTIVE'})
			return (child_accounts)
		else:
			logging.warning(f"Account {self.acct_num()} suffered a crisis of identity")
			return ()
