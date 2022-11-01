#!/usr/bin/env python3


import re
import datetime
import Inventory_Modules
from colorama import init, Fore
from botocore.exceptions import ClientError
from ArgumentsClass import CommonArguments
from account_class import aws_acct_access

import logging

init()

parser = CommonArguments()
parser.verbosity()
parser.singleprofile()
parser.singleregion()

parser.my_parser.add_argument(
		'--ALZ',
		help="Identify left-over parameters created by the ALZ solution",
		action="store_const",
		dest="ALZParam",
		const=True,
		default=False)
parser.my_parser.add_argument(
		'-b', '--daysback',
		help="Only keep the last x days of Parameters (default 90)",
		dest="DaysBack",
		default=90)
parser.my_parser.add_argument(
		'+d', '--delete',
		help="Delete left-over parameters created by the ALZ solution",
		action="store_const",
		dest="DeletionRun",
		const=True,
		default=False)
args = parser.my_parser.parse_args()

pProfile = args.Profile
pRegion = args.Region
ALZParam = args.ALZParam
DeletionRun = args.DeletionRun
dtDaysBack = datetime.timedelta(days=int(args.DaysBack))
logging.basicConfig(level=args.loglevel,
                    format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")

##########################
ERASE_LINE = '\x1b[2K'
ALZRegex = '/\w{8,8}-\w{4,4}-\w{4,4}-\w{4,4}-\w{12,12}/\w{3,3}'
print()
fmt = '%-15s %-20s'
print(fmt % ("Parameter Name", "Last Modified Date"))
print(fmt % ("--------------", "------------------"))

aws_acct = aws_acct_access(pProfile)
aws_session = aws_acct.session
client_ssm = aws_session.client('ssm')
Parameters = []
ParamsToDelete = []
ALZParams = 0

try:
	# Since there could be 10,000 parameters stored in the Parameter Store - this function COULD take a long time
	Parameters = Inventory_Modules.find_ssm_parameters(pProfile, pRegion)
	logging.error(f"Profile: {pProfile} found a total of {len(Parameters)} parameters")
# print(ERASE_LINE,"Account:",account['AccountId'],"Found",len(Users),"users",end='\r')
except ClientError as my_Error:
	if str(my_Error).find("AuthFailure") > 0:
		print(f"{pProfile}: Authorization Failure")

if ALZParam:
	today = datetime.datetime.now(tz=datetime.timezone.utc)
	for y in range(len(Parameters)):
		# If the parameter matches the string regex of "/2ac07efd-153d-4069-b7ad-0d18cc398b11/105" - then it should be a candidate for deletion
		# With Regex - I'm looking for "/\w{8,8}-\w{4,4}-\w{4,4}-\w{4,4}-\w{12,12}/\w{3,3}"
		ParameterDate = Parameters[y]['LastModifiedDate']
		mydelta = today - ParameterDate  # this is a "timedelta" object
		p = re.compile(ALZRegex)  # Sets the regex to look for
		logging.info(f"Parameter{y}: {Parameters[y]['Name']} with date {Parameters[y]['LastModifiedDate']}")
		if p.match(Parameters[y]['Name']) and mydelta > dtDaysBack:
			logging.error(f"Parameter {Parameters[y]['Name']} with date of {Parameters[y]['LastModifiedDate']} matched")
			ALZParams += 1
			if DeletionRun:
				ParamsToDelete.append(Parameters[y]['Name'])
if DeletionRun:
	print(f"Deleting {len(ParamsToDelete)} ALZ-related Parameters now, further back than {dtDaysBack.days} days")
	# for i in range(len(ParamsToDelete)):
	mark = 0
	i = 0
	while i < len(ParamsToDelete) + 1:
		i += 1
		if i % 10 == 0:
			response = client_ssm.delete_parameters(
					Names=ParamsToDelete[mark:i]
					)
			mark = i
			print(ERASE_LINE, f"{i} parameters deleted and {len(ParamsToDelete) - i} more to go...", end='\r')
		elif i == len(ParamsToDelete):
			response = client_ssm.delete_parameters(
					Names=ParamsToDelete[mark:i]
					)
			logging.warning(f"Deleted the last {i % 10} parameters.")
print()
print(ERASE_LINE)
print(f"Found {len(Parameters)} total parameters")
if ALZParam:
	print(f"And {ALZParams} of them were from buggy ALZ runs more than {dtDaysBack.days} days back")
if DeletionRun:
	print(f"And we deleted {len(ParamsToDelete)} of them")
print()
print("Thanks for using this script.")
print()
