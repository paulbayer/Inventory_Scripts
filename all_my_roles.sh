#!/bin/bash

declare -a AllProfiles
now=$(date +%s)

AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all IAM Roles from all profiles"

for profile in ${AllProfiles[@]}; do
	aws iam list-roles --profile $profile --query 'Roles[].[RoleName,Arn]' --output table
	echo "-----------------------"
done

echo
exit 0
