#!/bin/bash

declare -a AllProfiles

if [[ $1 ]]
	then
		ProfileRegion=$1
	else
		ProfileRegion=`aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text|tr '\t' '\n' |sort -u`
fi

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all NAT Gateways from all profiles"

format='%-20s %-12s %-15s %-12s %-10s %-15s\n'

printf "$format" "Profile" "Region" "NAT GW Name" "State" "VpcID"
printf "$format" "-------" "------" "-----------" "-----" "-----"
for profile in ${AllProfiles[@]}; do
	if [[ $1 ]]
		then
			region=$1
		else
			region=`aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text --profile ${profile}|tr '\t' '\n' |sort -u`
	fi
	aws ec2 describe-nat-gateways --query 'NatGateways[].[NatGatewayId,State,VpcId]' --output text --profile $profile --region $region | awk -F $"\t" -v var=${profile} -v rgn=${region} -v fmt="${format}" '{printf fmt,var,rgn,$1,$2,$3}'
	echo "------------"
done

echo "------------"
exit 0
