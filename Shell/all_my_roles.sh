#!/bin/bash

declare -a AllProfiles
now=$(date +%s)

AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all IAM Roles from all profiles"

format='%-15s %-30s %-40s \n'

printf "$format" "Profile" "Role Name" "Arn"
printf "$format" "-------" "---------" "---"

for profile in ${AllProfiles[@]}; do
	aws iam list-roles --profile $profile --query 'Roles[].[RoleName,Arn]' --output text | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2}'
	echo "-----------------------"
done

echo
exit 0
