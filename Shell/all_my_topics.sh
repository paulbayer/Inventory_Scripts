#!/bin/bash

declare -a AllProfiles
declare -a ProfileBuckets

AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )
echo "Gathering Profiles..."

format='%-20s %-50s \n'

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles"
echo "Outputting all SNS topics from all profiles"

printf "${format}" "Profile" "Topic Name"
printf "${format}" "-------" "-----------"
for profile in ${AllProfiles[@]}; do
	aws sns list-topics --output text --query 'Topics[].TopicArn' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{for (i=1;i<=NF;i++) printf fmt,var,$i}'
	echo "----------------"
done

echo
exit 0
