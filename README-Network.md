#Project Overview
Inventory_Scripts is a git repository to aggregate a number of scripts I've written, with the intent to make it easier to keep track of what's created and/ or running in any one of your (possibly) many AWS accounts... The scripts in this repo will be discussed below.

**_Critical Note_**:  *If your profiles include the "region" within the profile section, these scripts will be limited to looking for resources ONLY WITHIN THAT REGION. There's no quick answer to this problem right now, since all cli commands are inherently regionally focused. Just something to bear in mind when running these scripts.*
- By default - the ONLY region shown will be whatever is configured as your default region for the given profile. If there is no default region, you will have to specify one at the command line.
- As a corollary to above, if you **do** specify a region at the command line (e.g. --region <region-name>), the script will automatically use this region instead of your default.


## Profile Scripts
- **AllProfiles.sh**
    - This script displays all of your configured profiles, including in both your "credentials" file, as well as the "config" file.
    - There is a "feature" within this script that will **skip** the profiles you may have configured, but don't really want to ever consider. For instance - I have my personal AWS profile in my credentials file, but I don't generally need to examine it for my inventory needs. I also have a "False Positive" profile, which shouldn't ever actually work (for testing) which is reasonable to skip when looking for inventory. An example array declaration with these profiles is listed at the top of the script (but commented out).
---
## Network Scripts
- **all_my_vpcs.sh**
 	- This script displays all of the vpcs you have in all of your accounts. (See important note regarding regions above).
- **all_my_subnets.sh**
 	- This script displays all of the subnets you have in all of your accounts.
- **my_vpcs.sh**
 	- This script displays all of the vpcs you have in the account you specify. (See important note at the top of this README).
