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

echo "Outputting all key pairs, only from your $profile profile"
format='%-15s %-20s \n'

printf "$format" "Profile" "Key Pair Name"
printf "$format" "-------" "-------------"
aws ec2 describe-key-pairs --profile $profile --output text --query 'KeyPairs[].KeyName' |tr '\t' '\n'| awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1}'
# cmd_line = "aws ec2 describe-key-pairs --profile $profile --query 'KeyPairs[].KeyName | awk -F $'\t' -v var=${profile} -v fmt=${format} '{printf fmt,var,$1}'"
# if [[ -z $region ]]
#   then
#     ${cmd_line}
#   else
#     ${cmd_line} --region $region

echo
exit 0
