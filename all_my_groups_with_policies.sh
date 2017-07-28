#!/bin/bash

declare -a AllProfiles
declare -a AcctGroups

AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all Groups from all profiles"

# Screen Colors
nhl="[0m"
hl="[31;47m"

printf "%-15s %-40s %-60s \n" "Profile" "Group Name" "AttachedPolicies"
printf "%-15s %-40s %-60s \n" "-------" "----------" "----------------"
for profile in ${AllProfiles[@]}; do
#	echo "Running for profile: $profile"
	i=1
	AcctGroups=( $(aws iam list-groups --output text --query 'Groups[].GroupName' --profile $profile | tr '\t' '\n'))
	for group in ${AcctGroups[@]}; do
#		EvenOrOdd=( $i % 2 )
#		if [ $EvenOrOdd -eq 0 ] ; then
#			echo -en "Color:"${hl}${EvenOrOdd}":"
#		else
#			echo -en "NoColor:"${nhl}${EvenOrOdd}":"
#		fi
		aws iam list-attached-group-policies --group-name $group --profile $profile --output text --query 'AttachedPolicies[].PolicyName' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${group} '{printf "%-15s %-40s %-60s \n",var,var2,$1}'
		aws iam list-group-policies --group-name $group --profile $profile --output text --query 'PolicyNames' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${group} '{printf "%-15s %-40s %-60s \n",var,var2,$1}'
#		echo "Running for group: $group in Profile: $profile:"
#		aws iam list-attached-group-policies --group-name $group --profile $profile --output text --query 'AttachedPolicies[].PolicyName'
	done
	((i++))
	echo "----------------"
done

echo
exit 0
