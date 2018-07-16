#!/bin/bash

declare -a AllProfiles

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all VPCs from all profiles"

format='%-20s %-12s %-30s %-24s %-10s %-15s %-8s\n'

printf "$format" "Profile" "Region" "VPC Name" "VPC ID" "State" "Cidr Block" "Default?"
printf "$format" "-------" "------" "--------" "------" "-----" "----------" "--------"
for profile in ${AllProfiles[@]}; do
	if [[ $1 ]]
		then
			region=$1
		else
			region=`aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text --profile ${profile}|tr '\t' '\n' |sort -u`
	fi
	aws ec2 describe-vpcs --query 'Vpcs[].[Tags[?Key==`Name`]|[0].Value,VpcId,State,CidrBlock,IsDefault]' --output text --profile $profile --region $region | awk -F $"\t" -v var=${profile} -v rgn=${region} -v fmt="${format}" '{printf fmt,var,rgn,$1,$2,$3,$4,$5}'
	echo "------------"
done

echo "------------"
exit 0
