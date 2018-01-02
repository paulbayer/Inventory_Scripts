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

printf "%-15s %-35s \n" "Profile" "Group Name"
printf "%-15s %-35s \n" "-------" "----------"
aws iam list-groups --output text --query 'Groups[].GroupName' --profile $profile | tr '\t' '\n'  | awk -F $"\t" -v var=${profile} '{printf "%-15s %-35s \n",var,$1}'

echo
exit 0
