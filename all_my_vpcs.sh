#!/bin/bash

declare -a AllProfiles

#AllProfiles=(default Primary Secondary Nasdaq-Prod Nasdaq-Dev Nasdaq-DR)
AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all VPCs from all profiles"

printf "%-20s %-12s %-12s %-15s \n" "Profile" "VPC ID" "State" "Cidr Block"
printf "%-20s %-12s %-12s %-15s \n" "-------" "------" "-----" "----------"
for profile in ${AllProfiles[@]}; do
	aws ec2 describe-vpcs --query 'Vpcs[].[VpcId,State,CidrBlock]' --output text --profile $profile | awk -F $"\t" -v var=${profile} '{printf "%-20s %-12s %-12s %-15s \n",var,$1,$2,$3}'
	echo "----------------"
done

echo
exit 0
