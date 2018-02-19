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
format='%-20s %-50s \n'

printf "$format" "Profile" "Bucket Name"
printf "$format" "-------" "-----------"
	aws s3api list-buckets --output text --query 'Buckets[*].Name' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt=${format} '{for (i=1;i<=NF;i++) printf fmt,var,$i}'
echo
exit 0
