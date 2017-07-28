#!/bin/bash

declare -a AllProfiles
declare -a AcctUsers

AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all Users and their assigned policies (both attached and in-line) from all profiles"

# Screen Colors
nhl="[0m"
hl="[31;47m"

printf "%-15s %-40s %-60s \n" "Profile" "User Name" "AttachedPolicies"
printf "%-15s %-40s %-60s \n" "-------" "---------" "----------------"
for profile in ${AllProfiles[@]}; do
#	echo "Running for profile: $profile"
	i=1
	AcctUsers=( $(aws iam list-users --output text --query 'Users[].UserName' --profile $profile | tr '\t' '\n') )
	for user in ${AcctUsers[@]}; do
#		EvenOrOdd=( $i % 2 )
#		if [ $EvenOrOdd -eq 0 ] ; then
#			echo -en "Color:"${hl}${EvenOrOdd}":"
#		else
#			echo -en "NoColor:"${nhl}${EvenOrOdd}":"
#		fi
		aws iam list-attached-user-policies --user-name $user --profile $profile --output text --query 'AttachedPolicies[].PolicyName' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${user} '{printf "%-15s %-40s %-60s \n",var,var2,$1}'
		aws iam list-user-policies --user-name $user --profile $profile --output text --query 'PolicyNames' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${user} '{printf "%-15s %-40s %-60s \n",var,var2,$1}'
#		echo "Running for user: $user in Profile: $profile:"
#		aws iam list-attached-user-policies --user-name $user --profile $profile --output text --query 'AttachedPolicies[].PolicyName'
	done
	((i++))
	echo "----------------"
done

echo
exit 0
