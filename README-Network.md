#Project Overview
Inventory_Scripts is a git repository to aggregate a number of scripts I've written, with the intent to make it easier to keep track of what's created and/ or running in any one of your (possibly) many AWS accounts... The scripts in this repo will be discussed below.

**_Critical Note_**:  *If your profiles include the "region" within the profile section, these scripts will be limited to looking for resources ONLY WITHIN THAT REGION. There's no quick answer to this problem right now, since all cli commands are inherently regionally focused. Just something to bear in mind when running these scripts.*

## Profile Scripts
- **AllProfiles.sh**
    - This script displays all of your configured profiles, including in both your "credentials" file, as well as the "config" file.
---
## Network Scripts
- **all_my_vpcs.sh**
 	- This script displays all of the vpcs you have in all of your accounts. (See important note at the top of this README).
- **all_my_subnets.sh**
 	- This script displays all of the subnets you have in all of your accounts.
- **my_vpcs.sh**
 	- This script displays all of the vpcs you have in the account you specify. (See important note at the top of this README).
