#!/bin/bash

declare -a AllProfiles

echo "Capturing your profiles..."
AllProfiles=( $(./AllProfiles.sh ProfileNameOnly | awk '{print $1}') )

ProfileCount=${#AllProfiles[@]}
echo "Found ${ProfileCount} profiles in credentials file"
echo "Outputting all key pairs, only from your $profile profile"
format='%-20s %-20s \n'

printf "$format" "Profile" "Key Pair Name"
printf "$format" "-------" "-------------"
for profile in ${AllProfiles[@]}; do
	aws ec2 describe-key-pairs --profile $profile --output text --query 'KeyPairs[].KeyName' |tr '\t' '\n'| awk -F $"\t" -v var=${profile} -v fmt="${format}" '{printf fmt,var,$1}'
	echo "------------"
done
# cmd_line = "aws ec2 describe-key-pairs --profile $profile --query 'KeyPairs[].KeyName | awk -F $'\t' -v var=${profile} -v fmt=${format} '{printf fmt,var,$1}'"
# if [[ -z $region ]]
#   then
#     ${cmd_line}
#   else
#     ${cmd_line} --region $region

echo
exit 0
