#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(./AllProfiles.sh programmatic | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all Groups from all profiles"

printf "%-15s %-35s \n" "Profile" "Group Name"
printf "%-15s %-35s \n" "-------" "----------"
for profile in ${AllProfiles[@]}; do
	aws iam list-groups --output text --query 'Groups[].GroupName' --profile $profile | tr '\t' '\n'  | awk -F $"\t" -v var=${profile} '{printf "%-15s %-35s \n",var,$1}'
	echo "----------------"
done

echo
exit 0
