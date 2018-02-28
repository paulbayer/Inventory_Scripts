#!/bin/bash

declare -a AcctRoles

profile=$1

if [ -z $profile ] ;
	then
		echo "	When you run this script, you need to supply a profile to check"
		echo "	Like: $0 <profile>"
		echo
		exit 1
fi

# ProfileCount=${#AllProfiles[@]}
# echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting Roles from only the $profile profile"
format='%-15s %-35s \n'

printf "$format" "Profile" "Role Name"
printf "$format" "-------" "---------"
# Cycles through each role within the profile
aws iam list-roles --output text --query 'Roles[].RoleName' --profile $profile | tr '\t' '\n' |awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1}'
echo "----------------"

echo
exit 0
