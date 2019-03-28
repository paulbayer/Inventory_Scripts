#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all CloudTrails from all profiles"

printf "%-15s %-35s %-30s \n" "Profile" "Trail Name" "S3 Bucket Name"
printf "%-15s %-35s %-30s \n" "-------" "----------" "--------------"
for profile in ${AllProfiles[@]}; do
	aws cloudtrail describe-trails --output text --query 'trailList[].[Name,S3BucketName]' --profile $profile | awk -F $"\t" -v var=${profile} '{printf "%-15s %-35s %-30s \n",var,$1,$2}'
	echo "----------------"
done

echo
exit 0
