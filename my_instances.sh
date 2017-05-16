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
#format="%-25s %-40s %12s %12s\n"
#printf "$format" "Instance Name" "Public DNS Name" "State" "Instance ID"
#printf "%-25s %-40s %12s %12s\n" "-------------" "---------------" "-----" "-----------"
#aws ec2 describe-instances --output table --query 'Reservations[*].Instances[*].[Architecture,Tags[?Key==`Name`]|[0].Value,PublicDnsName,State.Name,InstanceId]' --profile $profile | awk '{print $1,"|",$2,"|",$3,"|",$4,"|",$5}'
#aws ec2 describe-instances --output text --query 'Reservations[*].Instances[*].[Architecture,Tags[?Key==`Name`]|[0].Value,PublicDnsName,State.Name,InstanceId]' --profile $profile | paste -d "\t" - - - - - | awk -F $"\t" '{printf "%-25s %-40s %12s %12s\n", $2 $3 $4 $5}'
aws ec2 describe-instances --query 'Reservations[*].Instances[*].{Name:Tags[?Key==`Name`]|[0].Value,PublicDNSName:PublicDnsName,State:State.Name,Instance_ID:InstanceId}' --output table --profile $profile 

