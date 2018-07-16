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
format='%-20s %-12s %-15s %-12s %-10s %-15s\n'

printf "$format" "Profile" "Region" "NAT GW Name" "State" "VpcID"
printf "$format" "-------" "------" "-----------" "-----" "-----"
if [[ $1 ]]
	then
		region=$1
	else
		region=`aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text --profile ${profile} |tr '\t' '\n' |sort -u`
fi
aws ec2 describe-nat-gateways --query 'NatGateways[].[NatGatewayId,State,VpcId]' --output text --profile $profile --region $region | awk -F $"\t" -v var=${profile} -v rgn=${region} -v fmt="${format}" '{printf fmt,var,rgn,$1,$2,$3}'

echo
exit 0
