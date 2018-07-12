#!/bin/bash

declare -a AllProfiles

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all VPC Endpoints from all profiles"

format='%-20s %-20s %-20s %-30s %-15s \n'

# ToDo: This really needs to include the Account number for both sides, as well as the "Name" tag for the connectino, but I'm tired right now.
printf "$format" "Profile" "Req VPC ID" "Acptr VPC ID" "Peering Connection ID" "Status Message"
printf "$format" "-------" "----------" "------------" "---------------------" "--------------"
for profile in ${AllProfiles[@]}; do
	aws ec2 describe-vpc-peering-connections --query 'VpcPeeringConnections[].[RequesterVpcInfo.VpcId,AccepterVpcInfo.VpcId,VpcPeeringConnectionId,Status.Message]' --output text --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2,$3,$4}'
	echo "------------"
done

echo "------------"
exit 0
