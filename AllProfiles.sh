#!/bin/bash

automated=$1

declare -a CredProfiles
declare -a CredProfiles2
declare -a ConfProfiles2
declare -a ConfProfiles
declare -a SkipProfiles

SkipProfiles=("default" "Nope" "Personal")
CredProfiles2=$(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r')
ConfProfiles2=$(egrep '\[.*\]' ~/.aws/config | tr -d '[]\r' | sed -e 's/profile //g')
CredProfiles=($(sort <<< "${CredProfiles2[@]}"))
ConfProfiles=($(sort <<< "${ConfProfiles2[@]}"))

fmt='%-20s %-20s %-20s \n'
if [[ ! $automated ]]
	then
		NumofProfiles=${#CredProfiles[@]}
		echo "Found ${NumofProfiles} profiles in credentials file"
		echo "Outputting all profiles from all profiles"
		echo
		printf "$fmt" "Profile Name" "Account Number" "File"
		printf "$fmt" "------------" "--------------" "----"
fi
for profile in ${CredProfiles[@]}; do
	if [[ ! " ${SkipProfiles[@]} " =~ " ${profile} " ]]
		then
			AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
			printf "$fmt" $profile $AccountNumber "credentials file"
# Debugging tools below
#		else
#			echo "SkipProfiles: "${SkipProfiles[@]}
#			echo "Profile: "${profile}
	fi
done
if [[ ! $automated ]] 
	then
		echo "-----"
fi
for profile in ${ConfProfiles[@]}; do
	if [[ ! " ${SkipProfiles[@]} " =~ " ${profile} " ]]
		then
			AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
			printf "$fmt" $profile $AccountNumber "config file"
# Debugging tools below
#		else
#			echo "SkipProfiles: "${SkipProfiles[@]}
#			echo "Profile: "${profile}
	fi
done

echo
exit 0
