#!/bin/bash

declare -a Acct1Roles
declare -a Acct2Roles
declare -a CombinedRoles

srcProfile=$1
dstProfile=$2


if [ -z $srcProfile ] ;
	then
		echo "	When you run this script, you need to supply two profiles to compare"
		echo "	Like: $0 <Source profile> <Destination profile>"
		echo
		exit 1
fi

# ProfileCount=${#AllProfiles[@]}
# echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting Roles from only the $srcProfile profile"
format='%-50s %-20s %-20s \n'

printf "$format" "Role Name" $srcProfile $dstProfile
printf "$format" "---------" "---------" "---------"
# Cycles through each role within the profile
Acct1Roles=( $(aws iam list-roles --output text --query 'Roles[].RoleName' --profile $srcProfile | tr '\t' '\n'))
Acct2Roles=( $(aws iam list-roles --output text --query 'Roles[].RoleName' --profile $dstProfile | tr '\t' '\n'))

#CombinedRoles=(${Acct1Roles[@]} ${Acct2Roles[@]}) | tr ' ' '\n' | sort | uniq -u

#for rolename in ${CombinedRoles[@]}; do
	aws iam list-users --output text --query 'Users[].UserName' --profile $profile | tr '\t' '\n'  | awk -F $"\t" -v var=${profile} -v fmt=${format} '{printf fmt,var,$1}'
	echo "----------------"
#done


# aws iam list-roles --output text --query 'Roles[].RoleName' --profile $srcProfile | tr '\t' '\n' |awk -F $"\t" -v var=${srcProfile} -v fmt="${format}" '{printf fmt,var,$1}'
echo "----------------"

echo
exit 0
