# Write Python3 code here
"""
How to use: 
	from ArgumentsClass import CommonArguments
	parser = CommonArguments()
	parser.extendedargs()
	parser.my_parser.add_argument(...
	< ... >
	< Add more arguments as you would like >
	< ... >
	args = parser.my_parser.parse_args()

	pProfile = args.Profile
	pRegionList = args.Region
	verbose = args.loglevel

"""


class CommonArguments():
	"""
	Class is created on the argparse class, and extends it for my purposes.
	"""

	def __init__(self):
		import argparse
		self.my_parser = argparse.ArgumentParser(
			description='Accept common arguments to the Inventory Scripts',
			allow_abbrev=True,
			prefix_chars='-+/')


	def singleprofile(self):
		self.my_parser.add_argument(
			"-p", "--profile",
			dest="Profile",
			metavar="Profile",
			default=None,               # Default to boto3 defaults
			help="Which single profile do you want to run against?")


	def verbosity(self):
		import logging
		self.my_parser.add_argument(
			'-v',
			help="Be verbose",
			action="store_const",
			dest="loglevel",
			const=logging.ERROR,        # args.loglevel = 40
			default=logging.CRITICAL)   # args.loglevel = 50
		self.my_parser.add_argument(
			'-vv', '--verbose',
			help="Be MORE verbose",
			action="store_const",
			dest="loglevel",
			const=logging.WARNING,      # args.loglevel = 30
			default=logging.CRITICAL)   # args.loglevel = 50
		self.my_parser.add_argument(
			'-vvv',
			help="Print debugging statements",
			action="store_const",
			dest="loglevel",
			const=logging.INFO,         # args.loglevel = 20
			default=logging.CRITICAL)   # args.loglevel = 50
		self.my_parser.add_argument(
			'-d', '--debug',
			help="Print LOTS of debugging statements",
			action="store_const",
			dest="loglevel",
			const=logging.DEBUG,        # args.loglevel = 10
			default=logging.CRITICAL)   # args.loglevel = 50


	def extendedargs(self):
		# self.my_parser.add_argument(
		# 	"+forreal",
		# 	help="By default, we report results without changing anything. If you want to remediate or change your environment - include this parameter",
		# 	action="store_false",
		# 	dest="DryRun")              # Default to Dry Run (no changes)
		self.my_parser.add_argument(
			"--force",
			help="To force a change - despite indications to the contrary",
			action="store_true",
			dest="Force")              # Default to Dry Run (no changes)
		self.my_parser.add_argument(
			"-k", "--skip",
			dest="SkipAccounts",
			nargs="*",
			metavar="Accounts to leave alone",
			default=[],
			help="These are the account numbers you don't want to screw with. Likely the core accounts.")


	def multiprofile(self):
		self.my_parser.add_argument(
			"-ps", "-p", "--profiles",
			dest="Profiles",
			nargs="*",
			metavar="Profiles",
			default=['all'],               # Defaults to all profiles
			help="Which profiles do you want to run against?")

	def multiregion(self):
		self.my_parser.add_argument(
			"-rs", "--regions",
			nargs="*",
			dest="Regions",
			metavar="region name string",
			default=["us-east-1"],
			help="String fragment of the region(s) you want to check for resources. You can supply multiple fragments.")


	def singleregion(self):
		self.my_parser.add_argument(
			"-r", "--region",
			dest="Region",
			metavar="region name string",
			default="us-east-1",
			help="Name of the single region(s) you want to check for resources.")
