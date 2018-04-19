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

format='%-15s %-36s %-50s \n'

printf "$format" "Profile" "Athena Query ID" "Athena Query Name"
printf "$format" "-------" "---------------" "-----------------"

QueryIDs=$(aws athena list-named-queries --output text --query 'NamedQueryIds' --profile $profile | tr '\t' '\n')

for ID in ${QueryIDs[@]}; do
	QueryName=$(aws athena get-named-query --named-query-id $ID --query 'NamedQuery.[Name]' --profile $profile --output text)
	printf "$format" $profile $ID "$QueryName"	# The quotes on the 'QueryName' allow the name to be passed to printf as one argument, even when 'QueryName' has spaces.
done
echo "-----------------------"

echo
exit 0
