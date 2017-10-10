#!/bin/bash

declare -a AllProfiles

#AllProfiles=(default Primary Secondary Nasdaq-Prod Nasdaq-Dev Nasdaq-DR)
AllProfiles=( $(~/GitRepos/Inventory_Scripts/Allprofiles.sh | awk '(NR>5 && $1 !~ /^-/) {print $1}') )

NumofProfiles=${#AllProfiles[@]}
echo "Found ${NumofProfiles} profiles in credentials file"
echo "Outputting all EFS File systems from all profiles"

printf "%-20s %-12s %-20s %-10s %-12s %-15s \n" "Profile" "FS Name" "Performance Mode" "State" "# of Mounts" "Size (Bytes)"
printf "%-20s %-12s %-20s %-10s %-12s %-15s \n" "-------" "-------" "----------------" "-----" "-----------" "------------"
for profile in ${AllProfiles[@]}; do
	aws efs describe-file-systems --output text --query 'FileSystems[*].[FileSystemId,PerformanceMode,LifeCycleState,NumberOfMountTargets,SizeInBytes.Value]' --profile $profile | awk -F $"\t" -v var=${profile} '{printf "%-20s %-12s %-20s %-10s %-12d %-15'"'"'d \n",var,$1,$2,$3,$4,$5}'
	echo "----------------"
done

echo
exit 0
