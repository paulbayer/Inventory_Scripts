#!/usr/local/Cellar/bash/4.4.12/bin/bash

declare -a AcctRoles

profile=$1

if [ -z $profile ] ;
	then
		echo "	When you run this script, you need to supply a profile to check"
		echo "	Like: $0 <profile>"
		echo
		exit 1
fi

# AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )

# NumofProfiles=${#AllProfiles[@]}
# echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting Roles from only the $profile profile"

printf "%-15s %-35s %-18s %-60s \n" "Profile" "Role Name" "Policy Type" "AttachedPolicies"
printf "%-15s %-35s %-18s %-60s \n" "-------" "---------" "-----------" "----------------"
# Cycles through each role within the profile
AcctRoles=( $(aws iam list-roles --output text --query 'Roles[].RoleName' --profile $profile | tr '\t' '\n'))
for role in ${AcctRoles[@]}; do
	# This will output each policy associated with the specific role
	aws iam list-attached-role-policies --role-name $role --profile $profile --output text --query 'AttachedPolicies[].PolicyName' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${role} '{printf "%-15s %-35s %-18s %-60s \n",var,var2,"AWS Managed",$1}'
	aws iam list-role-policies --role-name $role --profile $profile --output text --query 'PolicyNames' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${role} '{printf "%-15s %-35s %-18s %-60s \n",var,var2,"In-line Policies",$1}'
done
echo "----------------"

echo
exit 0
