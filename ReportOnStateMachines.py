#!/usr/bin/env python3

"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import argparse
import boto3
import datetime
import logging
import pprint
import sys

from colorama import init

init()

# UsageMsg="You can provide a level to determine whether this script considers only the 'credentials' file, the 'config' file, or both."
parser = argparse.ArgumentParser(
	description="We\'re going to find all resources within any of the profiles we have access to.",
	prefix_chars='-+/')
parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	help="You need to specify a profile that represents the ROOT account.")
parser.add_argument(
	"-r", "--region",
	dest="pregion",
	metavar="region name string",
	default="us-east-1",
	help="Name of the region(s) you want to check for resources.")
parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,  # args.loglevel = 10
	default=logging.CRITICAL)  # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,  # args.loglevel = 20
	default=logging.CRITICAL)  # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,  # args.loglevel = 30
	default=logging.CRITICAL)  # args.loglevel = 50
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,  # args.loglevel = 40
	default=logging.CRITICAL)  # args.loglevel = 50
args = parser.parse_args()

pProfile = args.pProfile  # Accepts only a single profile. TODO - check that it's the master of the org
pRegion = args.pregion  # Accepts only a single region. TODO - check that it's the region with the pipeline
logging.basicConfig(level=args.loglevel)

session_cp = boto3.Session(profile_name=pProfile, region_name=pRegion)
client_cp = session_cp.client('codepipeline')

# Find Pipeline name
response = client_cp.list_pipelines()
for i in range(len(response['pipelines'])):
	if "AWS-Landing-Zone" in response['pipelines'][i]['name']:
		PipelineName = response['pipelines'][i]['name']
# Find Pipeline Executions
response = client_cp.list_pipeline_executions(
	pipelineName=PipelineName)

# Assumes that at least one response comes back. TODO - error checking here
LatestRun = response['pipelineExecutionSummaries'][0]['lastUpdateTime']
PipelineExecutionId = response['pipelineExecutionSummaries'][0]['pipelineExecutionId']

# Sort output from above, to find the last successful full pipeline run and the stop time
for i in range(len(response['pipelineExecutionSummaries'])):
	if LatestRun < response['pipelineExecutionSummaries'][i]['lastUpdateTime']:
		LatestRun = response['pipelineExecutionSummaries'][i]['lastUpdateTime']
		PipelineExecutionId = response['pipelineExecutionSummaries'][i]['pipelineExecutionId']

response = client_cp.list_action_executions(pipelineName=PipelineName, filter={'pipelineExecutionId': PipelineExecutionId})

PipelineStart = response['actionExecutionDetails'][0]['startTime']
PipelineEnd = LatestRun
print("The pipeline run you're interested in:")
PipelineRun = response['actionExecutionDetails']
for i in range(len(PipelineRun)):
	logging.warning("StageType: " + PipelineRun[i]['actionName'])
	logging.warning("StageName: " + PipelineRun[i]['stageName'])
	logging.warning("Status: " + PipelineRun[i]['status'])
	if PipelineRun[i]['startTime'] < PipelineStart:
		PipelineStart = PipelineRun[i]['startTime']
	logging.warning("Start: " + str(PipelineRun[i]['startTime']))
	if PipelineRun[i]['lastUpdateTime'] > PipelineEnd:
		PipelineEnd = PipelineRun[i]['lastUpdateTime']
	logging.warning("End: " + str(PipelineRun[i]['lastUpdateTime']))
	logging.warning("Duration: " + str(PipelineRun[i]['lastUpdateTime'] - PipelineRun[i]['startTime']))
	print()

# List all State Machines - keeping the arns of all the state machines for the Landing Zone
StateMachineArns = []
print("The Landing Zone Step Functions that are configured within the account")
session_sf = boto3.Session(profile_name=pProfile)
client_sf = session_sf.client('stepfunctions')
response = client_sf.list_state_machines()
for i in range(len(response['stateMachines'])):
	if "LandingZone" in response['stateMachines'][i]['stateMachineArn']:
		StateMachineArns.append(response['stateMachines'][i]['stateMachineArn'])
		logging.warning(response['stateMachines'][i]['stateMachineArn'])
# Find all state machine executions from all state machine arns which started AFTER the last successful pipeline run started and stopped BEFORE the last successful pipeline run ended.
pprint.pprint(StateMachineArns)

StateMachinesDuringRun = []
# For each of the Pipeline Stages...
for k in range(len(PipelineRun)):
	# The Start of this Stage of the Pipeline
	PipelineStageStart = PipelineRun[k]['startTime']
	# The End of this Stage of the Pipeline
	PipelineStageEnd = PipelineRun[k]['lastUpdateTime']
	# The Name of this Stage of the Pipeline
	PipelineStageName = PipelineRun[k]['stageName']
	PipelineStageStatus = PipelineRun[k]['status']
	PipelineStageDuration = PipelineRun[k]['lastUpdateTime'] - PipelineRun[k]['startTime']
	logging.warning("Handling stage " + PipelineStageName + " now...")
	SMExecActiveDuringStage = []
	RunningSMExecDuration = 0
	SMExecDuration = datetime.datetime.min - datetime.datetime.min
	# For each of the State Machines that ran at all...
	for i in range(len(StateMachineArns)):
		response = client_sf.list_executions(stateMachineArn=StateMachineArns[i])
		# For each of the executions of those State Machines...
		for j in range(len(response['executions'])):
			# See which execution of that State Machines was active during this time...
			if response['executions'][j]['startDate'] > PipelineStageStart and response['executions'][j][
				'stopDate'] < PipelineStageEnd:
				# Find the Duration of this execution of the Step Machine
				SMExecDuration = response['executions'][j]['stopDate'] - response['executions'][j]['startDate']
				# And collect those executions that were active into a list...
				SMExecActiveDuringStage.append(response['executions'][j])
				RunningSMExecDuration = RunningSMExecDuration + SMExecDuration.total_seconds()
	# Potentially a place to check for CloudFormation stackset work
	StateMachinesDuringRun.append({
		'PipelineStageName': PipelineStageName,
		'PipelineStageStatus': PipelineStageStatus,
		'PipelineStart': PipelineStageStart,
		'PipelineEnd': PipelineStageEnd,
		'PipelineStageDuration': str(PipelineStageDuration),
		'StateMachinesDuration': datetime.timedelta(seconds=RunningSMExecDuration),
		# 'StateMachinesRun':SMExecActiveDuringStage,
		'Unaccounted': str(PipelineStageDuration - datetime.timedelta(seconds=RunningSMExecDuration))
	})
print()
print("This is the list of Pipelines with Step Functions")
pprint.pprint(StateMachinesDuringRun)
print()

sys.exit(9)
# Find all StackSets for Landing zone
session_cf = boto3.Session(profile_name=pProfile)
client_cf = session_cf.client('cloudformation')
response = client_cf.list_stack_sets(Status='ACTIVE')

# Find all Operations for these StackSets since the beginning of the pipeline
print("You're interested in CFN stackset instances that ran between the beginning of the Pipeline:", PipelineStart, "and the end of the Pipeline:", PipelineEnd)
StackSetsArray = []
for i in range(len(response['Summaries'])):
	if 'AWS-Landing-Zone' in response['Summaries'][i]['StackSetName']:
		StackSetsArray.append(response['Summaries'][i]['StackSetName'])

StackSetOperations = []
# Finds all stackset instances that ran during the Pipeline
PipelineStart = datetime.datetime(2019, 10, 24, 11, 7, 59, 527000, tzinfo=tzlocal())
for StackSet in StackSetsArray:
	logging.warning("Now handling stackset: " + str(StackSet))
	MoreResults = True
	NextPageToken = ''
	while MoreResults:
		if NextPageToken == '':
			resp = client_cf.list_stack_set_operations(
				StackSetName=StackSet,
				MaxResults=100)
		else:
			resp = client_cf.list_stack_set_operations(
				StackSetName=StackSet,
				NextToken=NextPageToken,
				MaxResults=100)
		if 'NextToken' in resp:
			NextPageToken = resp['NextToken']
			MoreResults = True
		else:
			MoreResults = False
		for i in range(len(resp['Summaries'])):
			Accounts = []
			Regions = []
			if PipelineStart < resp['Summaries'][i]['CreationTimestamp']:
				response = client_cf.list_stack_set_operation_results(
					StackSetName=StackSet,
					OperationId=resp['Summaries'][i]['OperationId']
				)
				for x in range(len(response['Summaries'])):
					Accounts.append(response['Summaries'][x]['Account'])
					Regions.append(response['Summaries'][x]['Region'])
				Accounts = list(set(Accounts))
				Regions = list(set(Regions))
				StackSetOperations.append({
					'StackSetName': StackSet,
					'StackSetOperationId': resp['Summaries'][i]['OperationId'],
					'Account': Accounts,
					'Regions': Regions,
					'Action': resp['Summaries'][i]['Action'],
					'Status': resp['Summaries'][i]['Status'],
					'OperationStart': resp['Summaries'][i]['CreationTimestamp'],
					'OperationEnd': resp['Summaries'][i]['EndTimestamp'],
					'OperationDuration': resp['Summaries'][i]['EndTimestamp'] - resp['Summaries'][i][
						'CreationTimestamp']
				})
newlist = sorted(StackSetOperations, key=itemgetter('OperationDuration'))
pprint.pprint(newlist)
