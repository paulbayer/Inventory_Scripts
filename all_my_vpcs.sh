#!/bin/bash

declare -a AllProfiles

BLUE=$(tput setaf 12)
MAGENTA=$(tput setaf 13)
RedError=$(tput setaf 9; tput setab 249; tput blink)
STD=$(tput init)


if [[ $1 ]]
	then
		region=$1
	else
		region=$(aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text --profile ${profile} |tr '\t' '\n' |sort -u)
		# region=`aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text --profile ${profile}|tr '\t' '\n' |sort -u`
fi

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all VPCs from all profiles"

format='%-20s %-12s %-30s %-24s %-10s %-15s %-8s\n'

printf "$format" "Profile" "Region" "VPC Name" "VPC ID" "State" "Cidr Block" "Default?"
printf "$format" "-------" "------" "--------" "------" "-----" "----------" "--------"
i=0
for profile in ${AllProfiles[@]}; do
	if (( $i % 2 ))
		then
			echo -n $BLUE
		else
			echo -n $MAGENTA
	fi
	aws ec2 describe-vpcs --query 'Vpcs[].[Tags[?Key==`Name`]|[0].Value,VpcId,State,CidrBlock,IsDefault]' --output text --profile $profile --region $region | awk -F $"\t" -v var=${profile} -v rgn=${region} -v fmt="${format}" '{printf fmt,var,rgn,$1,$2,$3,$4,$5}'
	# echo "------------"
	(( i++ ))
done

echo $STD
# echo "------------"
exit 0
