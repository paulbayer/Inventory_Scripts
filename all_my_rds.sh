#!/bin/bash

declare -a AllProfiles

#AllProfiles=(default Primary Secondary Nasdaq-Prod Nasdaq-Dev Nasdaq-DR)
AllProfiles=( $(./Allprofiles.sh programmatic | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all RDS Clusters from all profiles"

printf "%-20s %-20s %-10s %12s %-10s %-25s %-12s \n" "Profile" "Database Name" "DB Engine" "Storage (GB)" "Encrypted?" "Creation Time" "Status"
printf "%-20s %-20s %-10s %12s %-10s %-25s %-12s \n" "-------" "-------------" "---------" "------------" "----------" "-------------" "------"
for profile in ${AllProfiles[@]}; do
	aws rds describe-db-clusters --output text --query 'DBClusters[].[DatabaseName,Engine,AllocatedStorage,StorageEncrypted,ClusterCreateTime,Status]' --profile $profile | awk -F $"\t" -v var=${profile} '{printf "%-20s %-20s %-10s %12s %-10s %-25s %-12s \n",var,$1, $2, $3, $4, $5, $6}'
	echo "----------------"
done

echo
exit 0

2017-06-30T14:09:29.651Z
