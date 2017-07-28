#!/usr/local/Cellar/bash/4.4.12/bin/bash

declare -a AllProfiles
declare -a AcctGroups

AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all Groups from all profiles"

## Screen Colors
## nhl="[0m"
## hl="[31m"
## i=1

printf "%-15s %-40s %-60s \n" "Profile" "Group Name" "AttachedPolicies"
printf "%-15s %-40s %-60s \n" "-------" "----------" "----------------"
# Cycles through each profile
for profile in ${AllProfiles[@]}; do
	# Cycles through each group within the profile
	AcctGroups=( $(aws iam list-groups --output text --query 'Groups[].GroupName' --profile $profile | tr '\t' '\n'))
	for group in ${AcctGroups[@]}; do
		## To enable changing the font color to show when a group has multiple policies assigned.
		## EvenOrOdd=$(($i % 2))
		## if [ $EvenOrOdd -eq 0 ] ; then
		## 	echo -n ${hl}
		## else
		## 	echo -n ${nhl}
		## fi
		## This will output each policy associated with the specific group
		aws iam list-attached-group-policies --group-name $group --profile $profile --output text --query 'AttachedPolicies[].PolicyName' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${group} '{printf "%-15s %-40s %-60s \n",var,var2,$1}'
		aws iam list-group-policies --group-name $group --profile $profile --output text --query 'PolicyNames' | tr '\t' '\n' | awk -F $"\t" -v var=${profile} -v var2=${group} '{printf "%-15s %-40s %-60s \n",var,var2,$1}'
		## ((i++))
	done
	## i=1
	## echo -n ${nhl}
	echo "----------------"
done

echo
exit 0
