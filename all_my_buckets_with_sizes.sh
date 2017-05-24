#!/bin/bash

declare -a AllProfiles
declare -a ProfileBuckets

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
			aws s3api list-objects --bucket $bucket --query 'Contents[].[Key,Size]' --output text --profile $profile | awk -v bucketname=${bucket} -v profilename=${profile} '{s+=$2;++i;}; END {printf "%-20s %-60s %'"'"'15d %'"'"'18d \n",profilename,bucketname,i,s; }' 
	done
	echo "-----------------------"
done

echo
exit 0
