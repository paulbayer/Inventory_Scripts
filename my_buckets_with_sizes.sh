#!/bin/bash

declare -a ProfileBuckets
now=$(date +%s)

profile=$1

if [[ -z $profile ]]
	then
		echo
		echo "This command requires that you pass in the AWS profile name you're looking up"
		echo "Therefore, the script should be run like this:"
		echo "	$0 <profile name>"
		echo
		exit 1
fi

echo
format='%-20s %-60s %15s %18s \n'

echo "Outputting all S3 buckets from profile: $profile"

printf "${format}" "Profile" "Bucket Name" "Number of Files" "Total Size (Bytes)"
printf "${format}" "-------" "-----------" "---------------" "------------------"
ProfileBuckets=( $(aws s3api list-buckets --output text --query 'Buckets[*].Name' --profile $profile) )
for bucket in ${ProfileBuckets[@]}; do
		bucketsize=$(aws cloudwatch get-metric-statistics --profile $profile --namespace AWS/S3 --start-time "$(echo "$now - 86400" | bc)" --end-time "$now" --period 86400 --statistics Average --metric-name BucketSizeBytes --dimensions Name=BucketName,Value="$bucket" Name=StorageType,Value=StandardStorage --output text | awk 'NR>1 {printf "%'"'"'15d",$2}')
		bucketcount=$(aws cloudwatch get-metric-statistics --profile $profile --namespace AWS/S3 --start-time "$(echo "$now - 86400" | bc)" --end-time "$now" --period 86400 --statistics Average --metric-name NumberOfObjects --dimensions Name=BucketName,Value="$bucket" Name=StorageType,Value="AllStorageTypes" --output text | awk 'NR>1 {printf "%'"'"'15d",$2}') 
		printf "${format}" $profile $bucket $bucketcount $bucketsize
done
echo "-----------------------"
echo
exit 0
