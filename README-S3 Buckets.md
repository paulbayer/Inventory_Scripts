#Project Overview
Inventory_Scripts is a git repository to aggregate a number of scripts I've written, with the intent to make it easier to keep track of what's created and/ or running in any one of your (possibly) many AWS accounts... The scripts in this repo will be discussed below.

**_Critical Note_**:  *If your profiles include the "region" within the profile section, these scripts will be limited to looking for resources ONLY WITHIN THAT REGION. There's no quick answer to this problem right now, since all cli commands are inherently regionally focused. Just something to bear in mind when running these scripts.*

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
