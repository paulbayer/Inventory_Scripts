#!/bin/bash

declare -a AllProfiles

AllProfiles=$(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r')

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all profiles from all profiles"
echo
printf "%-15s %-20s \n" "Profile Name" "Account Number"
printf "%-15s %-20s \n" "------------" "--------------"
																         for profile in ${AllProfiles[@]}; do
    AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
	printf "%-15s %-20s \n" $profile $AccountNumber
done

echo
exit 0
