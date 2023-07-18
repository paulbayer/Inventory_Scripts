from unittest import TestCase
from account_class import aws_acct_access
from Inventory_Modules import get_regions3
import datetime
from botocore.stub import Stubber



# This requires a default method of authentication be already setup
aws_acct = aws_acct_access()


class TestGetRegions(TestCase):

	def test_get_regions3(self):
		regions = get_regions3(aws_acct, 'us-east-1')
		self.assertIn('us-east-1', regions)
		self.assertNotIn('us', regions)
		# self.fail()


def test_list_objects():

	s3 = aws_acct.session.create_client('s3')

	response = {
	    "Owner": {
	        "ID": "foo",
	        "DisplayName": "bar"
	    },
	    "Buckets": [{
	        "CreationDate": datetime.datetime(2016, 1, 20, 22, 9),
	        "Name": "baz"
	    }]
	}


	with Stubber(s3) as stubber:
		stubber.add_response('list_buckets', response, {})
		service_response = s3.list_buckets()

	assert service_response == response

def test_get_regions3(faws_acct, fregion_list=None):
def test_get_ec2_regions(fprofile=None, fregion_list=None):
def test_get_ec2_regions3(faws_acct, fkey=None):
def test_get_service_regions(service, fkey=None, fprofile=None, ocredentials=None, faws_acct=None):
def test_validate_region3(faws_acct, fRegion=None):
def test_get_profiles(fSkipProfiles=None, fprofiles=None):
def test_find_in(list_to_search, list_to_find=None):
def test_find_bucket_location(fProfile, fBucketname):
def test_find_acct_email(fOrgRootProfile, fAccountId):
def test_find_account_number(fProfile=None):
def test_find_calling_identity(fProfile):
def test_RemoveCoreAccounts(MainList, AccountsToRemove=None):
def test_make_creds(faws_acct):
def test_get_child_access(fRootProfile, fChildAccount, fRegion='us-east-1', fRoleList=None):
def test_get_child_access3(faws_acct, fChildAccount, fRegion='us-east-1', fRoleList=None):
def test_enable_drift_on_stacks2(ocredentials, fRegion, fStackName):
def test_enable_drift_on_stack_set(ocredentials, fRegion, fStackSetName):
def test_find_sns_topics2(ocredentials, fRegion, fTopicFrag=None):
def test_find_role_names2(ocredentials, fRegion, fRoleNameFrag=None):
def test_find_cw_log_group_names2(ocredentials, fRegion, fCWLogGroupFrag=None):
def test_find_org_services2(ocredentials, serviceNameList=None):
def test_disable_org_service2(ocredentials, serviceName=None):
def test_find_account_vpcs2(ocredentials, defaultOnly=False):
def test_find_account_vpcs3(faws_acct, fRegion, defaultOnly=False):
def test_find_config_recorders2(ocredentials, fRegion):
def test_del_config_recorder2(ocredentials, fRegion, fConfig_recorder_name):
def test_find_delivery_channels2(ocredentials, fRegion):
def test_del_delivery_channel2(ocredentials, fRegion, fDelivery_channel_name):
def test_del_config_recorder_or_delivery_channel2(deletion_item):
def test_find_cloudtrails2(ocredentials, fRegion, fCloudTrailnames=None):
def test_del_cloudtrails2(ocredentials, fRegion, fCloudTrail):
def test_find_gd_invites2(ocredentials, fRegion):
def test_delete_gd_invites2(ocredentials, fRegion, fAccountId):
def test_find_account_instances2(ocredentials, fRegion='us-east-1'):
def test_find_cw_groups_retention2(ocredentials, fRegion='us-east-1'):
def test_find_account_rds_instances2(ocredentials, fRegion='us-east-1'):
def test_find_account_cloudtrail2(ocredentials, fRegion='us-east-1'):
def test_find_account_subnets2(ocredentials, fRegion='us-east-1', fipaddresses=None):
def test_find_account_enis2(ocredentials, fRegion=None, fipaddresses=None):
def test_find_account_volumes2(ocredentials):
def test_find_account_policies2(ocredentials, fRegion='us-east-1', fFragments=None, fExact=False):
def test_find_account_policies3(faws_acct, fRegion='us-east-1', fFragments=None):
def test_find_policy_action(ocredentials, fpolicy, f_action):
def test_find_users2(ocredentials):
def test_find_profile_vpcs(fProfile, fRegion, fDefaultOnly):
def test_find_profile_functions(fProfile, fRegion):
def test_find_lambda_functions2(ocredentials, fRegion='us-east-1', fSearchStrings=None):
def test_find_lambda_functions3(faws_acct, fRegion='us-east-1', fSearchStrings=None):
def test_get_lambda_code_url(fprofile, fregion, fFunctionName):
def test_find_directories2(ocredentials, fRegion='us-east-1', fSearchStrings=None):
def test_find_directories3(faws_acct, fRegion='us-east-1', fSearchStrings=None):
def test_find_private_hosted_zones(fProfile, fRegion):
def test_find_private_hosted_zones2(ocredentials, fRegion=None):
def test_find_private_hosted_zones3(faws_acct, fRegion=None):
def test_find_load_balancers(fProfile, fRegion, fStackFragment='all', fStatus='all'):
def test_find_load_balancers3(faws_acct, fRegion='us-east-1', fStackFragments=None, fStatus='all'):
def test_find_stacks(fProfile, fRegion, fStackFragment="all", fStatus="active"):
def test_find_stacks2(ocredentials, fRegion, fStackFragment=None, fStatus=None):
def test_find_stacks3(faws_acct, fRegion, fStackFragment="all", fStatus="active"):
def test_delete_stack(fprofile, fRegion, fStackName, **kwargs):
def test_delete_stack2(ocredentials, fRegion, fStackName, **kwargs):
def test_find_stacks_in_acct3(faws_acct, fRegion, fStackFragment="all", fStatus="active"):
def test_find_saml_components_in_acct2(ocredentials, fRegion):
def test_find_stacksets2(ocredentials, fRegion='us-east-1', fStackFragment=None, fStatus=None):
def test_find_stacksets3(faws_acct, fRegion=None, fStackFragment=None, fExact=False):
def test_delete_stackset(fProfile, fRegion, fStackSetName):
def test_delete_stackset3(faws_acct, fRegion, fStackSetName):
def test_find_stack_instances(fProfile, fRegion, fStackSetName, fStatus='CURRENT'):
def test_find_stack_instances2(ocredentials, fRegion, fStackSetName, fStatus='CURRENT'):
def test_find_stack_instances3(faws_acct, fRegion, fStackSetName, fStatus='CURRENT'):
def test_check_stack_set_status3(faws_acct, fStack_set_name, fOperationId=None):
def test_find_if_stack_set_exists3(faws_acct, fStack_set_name):
def test_find_sc_products(fProfile, fRegion, fStatus="ERROR", flimit=100):
def test_find_sc_products3(faws_acct, fStatus="ERROR", flimit=100, fproductId=None):
def test_find_ssm_parameters(fProfile, fRegion):
def test_find_ssm_parameters2(ocredentials):
def test_find_ssm_parameters3(faws_acct, fregion=None):
def test_display_results(results_list, fdisplay_dict, defaultAction=None, file_to_save=None):
def test_get_all_credentials(fProfiles=None, fTiming=False, fSkipProfiles=None, fSkipAccounts=None, fRootOnly=False, fAccounts=None, fRegionList=None, RoleList=None):
def test_get_credentials_for_accounts_in_org(faws_acct, fSkipAccounts=None, fRootOnly=False, accountlist=None, fprofile="default", fregions=None, fRoleNames=None, fTiming=False):
def test_get_org_accounts_from_profiles(fProfileList, progress_bar=False):
