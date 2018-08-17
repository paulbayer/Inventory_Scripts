#!/bin/bash

declare -a AllProfiles

echo "Gathering your profiles..."
AllProfiles=( $(AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

format='%-12s %-40s %-12s %-50s \n'

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all Service Catalog Products from all profiles"

printf "$format" "Profile" "Product Name" "Status" "Product ID"
printf "$format" "-------" "------------" "------" "----------"
for profile in ${AllProfiles[@]}; do
	out=$(aws servicecatalog search-products-as-admin --query 'ProductViewDetails[].[ProductViewSummary.Name,Status,roductViewSummary.Id]' --output text --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2,$3}'|tee /dev/tty)
	if [[ $out ]]
		then
			echo "------------"
	fi
done

exit 0
