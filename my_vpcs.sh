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

echo "Outputting all VPCs, only from ${profile:="default"}, and only from ${region:="us-east-1"}"
format='%-20s %-20s %-24s %-15s %-15s %-14s \n'

printf "$format" "Profile" "Region" "VPC ID" "State" "Cidr Block" "Default VPC"
printf "$format" "-------" "------" "------" "-----" "----------" "-----------"
aws ec2 describe-vpcs --query 'Vpcs[].[VpcId,State,CidrBlock,IsDefault]' --output text --profile $profile --region $region | awk -F $"\t" -v reg=${region} -v var=${profile} -v fmt="${format}" '{printf fmt,var,reg,$1,$2,$3,$4}'

echo
exit 0
