#!/bin/bash

profile=$1

if [[ -z $profile ]]
	then
		echo
		echo "This command requires that you pass in the AWS profile name you're looking up"
		echo "Therefore, the script should be run like this:"
		echo "	$0 <profile name>"
		echo
		exit 1
fi

echo "Outputting all Groups from $profile"
format='%-20s %-40s %-15s %-15s %-40s \n'

printf "$format" "Profile" "Group Name" "Group ID" "VPCId" "Description"
printf "$format" "-------" "----------" "--------" "-----" "-----------"
aws ec2 describe-security-groups --output text --query 'SecurityGroups[].[GroupName,GroupId,VpcId,Description]' --profile $profile | awk -F $"\t" -v var="${profile}" -v fmt="${format}" '{printf fmt,var,$1,$2,$3,$4}'

echo
exit 0
