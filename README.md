#Project Overview
Inventory_Scripts is a git repository to aggregate a number of scripts I've written, with the intent to make it easier to keep track of what's created and/ or running in any one of your (possibly) many AWS accounts... The scripts in this repo are discussed below.

**_Note_**:  _The tools I've written here have grown organically. They're presented below in an order I thought made sense, but they were definitely not created all at once, nor all kept up to the same level of perfection. I started this journey back in 2017 when there was no such thing as the Landing Zone, and Federation wasn't as prevalent a thing, so I assumed everyone would have profiles for every account they managed. Fast-forward to 2019 and we realize that most admin is done by authenticating to one account and using cross-account roles to authorize to other Child accounts. Hence - some of these files still work by profile, but I'm slowly moving everything over to being able to work with a Federated model. I still haven't baked in MFA token stuff, but I think I might just rely on the OS for that in the short term._

**_Note_**: _I've tried to make the "verbose" and "debugging" options standard across all of the scripts. Apologies if they're not._
  - -v for some additional logging (level: ERROR)
    - For those times when I decided to show less information on screen, to keep the output neat - you could use this level of logging to get what an interested user might want to see.
  - -vv for even more logging (level: WARNING)
    - You could use this level of logging to get what a developer might want to see.
  - -d for lots of logging (level: INFO)
    - This is generally the lowest level I would recommend anyone use.
  - -dd for crazy amount of logging (level: DEBUG)
    - I would avoid the "debug" level because Python itself tends to bombard you with so much screen-spam that it's not useful. I've used DEBUG level for when I was writing the code and needed to debug it myself.

Additional common parameters:
  - -p: to specify the profile which the script will work with. In most cases, this could/ should be a Master Profile, but doesn't always have to be. 
  - -r: to specify the region for the script to work in. Most scripts take "all" as a valid parameter. Most scripts also assume "us-east-1" as a default if nothing is specified.
  -

- **Inventory_Modules.py**
  - This is the "utils" file that is referenced by nearly every other script I've written. I didn't know Python well enough when I started to know that I should have named this "utils". If I get ambitious, maybe I'll go through and rename it within every script.

- **ALZ_CheckAccount.py**
  - This script takes an Organization Master Account profile, and checks additional accounts to see if they meet the pre-reqs to be "adopted" by either Landing Zone or Control Tower.

- **RegistrationScript.py**
  - This script goes through an Organization and determines (based on roles) whether the account has been on-boarded to the AWS Federation tool or not. If not, it creates a temporary user ("Alice") and prints the information to the screen to be able to register the account to the tool.

- **ReportOnStateMachines.py**
- **SC_Products_to_CFN_Stacks.py**
  - This script is focused on reconciling the SC Products with the CFN Stacks they create. It definitely can happen that a CFN stack can exist without a corresponding SC Product, and it can happen that an SC Product can exist without a corresponding CFN stack (I'm looking at you AWS Control Tower!). However, when an SC Product is in ERROR state and the CFN stack is in an error state - you're best served by terminating the SC Product and starting over. This script can help you find those instances and even offers to get rid of them for you.

- **all_my_cfnstacks.py**
  - As typical
- **all_my_cfnstacksets.py**
- **all_my_config_recorders_and_delivery_channels.py**
- **all_my_elbs.py**
- **all_my_functions.py**
- **all_my_gd-detectors.py**
- **all_my_instances.py**
- **all_my_orgs.py**
- **all_my_phzs.py**
- **all_my_roles.py**
- **all_my_saml_providers.py**
- **all_my_vpcs.py**
- **all_my_vpcs2.py**
- **del_my_cfnstacksets.py**
- **delete_bucket_objects.py**
- **my_org_users.py**
- **my_ssm_parameters.py**
