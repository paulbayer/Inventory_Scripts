#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(./AllProfiles.sh programmatic | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all subnets from all profiles"

format='%-20s %-20s %-24s %-15s %13s \n'

printf "$format" "Profile" "Subnet Name" "CIDR Block" "VPC ID" "Available IPs"
printf "$format" "-------" "-----------" "----------" "------" "-------------"
for profile in ${AllProfiles[@]}; do
	aws ec2 describe-subnets --profile $profile --query 'Subnets[].[Tags[?Key==`Name`]|[0].Value,CidrBlock,VpcId,AvailableIpAddressCount]' --output text | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt, var, $1, $2, $3, $4}'
	echo "----------------"
done

echo
exit 0
