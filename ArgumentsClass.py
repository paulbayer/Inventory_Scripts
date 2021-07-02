# Write Python3 code here
"""
class car():
	# init method or constructor
	def __init__(self, model='hyundai', color='white'):
		self.model = model
		self.color = color

	def show(self):
		print("Model is", self.model)
		print("color is", self.color)

# both objects have different self which
# contain their attributes
audi = car("audi a4", "blue")
ferrari = car("ferrari 488", "green")
audi.show()  # same output as car.show(audi)
ferrari.show()  # same output as car.show(ferrari)

ford = car()
ford.drivetrain = '4x4'
ford.show()
print(ford.drivetrain)
"""

"""
How to use: 
	from ArgumentsClass import CommonArguments
	parser = CommonArguments().my_parser
	< ... >
	< Add more arguments as you would like >
	< ... >
	args = parser.parse_known_args()[0]

	pProfile = args.pProfile
	pRegionList = args.pRegion
	verbose = args.loglevel

"""


class CommonArguments():
	"""
	Class is created on the argparse class, and extends it for my purposes.
	"""

	def __init__(self):
		import logging
		import argparse
		self.my_parser = argparse.ArgumentParser(
			description='Accept common arguments to the Inventory Scripts',
			prog='python',
			allow_abbrev=True,
			prefix_chars='-+/')
		self.my_parser.add_argument(
			"-p", "--profile",
			dest="Profile",
			metavar="Profile",
			default=None,               # Default to boto3 defaults
			help="Which profile do you want to run against?")
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
		# self.args = self.my_parser.parse_args()

	def extendedargs(self):
		self.my_parser.add_argument(
			"-n", "--dryrun",
			help="To report on results without changing anything",
			action="store_false",
			dest="DryRun")              # Default to Dry Run (no changes)
		self.my_parser.add_argument(
			"--force",
			help="To force a change - despite indications to the contrary",
			action="store_true",
			dest="Force")              # Default to Dry Run (no changes)
		self.my_parser.add_argument(
			"-r", "--region",
			nargs="*",
			dest="Region",
			metavar="region name string",
			default=["us-east-1"],
			help="String fragment of the region(s) you want to check for resources. You can supply multiple fragments.")
		self.my_parser.add_argument(
			"-k", "--skip",
			dest="SkipAccounts",
			nargs="*",
			metavar="Accounts to leave alone",
			default=[],
			help="These are the account numbers you don't want to screw with. Likely the core accounts.")
		# self.args = self.my_parser.parse_args()
