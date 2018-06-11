#!/bin/bash

declare -a AllProfiles

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"

format='%-15s %-45s %-20s %-55s \n'

echo "Outputting all Lambda Functions and Roles from all profiles"

printf "$format" "Profile" "Function Name" "Runtime" "Role"
printf "$format" "-------" "-------------" "-------" "----"
for profile in ${AllProfiles[@]}; do
	aws lambda list-functions --output text --query 'Functions[].[FunctionName,Runtime,Role]' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2,$3}'
	echo "----------------"
done

echo
exit 0
