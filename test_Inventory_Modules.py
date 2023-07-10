from unittest import TestCase
from account_class import aws_acct_access
from Inventory_Modules import get_regions3
import datetime
import botocore.session
from botocore.stub import Stubber


# This requires a default method of authentication be already setup
aws_acct = aws_acct_access()


class TestGetRegions(TestCase):

	def test_get_regions3(self):
		regions = get_regions3(aws_acct, 'us-east-1')
		self.assertIn('us-east-1', regions)
		self.assertNotIn('us', regions)
		# self.fail()


s3 = botocore.session.get_session().create_client('s3')
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
service_response = s3.list_buckets()
with Stubber(s3) as stubber:
	stubber.add_response('list_buckets', response, {})
	service_response = s3.list_buckets()
