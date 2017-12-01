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
echo "Outputting all S3 buckets from profile: $profile"

printf "%-20s %-50s \n" "Profile" "Bucket Name"
printf "%-20s %-50s \n" "-------" "-----------"
	aws s3api list-buckets --output text --query 'Buckets[*].Name' --profile $profile | awk -F $"\t" -v var=${profile} '{for (i=1;i<=NF;i++) printf "%-20s %-50s \n",var,$i}'
echo
exit 0
