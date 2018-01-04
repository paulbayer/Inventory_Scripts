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
format='%-15s %-35s \n'

printf "$format" "Profile" "Group Name"
printf "$format" "-------" "----------"
aws iam list-groups --output text --query 'Groups[].GroupName' --profile $profile | tr '\t' '\n'  | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1}'

echo
exit 0
