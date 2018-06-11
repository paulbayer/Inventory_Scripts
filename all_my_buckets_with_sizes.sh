#!/bin/bash

declare -a AllProfiles
declare -a ProfileBuckets
now=$(date +%s)

echo "Gathering your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all S3 buckets from all profiles"

format='%-20s %-60s %15s %18s \n'

printf "$format" "Profile" "Bucket Name" "Number of Files" "Total Size (Bytes)"
printf "$format" "-------" "-----------" "---------------" "------------------"
for profile in ${AllProfiles[@]}; do
	ProfileBuckets=( $(aws s3api list-buckets --output text --query 'Buckets[*].Name' --profile $profile) )
	for bucket in ${ProfileBuckets[@]}; do
			bucketsize=$(aws cloudwatch get-metric-statistics --profile $profile --namespace AWS/S3 --start-time "$(echo "$now - 86400" | bc)" --end-time "$now" --period 86400 --statistics Average --metric-name BucketSizeBytes --dimensions Name=BucketName,Value="$bucket" Name=StorageType,Value=StandardStorage --output text | awk 'NR>1 {printf "%'"'"'15d",$2}')
			bucketcount=$(aws cloudwatch get-metric-statistics --profile $profile --namespace AWS/S3 --start-time "$(echo "$now - 86400" | bc)" --end-time "$now" --period 86400 --statistics Average --metric-name NumberOfObjects --dimensions Name=BucketName,Value="$bucket" Name=StorageType,Value="AllStorageTypes" --output text | awk 'NR>1 {printf "%'"'"'15d",$2}')
			printf "$format" $profile $bucket $bucketcount $bucketsize
	done
	echo "-----------------------"
done

echo
exit 0
