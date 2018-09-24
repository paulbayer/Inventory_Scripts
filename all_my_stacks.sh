#!/bin/bash

declare -a AllProfiles

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all CloudFormation Stacks from all profiles"

format='%-15s %-35s %-30s %-12s \n'

printf "$format" "Profile" "Region" "Stack Name" "Stack Status"
printf "$format" "-------" "------" "----------" "------------"
for profile in ${AllProfiles[@]}; do
	if [[ ${1} ]]
		then
			region=$1
		else
			region=`aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text --profile ${profile}|tr '\t' '\n' |sort -u`
	fi
	tput el
	echo -ne "Checking Profile: $profile in region: $region\\r"
	out=$(aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE --output text --query 'StackSummaries[].[StackName,StackStatus,CreationTime]' --profile $profile --region $region | awk -F $"\t" -v var=${profile} -v rgn=${region} -v fmt="${format}" '{printf fmt,var,rgn,$1,$2,$3}' | sort -k 74 | tee /dev/tty)
	if [[ $out ]]
		then
			echo "------------"
	fi
	done
echo
exit 0
