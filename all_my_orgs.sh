#!/bin/bash

declare -a AllProfiles
declare -a AllOrgAccts
declare -a UniqOrgs

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

# ProfileCount=${#AllProfiles[@]}
# echo "Found ${ProfileCount} profiles in credentials file"
# echo "Outputting all Organizations from all profiles"
#
# format='%-20s %-15s %-15s %-24s \n'
#
# printf "$format" "Profile" "Master Account ID" "Org ID" "Account Email"
# printf "$format" "-------" "-----------------" "------" "-------------"
for profile in ${AllProfiles[@]}; do
	AllOrgAccts+=( $(aws organizations describe-organization --query 'Organization.MasterAccountId' --output text --profile $profile) )
	tput el
	echo -ne "Checking profile $profile\\r"
done

echo
UniqOrgs=$(echo "${AllOrgAccts[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' ')

echo "----------"

for AcctNum in ${UniqOrgs[*]}; do
	echo ${AcctNum}
done
exit 0
