#!/bin/bash

profile=$1
region=${2-"us-east-1"}

if [[ -z $profile ]]
	then
		echo
		echo "This command requires that you pass in the AWS profile name you're looking up"
		echo "Therefore, the script should be run like this:"
		echo "	$0 <profile name> [region]"
		echo
		exit 1
fi

echo

aws ec2 describe-instances --query 'Reservations[*].Instances[*].{Name:Tags[?Key==`Name`]|[0].Value,AZ:Placement.AvailabilityZone,PublicDNSName:PublicDnsName,State:State.Name,Instance_ID:InstanceId}' --output table --profile $profile --region $region
