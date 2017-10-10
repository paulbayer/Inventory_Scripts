#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(~/GitRepos/Inventory_Scripts/Allprofiles.sh | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all Lambda Functions from all profiles"

printf "%-15s %-35s %-20s %-50s \n" "Profile" "Function Name" "Runtime" "Description"
printf "%-15s %-35s %-20s %-50s \n" "-------" "-------------" "-------" "-----------"
for profile in ${AllProfiles[@]}; do
	aws lambda list-functions --output text --query 'Functions[].[FunctionName,Runtime,Description]' --profile $profile | awk -F $"\t" -v var=${profile} '{printf "%-15s %-35s %-20s %-50s \n",var,$1,$2,$3}'
	echo "----------------"
done

echo
exit 0
