#Project Overview
Inventory_Scripts is a git repository to aggregate a number of scripts I've written, with the intent to make it easier to keep track of what's created and/ or running in any one of your (possibly) many AWS accounts... The scripts in this repo will be discussed below.

**_Critical Note_**:  *If your profiles include the "region" within the profile section, these scripts will be limited to looking for resources ONLY WITHIN THAT REGION. There's no quick answer to this problem right now, since all cli commands are inherently regionally focused. Just something to bear in mind when running these scripts.*

## Profile Scripts
- **AllProfiles.sh**
    - This script displays all of your configured profiles, including in both your "credentials" file, as well as the "config" file.

## IAM Scripts
- **all_my_policies.sh**
 	- This script displays all of the IAM policies you have in all of your accounts.
- **roles_with_policies.sh**
	- This script displays all of the IAM Roles and associated policies you have in your specified account.
- **all_my_IAM_roles.sh**
	- This script displays (in a table format) all of the IAM Roles (Role Name and Role ARN) you have in all of your accounts.
- **all_my_roles_with_policies.sh**
	- This script displays all of the IAM Roles and associated policies you have in all of your accounts.
- **groups_with_policies.sh**
	- This script displays all of the IAM Groups and associated policies you have in your specified account.
- **all_my_groups.sh**
	- This script displays all of the IAM Groups you have in all of your accounts.
- **all_my_groups_with_policies.sh**
	- This script displays all of the IAM Groups and associated policies you have in all of your accounts.
- **users_with_policies.sh**
	- This script displays all of the IAM Users and associated policies you have in your specified account.
- **all_my_users.sh**
	- This script displays all of the IAM Users you have in all of your accounts.
- **all_my_users_with_policies.sh**
	- This script displays all of the IAM Users and associated policies you have in all of your accounts.
---
