#!/bin/bash

declare -a AllProfiles
declare -a AcctUsers

AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all Users and their assigned policies (both attached and in-line) from all profiles"

## Screen Colors
## nhl=""
## hl=""
## i=1

printf "%-15s %-40s %-5s %-60s \n" "Profile" "User Name" "MFA" "AttachedPolicies"
printf "%-15s %-40s %-5s %-60s \n" "-------" "---------" "---" "----------------"
# Cycles through each profile
for profile in ${AllProfiles[@]}; do
#	echo "Running for profile: $profile"
	AcctUsers=( $(aws iam list-users --output text --query 'Users[].UserName' --profile $profile | tr '\t' '\n') )
	for user in ${AcctUsers[@]}; do
		## To enable changing the font color to show when a group has multiple policies assigned.
		## EvenOrOdd=$(($i % 2))
		## if [ $EvenOrOdd -eq 0 ] ; then
		## 	echo -n ${hl}
		## else
		## 	echo -n ${nhl}
		## fi
		# This will output each policy associated with the specific user
#Checking MFA status
		my_var=`aws iam list-mfa-devices --user-name $user --output text`
        	if [ -z "$my_var" ]; then MFA="No"; else MFA="Yes"; fi
        	#echo $MFA
		aws iam list-attached-user-policies --user-name $user --profile $profile --output text --query 'AttachedPolicies[].PolicyName' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${user} -v var3=${MFA} '{printf "%-15s %-40s %-5s %-60s \n",var,var2,var3,$1}'
		aws iam list-user-policies --user-name $user --profile $profile --output text --query 'PolicyNames' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${user} -v var3=${MFA} '{printf "%-15s %-40s %-5s %-60s \n",var,var2,var3,$1}'
		## ((i++))
	done
	## i=1
	## echo -n ${nhl}
	echo "----------------"
done

echo
exit 0
