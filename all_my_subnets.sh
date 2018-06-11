#!/bin/bash

declare -a AllProfiles

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all subnets from all profiles"

format='%-20s %-40s %-24s %-24s %-24s %13s \n'

printf "$format" "Profile" "Subnet Name" "CIDR Block" "VPC ID" "SubnetId" "Available IPs"
printf "$format" "-------" "-----------" "----------" "------" "--------" "-------------"
for profile in ${AllProfiles[@]}; do
	aws ec2 describe-subnets --profile $profile --query 'Subnets[].[Tags[?Key==`Name`]|[0].Value,CidrBlock,VpcId,SubnetId,AvailableIpAddressCount]' --output text | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt, var, $1, $2, $3, $4, $5}'
	echo "----------------"
done

echo
exit 0
