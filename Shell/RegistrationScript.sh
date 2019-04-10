#!/bin/bash

Username=$1
Profile=$2
UserPolicy="arn:aws:iam::aws:policy/AdministratorAccess"
AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $Profile)

aws iam create-user --user-name $Username --profile $Profile
read a b c <<< $(aws iam create-access-key --user-name $Username --profile $Profile --query 'AccessKey.[UserName,AccessKeyId,SecretAccessKey]' --output text )
AccessKey=$b
SecretAccessKey=$c
aws iam attach-user-policy --policy-arn $UserPolicy --user-name $Username --profile $Profile
echo "Account Number: $AccountNumber"
echo "User: $Username"
echo "AccessKey: $AccessKey"
echo "SecretAccessKey: $SecretAccessKey"
echo
echo "Now go to Isengard and use this data to register the new account"
read -p "Hit return when finished:"
echo
echo "Now removing the user we just created"
aws iam detach-user-policy --user-name $Username --profile $Profile --policy-arn $UserPolicy
aws iam update-access-key --profile $Profile --user-name $Username --access-key-id $AccessKey --status Inactive
aws iam delete-access-key --user-name $Username --profile $Profile --access-key-id $AccessKey
aws iam delete-user --user-name $Username --profile $Profile
echo
echo "Checking that we've removed all users:"
aws iam list-users --profile $Profile --query 'Users[].UserName' --output text
