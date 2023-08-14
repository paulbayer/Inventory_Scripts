# test_all_my_orgs.py

import unittest
import boto3

from unittest import mock
from Inventory_Modules import get_profiles
from all_my_orgs import main
# from moto import mock_organizations

class TestAllMyOrgs(unittest.TestCase):

    @mock.patch('boto3.client')
    def test_get_profiles_default(self, mock_boto3_client):
        # Mock the boto3.client to prevent actual AWS calls
        expected_response = ['Secondary', 'RIV21-1', 'LZRoot', 'NonOrgTest', 'default', 'Org-Parent', 'NonOrgAcct', 'CT-RIV20', 'Primary', 'LZ1', 'CT-AppAcct1', 'LZ3', 'MirrorWorld']
        mock_boto3_client.return_value.get_profiles.return_value = expected_response

        response = get_profiles()

        self.assertCountEqual(response, expected_response)
        # mock_boto3_client.assert_called_once_with('')
        # mock_boto3_client.return_value.get_profiles.assert_called_once()

    @mock.patch('boto3.client')
    def test_get_profiles_LZ1(self, mock_boto3_client):
        # Mock the boto3.client to prevent actual AWS calls
        expected_response = ['LZ1']
        mock_boto3_client.return_value.get_profiles.return_value = expected_response

        pProfiles = ['LZ']
        pSkipProfiles = ['LZ3', 'LZRoot']
        response = get_profiles(pSkipProfiles, pProfiles)

        self.assertCountEqual(response, expected_response)
        mock_boto3_client.assert_called_once_with(pSkipProfiles, pProfiles)
        mock_boto3_client.return_value.get_profiles.assert_called_once_with(pSkipProfiles, pProfiles)
        print()


@mock_organizations
def test_all_my_orgs():
    test_client = boto3.client('organizations', region_name='us-east-1')
    test_output = main()
    print()


test_all_my_orgs()
print()
