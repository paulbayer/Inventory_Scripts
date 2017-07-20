#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all CloudFormation Stacks from all profiles"

printf "%-15s %-35s %-20s %-50s \n" "Profile" "Stack Name" "Stack Status"
printf "%-15s %-35s %-20s %-50s \n" "-------" "----------" "------------"
for profile in ${AllProfiles[@]}; do
	aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE --output text --query 'StackSummaries[].[StackName,StackStatus,CreationTime]' --profile $profile | awk -F $"\t" -v var=${profile} '{printf "%-15s %-35s %-20s %-15s \n",var,$1,$2,$3}' | sort -k 74
	echo "----------------"
done

echo
exit 0
