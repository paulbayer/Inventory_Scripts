#!/bin/bash

declare -a AllProfiles
now=$(date +%s)

#AllProfiles=(default Primary Secondary Nasdaq-Prod Nasdaq-Dev Nasdaq-DR)
AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all IAM Roles from all profiles"

# printf "%-20s %-60s %15s %18s \n" "Profile" "Bucket Name" "Number of Files" "Total Size (Bytes)"
# printf "%-20s %-60s %15s %18s \n" "-------" "-----------" "---------------" "------------------"
for profile in ${AllProfiles[@]}; do
	aws iam list-roles --profile $profile --query 'Roles[].[RoleName,Arn]' --output table
	echo "-----------------------"
done

echo
exit 0
