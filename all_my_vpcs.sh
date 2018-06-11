#!/bin/bash

declare -a AllProfiles

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all VPCs from all profiles"

format='%-20s %-40s %-24s %-15s %-15s \n'

printf "$format" "Profile" "VPC Name" "VPC ID" "State" "Cidr Block"
printf "$format" "-------" "--------" "------" "-----" "----------"
for profile in ${AllProfiles[@]}; do
	aws ec2 describe-vpcs --query 'Vpcs[].[Tags[?Key==`Name`]|[0].Value,VpcId,State,CidrBlock]' --output text --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2,$3,$4}'
	echo "------------"
done

echo "------------"
exit 0
