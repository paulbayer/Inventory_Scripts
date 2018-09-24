#!/bin/bash

declare -a AllProfiles

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all directories from all profiles"

format='%-20s %-12s %-15s %-30s %-12s %-10s \n'

printf "$format" "Profile" "Region" "Name" "Access URL" "SSO Enabled" "Landing Zone"
printf "$format" "-------" "------" "----" "----------" "-----------" "------------"
for profile in ${AllProfiles[@]}; do
	if [[ ${1} ]]
		then
			region=$1
		else
			region=`aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text --profile ${profile}|tr '\t' '\n' |sort -u`
	fi
	tput el
	echo -ne "Checking Profile: $profile in region: $region\\r"
	# out=$(aws ds describe-directories --query 'DirectoryDescriptions[].[ShortName,AccessUrl,SsoEnabled]' --output text --profile $profile --region $region | awk -F $"\t" -v var=${profile} -v rgn=${region} -v fmt="${format}" '{printf fmt,var,rgn,$1,$2,$3}')
	out=$(aws ds describe-directories --query 'DirectoryDescriptions[].[ShortName,AccessUrl,SsoEnabled]' --output text --profile $profile --region $region)
	# echo "----- Output: "$out"-------"
	if [[ $out ]]
		then
			lz=$(aws ec2 describe-vpcs --profile $profile --region $region --filter --output text 'Name=tag-key,Values=AWS_Solutions' --query 'Vpcs[].[Tags[?Key==`AWS_Solutions`]|[0].Value]')
			if [[ " $lz " == " LandingZoneStackSet " ]]
				then
					lz="True"
			fi
			echo $out | awk -F $" " -v var=${profile} -v rgn=${region} -v lzone=${lz} -v fmt="${format}" '{printf fmt,var,rgn,$1,$2,$3,lzone}'
			echo "------------"
	fi
done

echo
exit 0
