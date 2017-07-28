#!/usr/local/Cellar/bash/4.4.12/bin/bash

declare -a AcctGroups

profile=$1

if [ -z $profile ] ;
	then
		echo "	When you run this script, you need to supply a profile to check"
		echo "	Like: $0 <profile>"
		echo
		exit 1
fi

echo "Outputting all Groups from all profiles"

printf "%-15s %-40s %-18s %-60s \n" "Profile" "Group Name" "Policy Type" "AttachedPolicies"
printf "%-15s %-40s %-18s %-60s \n" "-------" "----------" "-----------" "----------------"
# Cycles through each group within the profile
AcctGroups=( $(aws iam list-groups --output text --query 'Groups[].GroupName' --profile $profile | tr '\t' '\n'))
for group in ${AcctGroups[@]}; do
	## This will output each policy associated with the specific group
	aws iam list-attached-group-policies --group-name $group --profile $profile --output text --query 'AttachedPolicies[].PolicyName' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${group} '{printf "%-15s %-40s %-18s %-60s \n",var,var2,"AWS Managed",$1}'
	aws iam list-group-policies --group-name $group --profile $profile --output text --query 'PolicyNames' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${group} '{printf "%-15s %-40s %-18s %-60s \n",var,var2,"In-line Policies",$1}'
	## ((i++))
done
## i=1
## echo -n ${nhl}
echo "----------------"

echo
exit 0
