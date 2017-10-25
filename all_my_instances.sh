#!/bin/bash

declare -a AllProfiles

echo "Gathering profiles..."
#AllProfiles=(default Primary Secondary Nasdaq-Prod Nasdaq-Dev Nasdaq-DR)
AllProfiles=( $(./Allprofiles.sh programmatic | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

format='%-20s %-25s %-50s %-10s %-15s \n'

echo "Outputting all EC2 instances from all profiles"

printf "$format" "Profile" "Instance Name" "Public DNS Name" "State" "Instance ID"
printf "$format" "-------" "-------------" "---------------" "-----" "-----------"
for profile in ${AllProfiles[@]}; do
	aws ec2 describe-instances --output text --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`]|[0].Value,PublicDnsName,State.Name,InstanceId]' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2,$3,$4}'
done

echo
exit 0
