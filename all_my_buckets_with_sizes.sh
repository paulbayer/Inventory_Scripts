#!/bin/bash

declare -a AllProfiles
declare -a ProfileBuckets
now=$(date +%s)

#AllProfiles=(default Primary Secondary Nasdaq-Prod Nasdaq-Dev Nasdaq-DR)
AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all S3 buckets from all profiles"

printf "%-20s %-60s %15s %18s \n" "Profile" "Bucket Name" "Number of Files" "Total Size (Bytes)"
printf "%-20s %-60s %15s %18s \n" "-------" "-----------" "---------------" "------------------"
for profile in ${AllProfiles[@]}; do
	ProfileBuckets=( $(aws s3api list-buckets --output text --query 'Buckets[*].Name' --profile $profile) )
	# aws s3api list-buckets --output text --query 'Buckets[*].Name' --profile $profile | awk -F $"\t" -v var=${profile} '{for (i=1;i<=NF;i++) printf "%-20s %-50s \n",var,$i}'
	for bucket in ${ProfileBuckets[@]}; do
			#aws s3api list-objects --bucket $bucket --query 'Contents[].[Key,Size]' --output text --profile $profile | awk -v bucketname=${bucket} -v profilename=${profile} '{s+=$2;++i;}; END {printf "%-20s %-60s %'"'"'15d %'"'"'18d \n",profilename,bucketname,i,s; }'
			#aws cloudwatch get-metric-statistics --profile $profile --namespace AWS/S3 --start-time "$(echo "$now - 86400" | bc)" --end-time "$now" --period 86400 --statistics Average --metric-name BucketSizeBytes --dimensions Name=BucketName,Value="$bucket" Name=StorageType,Value=StandardStorage --output text | awk -v bucketname=${bucket} -v profilename=${profile} 'NR>1 {printf "%-20s %-60s %'"'"'15d %'"'"'18d \n",profilename,bucketname,"N/A",$2}'
			bucketsize=$(aws cloudwatch get-metric-statistics --profile $profile --namespace AWS/S3 --start-time "$(echo "$now - 86400" | bc)" --end-time "$now" --period 86400 --statistics Average --metric-name BucketSizeBytes --dimensions Name=BucketName,Value="$bucket" Name=StorageType,Value=StandardStorage --output text | awk 'NR>1 {printf "%'"'"'15d",$2}')
			bucketcount=$(aws cloudwatch get-metric-statistics --profile $profile --namespace AWS/S3 --start-time "$(echo "$now - 86400" | bc)" --end-time "$now" --period 86400 --statistics Average --metric-name NumberOfObjects --dimensions Name=BucketName,Value="$bucket" Name=StorageType,Value="AllStorageTypes" --output text | awk 'NR>1 {printf "%'"'"'15d",$2}')
			printf "%-20s %-60s %15s %18s \n" $profile $bucket $bucketcount $bucketsize
	done
	echo "-----------------------"
done

echo
exit 0
