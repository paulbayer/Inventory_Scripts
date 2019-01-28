"""
 Copyright 2018 Amazon.com, Inc. and its affiliates. All Rights Reserved.
 
 Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance with the License.
 A copy of the License is located at

  http://aws.amazon.com/asl/

 or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 express or implied. See the License for the specific language governing permissions and limitations under the License.
"""

import boto3
import logging
import re
import argparse

from colorama import init,Fore,Back,Style
from collections import OrderedDict
from botocore.exceptions import ClientError

logger = logging.getLogger()
session = boto3.session.Session()
default_assume_role_name = 'AWSCloudFormationStackSetExecutionRole'
assume_role_name = default_assume_role_name
dry_run = True
stacks_to_delete = []
stackset_associations = []
fmt='%-12s | %-10s | %-50s | %-25s | %-50s'



def list_detectors(client, aws_region):
    """
    Lists the detectors in a given Account/Region
    Used to detect if a detector exists already
    :param client: GuardDuty client
    :return: list of Detectors
    """

    detector_dict = client.list_detectors()

    if detector_dict['DetectorIds']:
        for detector in detector_dict['DetectorIds']:
            detector_dict.update({aws_region:detector})
    else:
        detector_dict.update({aws_region: ''})

    return detector_dict



def list_members(client, detector_id):

    member_dict = dict()

    response = client.list_members(
        DetectorId=detector_id,
        OnlyAssociated='false'
    )

    for member in response['Members']:
        member_dict.update({member['AccountId']:member['RelationshipStatus']})

    return member_dict



def assume_role(aws_account_number, role_name):
    """
    Assumes the provided role in each account and returns a GuardDuty client
    :param aws_account_number: AWS Account Number
    :param role_name: Role to assume in target account
    :param aws_region: AWS Region for the Client call, not required for IAM calls
    :return: GuardDuty client in the specified AWS Account and Region
    """

    # Beginning the assume role process for account
    sts_client = boto3.client('sts')
    
    # Get the current partition
    partition = sts_client.get_caller_identity()['Arn'].split(":")[1]
    
    response = sts_client.assume_role(
        RoleArn='arn:{}:iam::{}:role/{}'.format(
            partition,
            aws_account_number,
            role_name
        ),
        RoleSessionName='EnableGuardDuty'
    )
    
    # Storing STS credentials
    session = boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken']
    )

    print("Assumed session for {}.".format(
        aws_account_number
    ))

    return session



def find_stacksets(aws_region, stack_fragment):
    """
    Looks for CloudFormation stack sets based on a provided string fragment.
    :param stack_fragment: CloudFormation stack name fragment to search for
    :param aws_region: AWS Region for the Client call, not required for IAM calls
    :return: Stacksets in the specified Region
    """

    logging.info("Region: %s | Fragment: %s", aws_region, stack_fragment)
    
    cf_client = session.client('cloudformation', region_name=aws_region)

    all_stacksets = cf_client.list_stack_sets(Status='ACTIVE')
    filtered_stacksets=[]
	
    if stack_fragment == 'all' or stack_fragment == 'ALL' or stack_fragment == 'All':
	    logging.info("Found all the stacksets in Region: %s with Fragment: %s", aws_region, stack_fragment)
	    return all_stacksets['Summaries']
    else:
        for stack in all_stacksets['Summaries']:
            if stack_fragment in stack['StackSetName']:
                logging.info("Found stackset %s in Region: %s with Fragment: %s", stack['StackSetName'], aws_region, stack_fragment)
                filtered_stacksets.append(stack)

    return filtered_stacksets



def find_stacks_in_acct(account, aws_region, stack_fragment):
    """
    Looks for CloudFormation stacks within an account based on a provided string fragment.
    :param account: Account to search for the stacks
    :param aws_region: AWS Region for the Client call
    :param stack_fragment: CloudFormation stack name fragment to search for
    :return: Stacksets in the specified Region
    """

    session = assume_role(account, assume_role_name)
    cf_client = session.client('cloudformation', region_name=aws_region)
    
    logging.warning("Region: %s | Fragment: %s | Status: %s", aws_region, stack_fragment, "Active")
	
    stacks_list = []

    # Send back stacks that are active, check the fragment further down.
    stacks = cf_client.list_stacks(StackStatusFilter = ["CREATE_COMPLETE","UPDATE_COMPLETE","UPDATE_ROLLBACK_COMPLETE","DELETE_FAILED"])
    
    for stack in stacks['StackSummaries']:
        if stack_fragment in stack['StackName']:
            # Check the fragment now - only send back those that match
            logging.info("Found stack %s in Region: %s with Fragment: %s and Status: %s", stack['StackName'], aws_region, stack_fragment, "Active")
            stacks_list.append(stack)
	
    return stacks_list 



def delete_stacks(stackset_instances, stack_fragment):
    """
    Deletes CloudFormation stacks within accounts associated with a stackset.
    :param stackset_instances: CloudFormation stackset instances associated with a stackset
    :param stack_fragment: CloudFormation stack name fragment to search for
    :return instance_accounts: account list associated with the stackset instances
    :return instance_regions: region list associated with the stackset instances
    """
    
    instance_accounts = set()
    instance_regions = set()
    
    if len(stackset_instances['Summaries']) > 0:

        for sa in stackset_instances['Summaries']:
            stacks_list = find_stacks_in_acct(sa['Account'], sa['Region'], stack_fragment)
            instance_accounts.add(sa['Account'])
            instance_regions.add(sa['Region'])

            if len(stacks_list) > 0:
                #print("Stacks List: " + str(stacks_list))

                for stack in stacks_list:
                    #print("Stack: " + str(stack))
                    
                    if not dry_run:
                        temp_session = assume_role(sa['Account'], assume_role_name)
                        cfn_client = temp_session.client('cloudformation', region_name=sa['Region'])
                        response = cfn_client.delete_stack(StackName=stack['StackName'])

                        #print("Delete Stack Response: " + str(response))
                        print("Deleted stack {} in account {} in region {}".format(stack['StackName'], sa['Account'], sa['Region']))
                    else:
                        print("DryRun is enabled, so the stack was NOT DELETED in account {} in region {} called {}".format (sa['Account'], sa['Region'], stack['StackName']))
            
    return instance_accounts, instance_regions
    


def delete_stack_instances(stackset_name, account_list, region_list):
    """
    Deletes CloudFormation stackset instances .
    :param stackset_name: CloudFormation stackset name
    :param account_list: CloudFormation stack instance accounts
    :param region_list: CloudFormation stack instance regions
    """
    
    if len(list(account_list)) > 0 and len(list(region_list)) > 0:
        if not dry_run:
            cf_client = session.client('cloudformation')
            response = cf_client.delete_stack_instances(
                        StackSetName = stackset_name,
                        Accounts = list(account_list),
                        Regions = list(region_list),
                        RetainStacks = False
                    )
                
            print("StackSet Instances Deleted - StackSet Name: {stackset} - Accounts: {accounts} - Regions: {regions}".format(stackset=stackset_name, accounts=str(account_list), regions=str(region_list)))
        else:
            print("StackSet Instances NOT DELETED - StackSet Name: {stackset} - Accounts: {accounts} - Regions: {regions}".format(stackset=stackset_name, accounts=str(account_list), regions=str(region_list)))



def delete_stacksets(aws_region, stack_fragment):
    """
    Deletes CloudFormation stacksets within an account based on a provided string fragment.
    :param aws_region: AWS Region for the Client call
    :param stack_fragment: CloudFormation stack name fragment to search for
    """
    
    cf_client = session.client('cloudformation')
    stacksets = find_stacksets(aws_region, stack_fragment)

    for stackset in stacksets:
        stackset_instances = cf_client.list_stack_instances(StackSetName=stackset['StackSetName'])
        
        #print("StackSet Instances: " + str(stackset_instances))
        logging.info("Stackset: %s has %s associations" % (stackset['StackSetName'], len(stackset_instances['Summaries'])))
        
        instance_accounts, instance_regions = delete_stacks(stackset_instances, stack_fragment)
        delete_stack_instances(stackset['StackSetName'], instance_accounts, instance_regions)
        
        if len(stackset_instances['Summaries']) == 0:
            if not dry_run:
                response = cf_client.delete_stack_set(StackSetName = stackset['StackSetName'])  
                logging.info("Stackset %s was deleted." % (stackset['StackSetName']))
            else: 
                logging.info("Dry run is True and stackset was NOT DELETED.")
        else:
            logging.warning("Stackset %s has associations and cannot be deleted. Wait for the associations to finish deleting and then re-run the script." % (stackset['StackSetName']))



def delete_detectors(master_session, guardduty_regions, organization_accounts, delete_master):
    """
    Deletes GuardDuty Detectors in all accounts and regions
    :param master_session: boto3 session using the master account
    :param guardduty_regions: All GuardDuty regions
    """
    
    for aws_region in guardduty_regions:
        gd_client = master_session.client('guardduty', region_name=aws_region)

        detector_dict = list_detectors(gd_client, aws_region)
        detector_id = detector_dict[aws_region]

        if detector_id != '':
            print('GuardDuty is active in {region}'.format(region=aws_region))

        if detector_id != '':
            member_dict = list_members(gd_client, detector_id)
            
            if member_dict:
                print('There are members in {region}'.format(region=aws_region))
                
                if delete_master and not dry_run:
                    
                    response = gd_client.disassociate_members(
                        AccountIds=list(member_dict.keys()),
                        DetectorId=detector_id
                    )
                    
                    response = gd_client.delete_members(
                        DetectorId=detector_id,
                        AccountIds=list(member_dict.keys())
                    )
                    
                elif not dry_run:
                    response = gd_client.disassociate_members(
                        AccountIds=organization_accounts,
                        DetectorId=detector_id
                    )
                    
                    response = gd_client.delete_members(
                        DetectorId=detector_id,
                        AccountIds=organization_accounts
                    )
                
                print('Deleting members for {account} in {region}'.format(
                    account=args.master_account,
                    region=aws_region
                ))
    
            if delete_master and not dry_run:
                response = gd_client.delete_detector(
                    DetectorId=detector_id
                )
        else:
            print('No detector found for {account} in {region}'.format(
                account=args.master_account,
                region=aws_region
            ))

    failed_accounts = []
    for account_str in organization_accounts:
        try:
            session = assume_role(account_str, args.assume_role)
            
            for aws_region in guardduty_regions:
                gd_client = session.client('guardduty', region_name=aws_region)
    
                detector_dict = list_detectors(gd_client, aws_region)
                detector_id = detector_dict[aws_region]
    
                if detector_id != '':
                    print('GuardDuty is active in {region}'.format(region=aws_region))
    
                if detector_id != '' and not dry_run:
                    response = gd_client.delete_detector(
                        DetectorId=detector_id
                    )
                    
                    print('Deleted {detector} for {account} in {region}.'.format(
                        detector=detector_id,
                        account=account_str,
                        region=aws_region
                    ))
                    
                else:
                    print('No detector found for {account} in {region}'.format(
                        account=account_str,
                        region=aws_region
                    ))
        except ClientError as e:
            print("Error Processing Account {}".format(account_str))
            failed_accounts.append({
                account_str: repr(e)
            })
    
    if len(failed_accounts) > 0:
        print("---------------------------------------------------------------")
        print("Failed Accounts")
        print("---------------------------------------------------------------")
        for account in failed_accounts:
            print("{}: \n\t{}".format(
                account.keys()[0],
                account[account.keys()[0]]
            ))
            print("---------------------------------------------------------------")



if __name__ == '__main__':
    
    # Setup command line arguments
    parser = argparse.ArgumentParser(description='Link AWS Accounts to central GuardDuty Account')
    parser.add_argument('--master_account', type=int, required=True, help="AccountId for Central AWS Account")
    parser.add_argument('--assume_role', type=str, required=True, default=default_assume_role_name,  help="Role Name to assume in each account")
    parser.add_argument('--delete_master', action='store_true', default=False, help="Delete the master Gd Detector")
    parser.add_argument('--enabled_regions', type=str, help="Comma separated list of regions to remove GuardDuty. If not specified, all available regions disabled")
    parser.add_argument("-f","--fragment", dest="pstackfrag", type=str, metavar="CloudFormation GuardDuty stack fragment", default="GuardDuty", help="List containing fragment(s) of the cloudformation stack or stackset(s) you want to check for.")
    parser.add_argument('-v', '--verbose', help="Be verbose. Logging level set to INFO", action="store_const", dest="loglevel", const=logging.INFO)
    parser.add_argument('--forreal','--forrealsies', help="Do a Dry-run; don't delete anything", action="store_const", const=False, default=True, dest="DryRun")
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    dry_run = args.DryRun
    stackset_fragment = args.pstackfrag
    assume_role_name = args.assume_role
    master_account = args.master_account

    print("Dry Run = " + str(dry_run))
    print("Stackset Fragment: " + stackset_fragment)
    
    # Validate master accountId
    if not re.match(r'[0-9]{12}',str(args.master_account)):
        raise ValueError("Master AccountId is not valid")

    master_session = assume_role(master_account, assume_role_name)

    # Organization accounts
    organization_accounts = []
    org_client = master_session.client('organizations')

    accts = org_client.list_accounts()
    for acct in accts['Accounts']:
        organization_accounts.append(str(acct['Id']))
    
    print("Accounts: " + str(organization_accounts))
    
    # Getting GuardDuty regions
    guardduty_regions = []
    if args.enabled_regions:
        guardduty_regions = [str(item) for item in args.enabled_regions.split(',')]
    else:
        guardduty_regions = session.get_available_regions('guardduty')
            
    for aws_region in guardduty_regions:
        delete_stacksets(aws_region, stackset_fragment)

    
    # Double check that all the GuardDuty detectors have been deleted
    master_session = assume_role(master_account, assume_role_name)
    delete_detectors(master_session, guardduty_regions, organization_accounts, args.delete_master)