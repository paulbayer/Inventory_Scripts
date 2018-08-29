#!/bin/bash

automated=$1
## If the "automated" parameter is equal to the string "ProfileNameOnly", then this script won't call the "sts get-caller-identity" function

declare -a CredProfiles
declare -a CredProfiles2
declare -a ConfProfiles2
declare -a ConfProfiles
declare -a SkipProfiles

SkipProfiles=()
SkipProfiles=("Nope" "Personal" "SS-default" "SS-seciaas" "SS-Sand" "default" "TouchPoint" "Shared-Fid" "TIAA-Mngmnt-Prod-e1" "TIAA-Mngmnt-Prod-w2" "ChildAccount-e1" "ChildAccount-w2" "ChildAccount2-e1" "ChildAccount2-w2")
CredProfiles2=$(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r')
ConfProfiles2=$(egrep '\[.*\]' ~/.aws/config | tr -d '[]\r' | sed -e 's/profile //g')
CredProfiles=($(sort <<< "${CredProfiles2[@]}"))
ConfProfiles=($(sort <<< "${ConfProfiles2[@]}"))

fmt='%-20s %-20s %-20s %-30s \n'

if [[ ! $automated ]]
	then
		ProfileCount=${#CredProfiles[@]}
		echo "Found ${ProfileCount} profiles in credentials file"
		echo "Outputting all profiles from all profiles"
		echo
		printf "$fmt" "Profile Name" "Account Number" "File" "Root Organization"
		printf "$fmt" "------------" "--------------" "----" "-----------------"
fi
for profile in ${CredProfiles[@]}; do
	if [[ ! " ${SkipProfiles[@]} " =~ " ${profile} " ]]
		then
			if [[ " ${automated} " =~ " ProfileNameOnly " ]]
				then
					printf "$fmt" $profile "credentials file"
				else
					AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
					printf "$fmt" $profile $AccountNumber "credentials file"
			fi
	fi
done
if [[ ! $automated ]]
	then
		echo "-----"
fi
for profile in ${ConfProfiles[@]}; do
	if [[ ! " ${SkipProfiles[@]} " =~ " ${profile} " ]]
		then
			if [[ " ${automated} " =~ " ProfileNameOnly " ]]
				then
					printf "$fmt" $profile "config file"
				else
					AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
					printf "$fmt" $profile $AccountNumber "config file"
			fi
	fi
done

echo
exit 0
