#!/bin/bash

declare -a AcctRoles

profile=$1

if [ -z $profile ] ;
	then
		echo "	When you run this script, you need to supply a profile to check"
		echo "	Like: $0 <profile>"
		echo
		exit 1
fi

# ProfileCount=${#AllProfiles[@]}
# echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting Route Tables from only the $profile profile"
format='%-15s %-20s %-20s \n'

printf "$format" "Profile" "Route Table ID" "VPC ID"
printf "$format" "-------" "--------------" "------"
# Cycles through each role within the profile
aws ec2 describe-route-tables --output text --query 'RouteTables[].[RouteTableId,VpcId]' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2}'
echo "----------------"

echo
exit 0
