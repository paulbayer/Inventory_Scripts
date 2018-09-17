#!/bin/bash

declare -a AllProfiles

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles"
echo "Outputting all VPC Peering Connections from all profiles"

format='%-20s %-10s %-24s %-24s %-20s %-15s \n'

# ToDo: This really needs to include the Account number for both sides, as well as the "Name" tag for the connectino, but I'm tired right now.
printf "$format" "Profile" "Region" "Req VPC ID" "Acptr VPC ID" "Peering Connection ID" "Status"
printf "$format" "-------" "------" "----------" "------------" "---------------------" "------"
for profile in ${AllProfiles[@]}; do
	if [[ ${1} ]]
		then
			region=$1
		else
			region=`aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text --profile ${profile}|tr '\t' '\n' |sort -u`
	fi
	tput el
	echo -ne "Checking Profile: $profile in region: $region\\r"
	out=$(aws ec2 describe-vpc-peering-connections --query 'VpcPeeringConnections[].[RequesterVpcInfo.VpcId,AccepterVpcInfo.VpcId,VpcPeeringConnectionId,Status.Message]' --output text --profile $profile --region $region | awk -F $"\t" -v var=${profile} -v rgn=${region} -v fmt="${format}" '{printf fmt,var,rgn,$1,$2,$3,$4}'|tee /dev/tty)
	if [[ $out ]]
		then
			echo "------------"
	fi
done
echo
echo "Finished checking all profiles"
# echo "------------"
exit 0
