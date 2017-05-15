#!/bin/bash

declare -a AllProfiles

#AllProfiles=(default Primary Secondary Nasdaq-Prod Nasdaq-Dev Nasdaq-DR)
AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )


echo "Outputting all EC2 instances from all profiles"

printf "%-20s %-25s %-50s %-10s \n" "Profile" "Instance Name" "Public DNS Name" "State"
printf "%-20s %-25s %-50s %-10s \n" "-------" "-------------" "---------------" "-----"
for profile in ${AllProfiles[@]}; do
	aws ec2 describe-instances --output text --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value,PublicDnsName,[State.Name]]' --profile $profile | paste -d "\t" - - - | awk -F $"\t" -v var=${profile} '{printf "%-20s %-25s %-50s %-10s \n",var,$2,$1,$3}' 
done
echo
exit 0
