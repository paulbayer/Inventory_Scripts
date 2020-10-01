Project Overview
================
Inventory_Scripts is a git repository to aggregate a number of scripts I've written, with the intent to make it easier to keep track of what's created and/ or running in any one of your (possibly) many AWS accounts... The scripts in this repo are discussed below.

***Note***:  *The tools I've written here have grown organically. They're presented below in an order I thought made sense, but they were definitely not created all at once, nor all kept up to the same level of perfection. I started this journey back in 2017 when there was no such thing as the Landing Zone, and Federation wasn't as prevalent a thing, so I assumed everyone would have profiles for every account they managed. Fast-forward to 2019 and we realize that most admin is done by authenticating to one account and using cross-account roles to authorize to other Child accounts. Hence - some of these files still work by profile, but I'm slowly moving everything over to being able to work with a Federated model. I still haven't baked in MFA token stuff, but I think I might just rely on the OS for that in the short term.*

***Note***: *I've tried to make the "verbose" and "debugging" options standard across all of the scripts. Apologies if they're not.*

***Note***: *I've also made this repo available at https://github.com/paulbayer/Inventory_Scripts for customers.*

Common Parameters
------------------
  - -v for some additional logging (level: ERROR)
    - For those times when I decided to show less information on screen, to keep the output neat - you could use this level of logging to get what an interested user might want to see.
  - -vv for even more logging (level: WARNING)
    - You could use this level of logging to get what a developer might want to see.
  - -d for lots of logging (level: INFO)
    - This is generally the lowest level I would recommend anyone use.
  - -dd for crazy amount of logging (level: DEBUG)
    - I would avoid the "debug" level because Python itself tends to bombard you with so much screen-spam that it's not useful. I've used DEBUG level for when I was writing the code and needed to debug it myself.

Additional common parameters:
------------------
  - -h: Provide "-h" or "--help" on the command line and get a nicely formatted screen that describes all possible parameters.
  - -p: to specify the profile which the script will work with. In most cases, this could/ should be a Master Profile, but doesn't always have to be.
  - -r: to specify the region for the script to work in. Most scripts take "all" as a valid parameter. Most scripts also assume "us-east-1" as a default if nothing is specified. Also note - you can specify a fragment here - so you can specify "us-east" and get both "us-east-1" and "us-east-2". Specify "us-" and you'll get all four "us-" regions.
  - -f: string fragment - some scripts (specifically ones dealing with CFN stacks and stacksets) take a parameter that allows you to specify a fragment of the stack name, so you can find that stack you can't quite remember the whole name of.


Purpose Built Scripts
------------------
- **ALZ_CheckAccount.py**
  - This script takes an Organization Master Account profile, and checks additional accounts to see if they meet the pre-reqs to be "adopted" by either Landing Zone or Control Tower.
  - If there are blockers to the adoption (like the default VPCs being present, or Config Recorder already being enabled), it can rectify those blockers it finds. However - to avoid mistakes - it only does this if you specifically select that in the submitted parameters.
  - While this script was focused on ALZ, it also *sort of* supports an account being adopted by Control Tower too.

- **CT_CheckAccount.py**
  - This script takes an Organization Master Account profile, and checks additional accounts to see if they meet the pre-reqs to be "adopted" by Control Tower.
  - If there are blockers to the adoption (like the Config Recorder already being enabled), it can rectify those blockers it finds. However - to avoid mistakes - it only does this if you specifically select that in the submitted parameters. This script is still being worked on.

- **RegistrationScript.py**
  - This script goes through an Organization and determines (based on roles) whether the account has been on-boarded to the AWS Federation tool or not. If not, it creates a temporary user ("Alice") and prints the information to the screen to be able to register the account to the tool.

- **SC_Products_to_CFN_Stacks.py**
  - This script is focused on reconciling the SC Products with the CFN Stacks they create. It definitely can happen that a CFN stack can exist without a corresponding SC Product, and it can happen that an SC Product can exist without a corresponding CFN stack (I'm looking at you AWS Control Tower!). However, when an SC Product is in ERROR state and the CFN stack is in an error state - you're best served by terminating the SC Product and starting over. This script can help you find those instances and even offers to get rid of them for you.
- **del_enable_config.template.py**
  - This script was specifically created to remove the resources created during the "Enable Config" stack through the ALZ. Since this stack enables the Config Recorder, Delivery Channel, SNS Topic, Lambda Function, and SNS Notification Forwarder; all of these resources can be removed with this script.


  Generic Scripts
  ------------------
- **all_my_cfnstacks.py**
  - The objective of this script is to find that CloudFormation stack you know you created in some account within your Organization - but you just can't remember which one (and God forbid - in which region!). So here you can specify a stack fragment, and a region fragment and the script will search through all accounts within your Org (assuming you provided a profile of the Master Account-with appropriate rights) in only those regions that match your fragment, and find the stacks that match the fragment you provided.
  - If you provide the "+delete" parameter - it will DELETE those stacks WITHOUT ADDITIONAL CONFIRMATION! So please be careful about using this.
  - GuardDuty stacks sometimes need more care and feeding, so there's a special section in this script to handle those. It's a bit hard-coded (we expect that 'GuardDuty' was specified in its entirety in the fragment), but we'll fix that eventually.
- **all_my_cfnstacksets.py**
  - The objective of this script is to find those CloudFormation StackSets you know you created in some account within your Organization - but you just can't remember which one.
- **all_my_config_recorders_and_delivery_channels.py**
  - I wrote this script to help remove the Config Recorders and Delivery Channels for a given account, so that we could use this within the "adoption" of legacy accounts into the AWS Landing Zone.
  - Now that we have the ALZ_CheckAccount tool, I don't see a lot of use from this script, but it's complete - so why delete it?
- **mod_my_cfnstacksets.py**
  - So, originally, when I was creating this library, I had the idea that I would create scripts that found resources - and different scripts that deleted those resources. Hence - both the "all_my_cfnstacksets" as well as "del_my_cfnstacksets". However, I quickly realized that you had to do the finding before you could do the deleting - so I decided to put more effort into the "del\*" tool instead of the "find\*" tool. Of course - then I realized that having the "deletion" be action in the find script made way more sense, so I tried to put everything I had done from one script into the other. At the end of it all - I had a mish-mash of useful and stale features in both scripts.

  - The truth is that I need to go through this script and make sure everything useful here has gotten into the "all_my_cfnstacksets.py" script and simply move forward with that one only. Still a work in progress, I guess.
- **all_my_elbs.py**
  - The objective of this script was to find all the various Load Balancers created in various accounts within your org.
- **all_my_functions.py**
  - The objective of this script was to find all the various Lambda functions you've created and left in various accounts.
- **all_my_gd-detectors.py**
  - This script was created to help remove all the various GuardDuty pieces that are created when GuardDuty is enabled in an organization and its children. Trying to remove all the pieces by hand is crazy, so this script is really long and complex - but it does the job well.
- **all_my_instances.py**
  - The objective of this script is to find all the EC2 instances available within your accounts and regions. The script can accept 1 or more profiles. If you specify a profile representing a Master Account - the script will assume you mean the entire organization, instead of just that one account - and will try to find all instances for all accounts within that Org.
- **all_my_orgs.py**
  - I use this script almost every day. In its default form with no parameters provided - it will go through all of your profiles and find all the Master Accounts you may have access to - and list out all the accounts under all of the Master Accounts it can find.
  - If you provide a profile using the "-p" parameter, it will determine if that profile is a Master and only list out the accounts within that Org.
  - If you provide a profile (using the "-p" parameter) which is not a Master Account, it will admonish you and go through all of your profiles, assuming you _meant_ to provide a Root Profile.
  - If you provide one or more profiles using the "-l" parameter, it will limit its investigation to just those profiles and give you whatever information it can about those. If you provide a "Child" account, it won't give much information - since it's not available. But this way you can provide a list of Root Profiles (assuming you have proper access to all of them) and it will give you the necessary info about each.
  - There are two additional parameters which are useful:
    - "-R" for listing only the root profiles it can find
    - "-s" for listing only the short form of the output
- **all_my_phzs.py**
  - The objective of this script is to find all of the Private Hosted Zones in a cross-account fashion.
  - This is one of the older scripts that only worked by profile. I still need to fix this one up to use the "account" method instead of just looking through matching profiles.
- **all_my_roles.py**
  - The objective of this script is to find all the roles within the accounts it looks through.
  - There are most common use cases for this script:
    - "In which account did I put that role?" (you'd have to use 'grep', since I didn't update this to take a string fragment - yet)
- **all_my_saml_providers.py**
  - The objective of this script is to find all Identity Providers within your accounts within your org.
  - There is also the capability to delete these idps - but I don't see people doing that all that often.
- **all_my_vpcs.py**
  - The objective of this script is to find all the vpcs within your set of accounts - as determined by your profiles. This script has been superseded by the "all_my_vpcs2.py" since this script only looked in the specific profile you supplied.
- **all_my_vpcs2.py**
  - The objective of this script is to find all the vpcs within your set of accounts - as determined by your Master Account's list of children. This script obsoletes the previous "all_my_vpcs.py" as this script can look at your whole Org, instead of only the single profile you specify.
  - You can also specify "--default" to limit your searching to only default VPCs.
- **delete_bucket_objects.py**
  - This is a tool that should delete buckets and the objects in them. I didn't write the original script, but I've been adapting it to my needs. This one should be considered alpha.
- **my_org_users.py**
  - The objective of this script is to go through all of your child accounts within an Org and pull out any IAM users you have - to ensure it's only what you expect.
- **my_ssm_parameters.py**
  - The objective of this script was two fold -
    - One is to just list out your SSM Parameters, so you know how many and which ones you have.
    - The other is to resolve a problem that exists with the AWS Landing Zone tool - which creates Parameter Store entries and doesn't clean them up when needed. Since the Parameter Store has a limit of 10,000 entries - some sophisticated, long-time customers could hit this limit and be frustrated by the inability to easily remediate this acknowledged bug.
      - This script can solve that problem by using the "--ALZ" parameter and the "-b" parameter to identify any left-over parameters that should be cleaned up since so many days back (ideally further back than your last successful Pipeline run).
    - As usual - provide the "+delete" parameter to allow the script to programmatically remediate the problem.

Utility Files
----------------
- **Inventory_Modules.py**
  - This is the "utils" file that is referenced by nearly every other script I've written. I didn't know Python well enough when I started to know that I should have named this "utils". If I get ambitious, maybe I'll go through and rename it within every script.
- **vpc_modules.py**
  - This is another "utils" collection, generally specific to the "ALZ_CheckAccount" script as well as the all_my_vpcs(2).py script, because all of the VPC deletion functions are in this library file. Props to
