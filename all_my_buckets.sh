#!/bin/bash

declare -a AllProfiles
declare -a AllBuckets

#AllProfiles=(default Primary Secondary Nasdaq-Prod Nasdaq-Dev Nasdaq-DR)
AllProfiles=( $(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r') )

# AllBuckets=(

echo "Outputting all S3 buckets from all profiles"

printf "%-20s %-50s \n" "Profile" "Bucket Name" 
printf "%-20s %-50s \n" "-------" "-----------"
for profile in ${AllProfiles[@]}; do
	aws s3api list-buckets --output text --query 'Buckets[*].Name' --profile $profile | awk -F $"\t" -v var=${profile} '{for (i=1;i<=NF;i++) printf "%-20s %-50s \n",var,$i}' 

	# aws s3api list-objects --bucket $bucketname --query 'Contents[].[Key,Size]' --output text -- profile $profile | awk '{s+=$2;++i}; END {printf "%s %d %s %d %s \n","There are:",i,"files in the bucket; totaling:",s,"bytes."}'
done

echo
exit 0
