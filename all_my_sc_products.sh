#!/bin/bash

declare -a AllProfiles

echo "Gathering your profiles..."
AllProfiles=( $(AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

format='%-20s %-20s %-50s \n'

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all Service Catalog Products from all profiles"

printf "$format" "Profile" "Product Name" "Product ID"
printf "$format" "-------" "------------" "----------"
for profile in ${AllProfiles[@]}; do
	aws servicecatalog search-products-as-admin --query 'ProductViewDetails[].[ProductViewSummary.Name,ProductARN]' --output text --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" 'printf fmt,var,$1,$2}'
	echo "----------------"
done

echo
exit 0
