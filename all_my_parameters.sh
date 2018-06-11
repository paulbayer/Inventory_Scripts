#!/bin/bash

declare -a AllProfiles

echo "Gathering profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in all files"
echo "Outputting all Users from all profiles"

format='%-20s %-50s %-15s \n'

printf "$format" "Profile" "Parameter Name" "Parameter Type"
printf "$format" "-------" "--------------" "--------------"
for profile in ${AllProfiles[@]}; do
	aws ssm describe-parameters --output text --query 'Parameters[].[Name,Type]' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2}'
	echo "----------------"
done

echo
exit 0
