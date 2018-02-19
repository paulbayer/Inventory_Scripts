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

echo "Outputting all Groups from $profile"
format='%-15s %-45s %-20s %-55s \n'
# format='%-15s %-35s %-20s %-55s %-35s \n'

echo "Outputting all Lambda Functions and Roles from $profile"

printf "$format" "Profile" "Function Name" "Runtime" "Role"
printf "$format" "-------" "-------------" "-------" "----"
# printf "$format" "Profile" "Function Name" "Runtime" "Role" "Description"
# printf "$format" "-------" "-------------" "-------" "----" "-----------"
# aws lambda list-functions --output text --query 'Functions[].[FunctionName,Runtime,Role,Description]' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2,$3,$4}'
aws lambda list-functions --output text --query 'Functions[?contains(Role,`SSGSBilling_` == `true`)].[FunctionName,Runtime,Role]' --profile $profile | awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1,$2,$3}'

echo
exit 0
