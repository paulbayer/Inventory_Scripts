#!/bin/bash

profile=$1
region=$2

if [[ -z $profile ]]
	then
		echo
		echo "This command requires that you pass in the AWS profile name you're looking up"
		echo "Therefore, the script should be run like this:"
		echo "	$0 <profile name>"
		echo
		echo "Optionally - you can also include the region, but just the name, like this:"
		echo
		echo "	$0 <profile name> us-east-1"
		exit 1
fi

echo "Outputting all stacks, only from $profile, and only from your default region"
format='%-15s %-80s %-20s \n'

printf "$format" "Profile" "Export Name" "Export Value"
printf "$format" "-------" "-----------" "------------"
aws cloudformation list-exports --output text --query 'Exports[].[Name,Value]' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2}'

echo
exit 0
