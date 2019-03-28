#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all ECS Clusters from all profiles"

format='%-20s %-20s \n'

printf "$format" "Profile" "Cluster Name"
printf "$format" "-------" "------------"
for profile in ${AllProfiles[@]}; do
	aws ecs list-clusters --output text --query 'clusterArns' --profile $profile | cut -d"/" -f 2 | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1}'
	echo "----------------"
done

echo
exit 0
