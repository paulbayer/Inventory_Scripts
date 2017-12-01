#!/bin/bash

declare -a AllProfiles

echo "Gathering profiles..."

AllProfiles=( $(./Allprofiles.sh programmatic | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all Config Rules from all profiles"

printf "%-15s %-35s %-20s \n" "Profile" "Config Rule Name" "Config Rule State"
printf "%-15s %-35s %-20s \n" "-------" "----------------" "-----------------"
for profile in ${AllProfiles[@]}; do
	aws configservice describe-config-rules --output text --query 'ConfigRules[].[ConfigRuleName,ConfigRuleState]' --profile $profile | awk -F $"\t" -v var=${profile} '{printf "%-15s %-35s %-20s \n",var,$1,$2}'
	echo "----------------"
done

echo
exit 0
