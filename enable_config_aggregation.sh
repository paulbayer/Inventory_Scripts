#!/bin/bash

declare -a AllProfiles
declare -a RegionList

echo "Gathering your profiles..."
AllProfiles=( $(AllProfiles.sh ProfileNameOnly | awk '{print $1}') )
RegionList=( $(aws ec2 describe-regions --output text --query 'Regions[].RegionName' | sed -e 's/	/","/g' | sed -E 's/^(.)/"\1/g'| sed -E 's/$/"/g') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Enabling Config Aggregation across all profiles"


for profile in ${AllProfiles[@]}; do
	for region in ${RegionList[*]}; do
		echo "aws configservice put-aggregation-authorization --authorized-account-id 311204252865 --authorized-aws-region ${region} --profile ${profile}"
	done
	echo "*** Finished Profile ${profile} ***"
done

echo
exit 0
