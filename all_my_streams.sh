#!/bin/bash

declare -a AllProfiles

AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all Kinesis Streams from all profiles"

printf "%-20s %-50s \n" "Profile" "Topic Name"
printf "%-20s %-50s \n" "-------" "-----------"
for profile in ${AllProfiles[@]}; do
	aws kinesis list-streams --output text --query 'StreamNames' --profile $profile | awk -F $"\t" -v var=${profile} '{for (i=1;i<=NF;i++) printf "%-20s %-50s \n",var,$i}'
	echo "----------------"
done

echo
exit 0
