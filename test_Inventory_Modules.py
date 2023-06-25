from unittest import TestCase
from account_class import aws_acct_access
from Inventory_Modules import get_regions3


# This requires a default method of authentication be already setup
aws_acct = aws_acct_access()


class TestGetRegions(TestCase):

	def test_get_regions3(self):
		regions = get_regions3(aws_acct, 'us-east-1')
		self.assertIn('us-east-1', regions)
		self.assertNotIn('us', regions)
		# self.fail()
