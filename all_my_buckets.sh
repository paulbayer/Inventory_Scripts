#!/bin/bash

declare -a AllProfiles

echo "Gathering your profiles..."
AllProfiles=( $(AllProfiles.sh programmatic | awk '{print $1}') )

format='%-20s %-50s \n'

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all S3 buckets from all profiles"

printf "$format" "Profile" "Bucket Name"
printf "$format" "-------" "-----------"
for profile in ${AllProfiles[@]}; do
	aws s3api list-buckets --output text --query 'Buckets[*].Name' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{for (i=1;i<=NF;i++) printf fmt,var,$i}'
	echo "----------------"
done

echo
exit 0
