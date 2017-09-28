#!/bin/bash

########
##
## Function to determine whether a value is in an array.
## I think this really only works with strings, which is all I need
##
########
elementIn () {
  local e match="$1"
  shift
  echo "array: $e"
  echo "string: $match"
  for item in ${e[*]}
    do
        echo "array: $e"
        echo "item: $item"
        echo "string: $match"
        [[ "$item" == "$match" ]] && return 0
    done
  return 1
}

# Completely new attempt at handling profiles.

declare -a AllProfiles
declare -a CredProfiles
declare -a ConfProfiles
declare -a SortedProfiles
declare -a DumbProfiles

### Define those values you want to filter out of the credentials listing
DumbProfiles=('default' 'Nope' 'Personal')

# Define the format once.
format='%-20s %-20s \n'

# Finds the profiles within your "credentials" file
CredProfiles=$(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r')
# Finds the profiles within your "config" file
ConfProfiles=$(egrep '\[.*\]' ~/.aws/config      | tr -d '[]\r' | sed -e 's/profile //g')
# Merges the two arrays
AllProfiles=("${CredProfiles[@]}" "${ConfProfiles[@]}")
# Sorts the resulting array and remove duplicates
SortedProfiles=($(sort -u <<< "${AllProfiles[@]}"))

printf "$format" "Profile Name" "Account Number"
printf "$format" "------------" "--------------"

echo ">> DumbProfiles"
echo ${DumbProfiles[*]} | awk '{print $0,"end", NF}'
echo ">> CredProfiles"
echo ${CredProfiles[*]} | awk '{print $0,"end", NF}'
echo ">> ConfProfiles"
echo ${ConfProfiles[@]} | awk '{print $0,"end", NF}'
echo ">> AllProfiles"
echo ${AllProfiles[*]} | awk '{print $0,"end", NF}'
echo ">> SortedProfiles"
echo ${SortedProfiles[*]} | awk '{print $0,"end", NF}'


for profile in ${SortedProfiles[@]}; do
    echo "Profile: "${profile}
	if elementIn "$profile" "${DumbProfiles[*]}"
		then
            AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
            awk -v profile=${profile} -v fmt=${format} -v AcctNum=${AccountNumber} '{printf fmt,profile,AcctNum,"Cred"}'
#			continue # The profile name is one of the ones I want to filter out.
#		else
#			AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
#			printf "$format" $profile $AccountNumber
#			if elementIn "$profile" "${CredProfiles[@]}"
#			 	then
#					printf "%-20s $format" $profile $AccountNumber "Credentials"
#				else
#					printf "%-20s $format" $profile $AccountNumber "Config"
#			fi
#			#echo $profile
	fi
#    if elementIn "$profile" "${CredProfiles[@]}"
#        then
#            AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
#            printf "$format" $profile $AccountNumber "Cred"
#    fi
done
#echo "profile: $profile"



exit 0
