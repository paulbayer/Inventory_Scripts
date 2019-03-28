#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all policies from all profiles"

format='%-15s %-65s %-15s \n'

printf "$format" "Profile" "Policy Name" "Times Attached"
printf "$format" "-------" "-----------" "--------------"
# Cycles through each profile
for profile in ${AllProfiles[@]}; do
	# Cycles through each role within the profile
	# This will output each policy associated with the specific role
	aws iam list-policies --profile $profile --output text --query 'Policies[?AttachmentCount!=`0`].[PolicyName,AttachmentCount]' | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2}' | sort -rg -k 3
	echo "----------------"
done

echo
exit 0
