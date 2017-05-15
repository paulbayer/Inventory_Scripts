#!/bin/bash

profile=$1

if [[ -z $profile ]] 
	then
		echo 
		echo "This command requires that you pass in the AWS profile name you're looking up"
		echo "Therefore, the script should be run like this:"
		echo "	$0 <profile name>"
		echo
		exit 1
fi

echo
echo "Instance Name            Public DNS Name			State"
echo "-----------------------------------------------------------"
aws ec2 describe-instances --output text --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value,PublicDnsName,[State.Name]]' --profile $profile | paste -d "\t" - - - | awk -F $"\t" '{print $2,"\t",$1,"\t",$3}'

