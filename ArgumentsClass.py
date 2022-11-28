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
	pRegionList = args.Regions
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
				prefix_chars='-+')

	def version(self):
		self.my_parser.add_argument(
				"--version",
				dest="Version",
				action="store_true",
				default="store_false",  # Defaults to not providing the version
				help="Version #")

	def rootOnly(self):
		self.my_parser.add_argument(
				"--rootonly",
				dest="RootOnly",
				action="store_true",  # Defaults to False, so the script would continue to run
				help="Only run this code for the root account, not the children")

	def verbosity(self):
		import logging
		self.my_parser.add_argument(
				'-v',
				help="Be verbose (Error Statements)",
				action="store_const",
				dest="loglevel",
				const=logging.ERROR,  # args.loglevel = 40
				default=logging.CRITICAL)  # args.loglevel = 50
		self.my_parser.add_argument(
				'-vv', '--verbose',
				help="Be MORE verbose (Warning statements)",
				action="store_const",
				dest="loglevel",
				const=logging.WARNING,  # args.loglevel = 30
				default=logging.CRITICAL)  # args.loglevel = 50
		self.my_parser.add_argument(
				'-vvv',
				help="Print INFO statements",
				action="store_const",
				dest="loglevel",
				const=logging.INFO,  # args.loglevel = 20
				default=logging.CRITICAL)  # args.loglevel = 50
		self.my_parser.add_argument(
				'-d', '--debug',
				help="Print debugging statements",
				action="store_const",
				dest="loglevel",
				const=logging.DEBUG,  # args.loglevel = 10
				default=logging.CRITICAL)  # args.loglevel = 50

	def extendedargs(self):
		# self.my_parser.add_argument(
		# 	"+forreal",
		# 	help="By default, we report results without changing anything. If you want to remediate or change your environment - include this parameter",
		# 	action="store_false",
		# 	dest="DryRun")              # Default to Dry Run (no changes)
		self.my_parser.add_argument(
			"--force", "+force",
			help="To force a change - despite indications to the contrary",
			action="store_true",
			dest="Force")  # Default to Dry Run (no changes)
		self.my_parser.add_argument(
			"-k", "-ka", "--skip", "--skipaccount",
			dest="SkipAccounts",
			nargs="*",
			metavar="Accounts to leave alone",
			default=[],
			help="These are the account numbers you don't want to screw with. Likely the core accounts.")
		self.my_parser.add_argument(
			"-kp", "--skipprofile",
			dest="SkipProfiles",
			nargs="*",
			metavar="Profile names",
			default=[],
			help="These are the profiles you don't want to examine. You can specify 'skipplus' to skip over all profiles using a plus in them.")
		self.my_parser.add_argument(
			"--timing", "--time",
			dest="Time",
			action="store_true",
			help="Use this parameter to add a timing for the scripts")

	def fragment(self):
		self.my_parser.add_argument(
			"-f", "--fragment",
			dest="Fragments",
			nargs='*',
			metavar="CloudFormation stack fragment",
			default=["all"],
			help="List of fragments of the cloudformation stackset(s) you want to check for.")

	def singleprofile(self):
		self.my_parser.add_argument(
				"-p", "--profile",
				dest="Profile",
				metavar="Profile",
				default=None,  # Default to boto3 defaults
				help="Which single profile do you want to run against?")

	def multiprofile(self):
		self.my_parser.add_argument(
				"-p", "-ps", "--profiles",
				dest="Profiles",
				nargs="*",
				metavar="Profiles",
				default=None,  # Defaults to default profile, but can support multiple profiles
				help="Which profiles do you want to run against?")

	def multiregion(self):
		self.my_parser.add_argument(
				"-rs", "--regions", "-r",
				nargs="*",
				dest="Regions",
				metavar="region name string",
				default=["us-east-1"],
				help="String fragment of the region(s) you want to check for resources. You can supply multiple fragments.")

	def multiregion_nodefault(self):
		self.my_parser.add_argument(
				"-r", "-rs", "--regions",
				nargs="*",
				dest="Regions",
				metavar="region name string",
				default=None,
				help="String fragment of the region(s) you want to check for resources. You can supply multiple fragments.")

	def singleregion(self):
		self.my_parser.add_argument(
				"-r", "--region",
				dest="Region",
				metavar="region name string",
				default="us-east-1",
				help="Name of the single region(s) you want to check for resources.")
