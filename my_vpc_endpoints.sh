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
format='%-20s %-12s %-20s %-20s %-15s \n'

printf "$format" "Profile" "Region" "VPC ID" "VPC Endpoint ID" "State"
printf "$format" "-------" "------" "------" "---------------" "-----"
aws ec2 describe-vpc-endpoints --query 'VpcEndpoints[].[VpcId,VpcEndpointId,State]' --output text --profile $profile --region $region | awk -F $"\t" -v var=${profile} -v rgn=${region} -v fmt="${format}" '{printf fmt,var,rgn,$1,$2,$3}'
echo "------------"

echo "------------"
exit 0
