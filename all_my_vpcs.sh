#!/bin/bash

declare -a AllProfiles

#AllProfiles=(default Primary Secondary Nasdaq-Prod Nasdaq-Dev Nasdaq-DR)
#AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )
AllProfiles=( $(~/GitRepos/Inventory_Scripts/Allprofiles.sh | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all VPCs from all profiles"
format='%-20s %-15s %-15s %-15s \n'

printf "$format" "Profile" "VPC ID" "State" "Cidr Block"
printf "$format" "-------" "------" "-----" "----------"
for profile in ${AllProfiles[@]}; do
	aws ec2 describe-vpcs --query 'Vpcs[].[VpcId,State,CidrBlock]' --output text --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2,$3}'
	echo "----------------"
done

echo
exit 0
