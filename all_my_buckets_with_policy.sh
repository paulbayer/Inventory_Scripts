#!/bin/bash

declare -a AllProfiles
declare -a AllBuckets

echo "Gathering your profiles..."
AllProfiles=( $(AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

format='%-20s %-12s %-50s %-50s \n'

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all S3 buckets from all profiles"

printf "$format" "Profile" "Region" "Bucket Name" "Policy"
printf "$format" "-------" "------" "-----------" "------"
for profile in ${AllProfiles[@]}; do
	if [[ $1 ]]
		then
			region=$1
		else
			region=`aws ec2 describe-availability-zones --query 'AvailabilityZones[].RegionName' --output text --profile ${profile}|tr '\t' '\n' |sort -u`
	fi
	tput el
	echo -ne "Checking Profile: $profile in region: $region\\r"
	AllBuckets=( $(my_buckets.sh $profile | tail +5 | awk '{print $2}') )
	for bucket in ${AllBuckets[@]}; do
		out=$(aws s3api get-bucket-policy --bucket $bucket --output text --profile $profile --region $region | awk -F $"\t" -v var=${profile} -v rgn=${region} -v fmt="${format}" -v bckt=${bucket} '{printf fmt,var,rgn,bckt,$1}'|tee /dev/tty)
	done
	# echo "----- Output: "$out"-------"
	if [[ $out ]]
		then
			echo "------------"
	fi
done

echo
exit 0
