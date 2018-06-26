#!/bin/bash

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

# mydir=$(mktemp -d "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")

declare -a QueryIDs
#declare -a
now=$(date +%s)

echo "Outputting all Athena Queries from your $profile profile"

format='%-20s %-50s %-50s \n'

printf "$format" "Profile" "Product Name" "Product ID"
printf "$format" "-------" "------------" "----------"

aws servicecatalog search-products-as-admin --query 'ProductViewDetails[].ProductViewSummary[].[Name,ProductId]' --output text --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2}'
echo "-----------------------"

echo
exit 0
