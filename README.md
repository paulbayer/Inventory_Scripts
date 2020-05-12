#Project Overview
Inventory_Scripts is a git repository to aggregate a number of scripts I've written, with the intent to make it easier to keep track of what's created and/ or running in any one of your (possibly) many AWS accounts... The scripts in this repo are discussed below.

**_Note_**:  _The tools I've written here have grown organically. They're presented below in an order I thought made sense, but they were definitely not created all at once, nor all kept up to the same level of perfection. I started this journey back in 2017 when there was no such thing as the Landing Zone, and Federation wasn't as prevalent a thing, so I assumed everyone would have profiles for every account they managed. Fast-forward to 2019 and we realize that most admin is done by authenticating to one account and using cross-account roles to authorize to other Child accounts. Hence - some of these files still work by profile, but I'm slowly moving everything over to being able to work with a Federated model. I still haven't baked in MFA token stuff, but I think I might just rely on the OS for that in the short term._

**_Note_**: _I've tried to make the "verbose" and "debugging" options standard across all of the scripts. Apologies if they're not._
  - -v for some additional logging (level: ERROR)
    - For those times when I decided to show less information on screen, to keep the output neat - you could use this level of logging to get what an interested user might want to see.
  - -vv for even more logging (level: CRITICAL)
    - You could use this level of logging to get what a developer might want to see.
  - -d for lots of logging (level: INFO)
    - This is generally the lowest level I would recommend anyone use.
  - -dd for crazy amount of logging (level: DEBUG)
    - I would avoid the "debug" level because Python itself tends to bombard you with so much screen-spam that it's not useful. I've used DEBUG level for when I was writing the code and needed to debug it myself.

- **Inventory_Modules.py**
  - This is the "utils" file that is referenced by nearly every other script I've written. I didn't know Python well enough when I started to know that I should have named this "utils". If I get ambitious, maybe I'll go through and rename it within every script.

- **ALZ_CheckAccount.py**
  - This script takes an Organization Master Account profile, and checks additional accounts to see if they meet the pre-reqs to be "adopted" by either Landing Zone or Control Tower.

- **RegistrationScript.py**
  - This script goes through an Organization and determines (based on roles) whether the account has been on-boarded to the AWS Federation tool or not. If not, it creates a temporary user ("Alice") and prints the information to the screen to be able to register the account to the tool.

ReportOnStateMachines.py
SC_Products_to_CFN_Stacks.py
TrustPolicy_Org-Parent.json
all_my_cfnstacks.py
all_my_cfnstacksets.py
all_my_config_recorders_and_delivery_channels.py
all_my_elbs.py
all_my_functions.py
all_my_gd-detectors.py
all_my_instances.py
all_my_orgs.py
all_my_phzs.py
all_my_roles.py
all_my_saml_providers.py
all_my_vpcs.py
all_my_vpcs2.py
del_my_cfnstacksets.py
delete_bucket_objects.py
my_org_users.py
my_ssm_parameters.py


## Profile Scripts
- **AllProfiles.sh**
  - This script displays all of your configured profiles, including in both your ```~/.aws/credentials``` file, as well as the ```~/.aws/config``` file.
- **my_account_number.sh**
  - This script simply shows you the account number for the account whose profile you specify at the command line.
- **profiles.sh**
  - This script shows you the account number for all profiles (accounts) in your ```~/.aws/credentials``` file.
---
## Config-like Discovery Scripts
- **Config-Discovered-Resources.sh**
  - This script displays all resources that have been discovered using the "Config" service within AWS. If you haven't enabled and configured the "Config" service, this won't give you any information.
---
## EC2 Scripts
- **my_instances.sh**
  - This script displays all instances in the specified account (by specifying the profile to run against).
- **all_my_instances.sh**
  - This script displays all instances in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
- **my_sec_groups.sh**
  - This script displays all security groups in the specified account.
---
## S3 Scripts
_These scripts are global, and not limited to the inherited region of the profile, like many other scripts._
- **all_my_buckets.sh**
  - This script displays all buckets in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
- **all_my_buckets_with_sizes.sh**
  - This script displays all buckets, # of files, and the total size of each bucket in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
- **my_buckets.sh**
  - This script displays all buckets in the specific profile.
- **my_buckets_with_sizes.sh**
  - This script displays all buckets, # of files, and the total size of each bucket in the specified profile.
---
## CloudFormation Scripts
- **all_my_stacks.sh**
  - This script displays all CFT Stacks in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
- **my_stacks.sh**
	- This script displays all CloudFormation Stacks in your specified account.
- **my_exports.sh**
	- This script displays all CloudFormation Exports in your specified account.
---
## Config Rule Scripts
- **all_my_config_rules.sh**
  - This script displays all Config Rules and their state in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
---
## CloudTrail Scripts
- **all_my_trails.sh**
  - This script displays all CloudTrail trails in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
---
## EFS Scripts
- **all_my_filesystems.sh**
  - This script displays all EFS filesystems within an account.
---
## SNS Scripts
- **all_my_topics.sh**
  - This script displays all SNS topics in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
---
## Kinesis
- **all_my_streams.sh**
  - This script displays all Kinesis Streams in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
---
## Dynamo DB Scripts
- **all_my_DDB_tables.sh**
	- This script displays all Dynamo DB Tables in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
---
## RDS DB Scripts
- **all_my_rds.sh**
	- This script displays all RDS databases in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
---
## Athena Scripts
- **my_athena_queries.sh**
	- This script displays all Athena Queries in your specified account.
---
## SSM Parameter Store Scripts
- **all_my_parameters.sh**
	- This script displays all SSM Parameter Stores in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
---
## Lambda Scripts
- **all_my_functions_and_roles.sh**
	- This script displays all Lambda Functions and their associated IAM roles in all available accounts (by running the "AllProfiles" script and parsing the profiles to run against).
- **my_functions_and_roles.sh**
	- This script displays all Lambda Functions and their associated IAM roles in your specified account.
---
## IAM Scripts
- **all_my_policies.sh**
 	- This script displays all of the IAM policies you have in all of your accounts.
- **my_roles_with_policies.sh**
	- This script displays all of the IAM Roles and associated policies you have in your specified account.
- **all_my_roles.sh**
	- This script displays (in a table format) all of the IAM Roles (Role Name and Role ARN) you have in all of your accounts.
- **my_roles.sh**
	- This script displays (in a table format) all of the IAM Roles (Role Name and Role ARN) you have in your specified account.
- **my_roles-compare.sh**
  - This script is still in development. I'm trying to figure a way to compare the roles in one account with the roles in another. It looks like the best way to do that may be using Python's boto3, instead of the command line.
- **all_my_roles_with_policies.sh**
	- This script displays all of the IAM Roles and associated policies you have in all of your accounts.
- **groups_with_policies.sh**
	- This script displays all of the IAM Groups and associated policies you have in your specified account.
- **all_my_groups.sh**
	- This script displays all of the IAM Groups you have in all of your accounts.
- **my_groups.sh**
	- This script displays all of the IAM Groups you have in your specified account.
- **all_my_groups_with_policies.sh**
	- This script displays all of the IAM Groups and associated policies you have in all of your accounts.
- **my_users_with_policies.sh**
	- This script displays all of the IAM Users and associated policies you have in your specified account.
- **all_my_users.sh**
	- This script displays all of the IAM Users you have in all of your accounts.
- **all_my_users_with_policies.sh**
	- This script displays all of the IAM Users and associated policies you have in all of your accounts.
---
## Network Scripts
- **all_my_vpcs.sh**
 	- This script displays all of the vpcs you have in all of your accounts. (See important note at the top of this README).
- **all_my_subnets.sh**
 	- This script displays all of the subnets you have in all of your accounts.
- **my_vpcs.sh**
 	- This script displays all of the vpcs you have in the account you specify. (See important note at the top of this README).
- **my_subnets.sh**
 	- This script displays all of the subnets you have in the account you specify. (See important note at the top of this README).
---
## Other Scripts
- **menu.sh**
	- This script presents a clean, simple menu to access the other scripts. The other scripts can be used by themselves, or they can be called by this menu. Your choice.
