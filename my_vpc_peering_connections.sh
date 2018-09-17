#!/bin/bash

#!/bin/bash

profile=$1
region=$2

if [[ -z $profile ]]
	then
		echo
		echo "This command requires that you pass in the AWS profile name you're looking up"
		echo "Therefore, the script should be run like this:"
		echo "	$0 <profile name>"
		echo
		echo "Optionally - you can also include the region, but just the name, like this:"
		echo
		echo "	$0 <profile name> us-east-1"
		exit 1
fi

echo "Outputting all VPCs, only from ${profile:="default"}, and only from ${region:="us-east-1"}"
format='%-20s %-13s %-13s %-21s %-13s %-24s %-24s %-15s \n'

printf "$format" "Profile" "My Acct ID" "Req Acct ID" "Req VPC ID" "Acptr Acct ID" "Acptr VPC ID" "Peer Connection ID" "Status Message"
printf "$format" "-------" "----------" "-----------" "----------" "-------------" "------------" "------------------" "--------------"
my_account_id=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
aws ec2 describe-vpc-peering-connections --query 'VpcPeeringConnections[].[RequesterVpcInfo.OwnerId,RequesterVpcInfo.VpcId,AccepterVpcInfo.OwnerId,AccepterVpcInfo.VpcId,VpcPeeringConnectionId,Status.Message]' --filter 'Name=status-code,Values=active,pending,provisioning,deleting,pending-acceptance' --output text --profile $profile | awk -F $"\t" -v var=${profile} -v my_acct_id=${my_account_id} -v fmt="${format}" '{printf fmt,var,my_acct_id,$1,$2,$3,$4,$5,$6}'

echo
exit 0
