#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all Users from all profiles"

printf "%-15s %-35s \n" "Profile" "User Name"
printf "%-15s %-35s \n" "-------" "----------"
for profile in ${AllProfiles[@]}; do
	aws iam list-users --output text --query 'Users[].UserName' --profile $profile | tr '\t' '\n'  | awk -F $"\t" -v var=${profile} '{printf "%-15s %-35s \n",var,$1}'
	echo "----------------"
done

echo
exit 0
