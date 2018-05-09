#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(./AllProfiles.sh programmatic | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

format='%-20s %-50s \n'

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all DynamoDB Tables from all profiles"

printf "$format" "Profile" "Table Name"
printf "$format" "-------" "----------"
for profile in ${AllProfiles[@]}; do
	aws dynamodb list-tables --output text --query 'TableNames' --profile $profile | tr "\t" "\n" | awk -F $"\t" -v var=${profile} -v fmt=${format} '{printf fmt,var,$1}'
	echo "----------------"
done

echo
exit 0
