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

format='%-20s %-15s \n'

echo

printf "$format" "Profile" "Account ID"
printf "$format" "-------" "----------"
	aws sts get-caller-identity --output text --query 'Account' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1}'
echo
exit 0
