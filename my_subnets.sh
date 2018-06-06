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

echo "Outputting all subnets from $profile profile, and only from your default (or specified) region"

format='%-20s %-40s %-24s %-24s %-24s %13s \n'

printf "$format" "Profile" "Subnet Name" "CIDR Block" "VPC ID" "SubnetId" "Available IPs"
printf "$format" "-------" "-----------" "----------" "------" "--------" "-------------"
aws ec2 describe-subnets --profile $profile --query 'Subnets[].[Tags[?Key==`Name`]|[0].Value,CidrBlock,VpcId,SubnetId,AvailableIpAddressCount]' --output text | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt, var, $1, $2, $3, $4, $5}'

echo
exit 0
