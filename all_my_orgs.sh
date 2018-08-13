#!/bin/bash

declare -a AllProfiles
declare -a AllOrgAccts
declare -a UniqOrgs

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all Organizations from all profiles"

format='%-20s %-15s %-15s %-24s \n'

printf "$format" "Profile" "Master Account ID" "Org ID" "Account Email"
printf "$format" "-------" "-----------------" "------" "-------------"
for profile in ${AllProfiles[@]}; do
	AllOrgAccts+=( $(aws organizations describe-organization --query 'Organization.MasterAccountId' --output text --profile $profile) )
	echo "Checking profile $profile"
done

UniqOrgs=$(echo "${AllOrgAccts[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' ')

echo "----------"

for AcctNum in ${UniqOrgs[*]}; do
	echo ${AcctNum}
done
exit 0

	tput el
	echo -ne "Checking Profile: $profile in region: $region\\r"
	out=$(aws organizations describe-organization --query 'Organization.[MasterAccountId,Id,MasterAccountEmail]' --output text --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2,$3}'|tee /dev/tty)
	# echo "----- Output: "$out"-------"

	if [[ $out ]]
		then
			echo "------------"
	fi
done

exit 0
