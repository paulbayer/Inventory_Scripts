#!/bin/bash
#set -x
declare -a AllProfiles
region="us-east-1"
echo "Gathering your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

format='%-20s %-12s %-50s \n'

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all S3 buckets from all profiles"

printf "$format" "Profile" "Region" "Bucket Name"
printf "$format" "-------" "------" "-----------"
for profile in ${AllProfiles[@]}; do
#	if [[ $1 ]]
#		then
#			region="us-east-1"
#		else
#			region=`aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text --profile ${profile}|tr '\t' '\n' |sort -u`
#	fi
	tput el
	echo -ne "Checking Profile: $profile in region: $region\\r"
	out=$(aws s3api list-buckets --output text --query 'Buckets[*].Name' --profile $profile --region $region | awk -F $"\t" -v var=${profile} -v rgn=${region} -v fmt="${format}" '{for (i=1;i<=NF;i++) printf fmt,var,rgn,$i}'|tee /dev/tty)
	# echo "----- Output: "$out"-------"
	if [[ $out ]]
		then
			echo "------------"
	fi
done

echo
exit 0
