#!/bin/bash

declare -a AcctUsers

profile=$1

if [ -z $profile ] ;
	then
		echo "	When you run this script, you need to supply a profile to check"
		echo "	Like: $0 <profile>"
		echo
		exit 1
fi

echo "Outputting all Users and their assigned policies (both attached and in-line)"
format='%-15s %-40s %-18s %-60s \n'

printf "$format" "Profile" "User Name" "Policy Type" "AttachedPolicies"
printf "$format" "-------" "---------" "-----------" "----------------"
#	echo "Running for profile: $profile"
AcctUsers=( $(aws iam list-users --output text --query 'Users[].UserName' --profile $profile | tr '\t' '\n') )
for user in ${AcctUsers[@]}; do
	# This will output each policy associated with the specific user
	aws iam list-attached-user-policies --user-name $user --profile $profile --output text --query 'AttachedPolicies[].PolicyName' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${user} -v fmt="${format}" '{printf fmt,var,var2,"AWS Managed",$1}'
	aws iam list-user-policies --user-name $user --profile $profile --output text --query 'PolicyNames' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${user} -v fmt="${format}" '{printf fmt,var,var2,"In-line Policies",$1}'
done
echo "----------------"
echo
exit 0
