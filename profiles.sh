#!/bin/bash

declare -a AllProfiles

AllProfiles=$(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r')

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all profiles and account numbers from your credentials file"
echo
format='%-15s %-20s \n'

printf "$format" "Profile Name" "Account Number"
printf "$format" "------------" "--------------"
for profile in ${AllProfiles[@]}; do
    AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
	printf "$format" $profile $AccountNumber
done

echo
exit 0
