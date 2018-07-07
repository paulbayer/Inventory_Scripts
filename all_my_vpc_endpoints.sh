#!/bin/bash

declare -a AllProfiles

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all VPC Endpoints from all profiles"

format='%-20s %-20s %-20s %-15s \n'

printf "$format" "Profile" "VPC ID" "VPC Endpoint ID" "State"
printf "$format" "-------" "------" "---------------" "-----"
for profile in ${AllProfiles[@]}; do
	aws ec2 describe-vpc-endpoints --query 'VpcEndpoints[].[VpcId,VpcEndpointId,State]' --output text --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2,$3}'
	echo "------------"
done

echo "------------"
exit 0
