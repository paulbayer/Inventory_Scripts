#! /bin/bash

# This script should create an IAM policy within a given account

profile=$1

if [ -z $profile ] ;
	then
		echo "	When you run this script, you need to supply an account ID to use"
		echo "	Like: $0 <profile>"
		echo
		exit 1
fi

# Captures the AccountNumber for the specific profile account
AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)

#Creates the policy file specific to this account from the template (in my filesystem)
sed -e "s/\<account id\>/$AccountNumber/g" /Users/paulbaye/WorkDocs/localwork/bin/Policies/CloudWatchLogs/CloudTrailLogs.json > CloudTrailLogs_$AccountNumber.json
#Creates the policy in the AWS account from the policy file created above
#At the same, it captures the ARN of the created policy, to refer to it later
PolicyArn=$(aws iam create-policy --policy-name CloudTrailLogs --policy-document file://CloudTrailLogs_$AccountNumber.json --profile $profile | grep Arn | cut -d ":" -f 2- | tr -d ",\"")

# Debugging
#echo $PolicyArn

#Creates the role for CloudTrail to log all events
aws iam create-role --role-name CloudTrail_Role --assume-role-policy-document file:///Users/paulbaye/WorkDocs/localwork/bin/Policies/CloudWatchLogs/TrustPolicy_CloudTrail.json --profile $profile

#Applies the policy created above, to the role created above
aws iam attach-role-policy --role-name CloudTrail_Role --policy-arn $PolicyArn --profile $profile

#Now the the role exists that can add events to a CloudTrail... we need to create a trail, and then enable that trail to write events to our centralized, shared S3 bucket.
aws cloudtrail create-trail --name CloudTrailLogs --s3-bucket-name my-aggcloudtrail-bucket 
