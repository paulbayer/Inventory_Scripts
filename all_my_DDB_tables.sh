#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(./Allprofiles.sh programmatic | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all DynamoDB Tables from all profiles"

printf "%-20s %-50s \n" "Profile" "Table Name"
printf "%-20s %-50s \n" "-------" "-----------"
for profile in ${AllProfiles[@]}; do
	aws dynamodb list-tables --output text --query 'TableNames' --profile $profile | tr "\t" "\n" | awk -F $"\t" -v var=${profile} '{printf "%-20s %-50s \n",var,$1}' 
	echo "----------------"
done

echo
exit 0
