#! /bin/bash

function geteverything () {
printf "%-20s %-30s %-20s \n" "Profile" "Resource Type" "Resource Name"
printf "%-20s %-30s %-20s \n" "-------" "-------------" "-------------"
aws configservice list-discovered-resources --resource-type AWS::EC2::CustomerGateway --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::EIP --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::Host --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::Instance --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::InternetGateway --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::NetworkAcl --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::NetworkInterface --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::RouteTable --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::SecurityGroup --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::Subnet --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::Volume --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::VPC --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::VPNConnection --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::EC2::VPNGateway --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
echo "-------------------------------"
aws configservice list-discovered-resources --resource-type AWS::IAM::Group --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::IAM::Policy --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::IAM::Role --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::IAM::User --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
echo "-------------------------------"
aws configservice list-discovered-resources --resource-type AWS::ACM::Certificate --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
echo "-------------------------------"
aws configservice list-discovered-resources --resource-type AWS::RDS::DBInstance --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::RDS::DBSubnetGroup --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::RDS::DBSecurityGroup --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::RDS::DBSnapshot --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::RDS::EventSubscription --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
echo "-------------------------------"
aws configservice list-discovered-resources --resource-type AWS::ElasticLoadBalancingV2::LoadBalancer --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
echo "-------------------------------"
aws configservice list-discovered-resources --resource-type AWS::S3::Bucket --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::SSM::ManagedInstanceInventory --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
echo "-------------------------------"
aws configservice list-discovered-resources --resource-type AWS::Redshift::Cluster --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::Redshift::ClusterSnapshot --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::Redshift::ClusterParameterGroup --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::Redshift::ClusterSecurityGroup --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::Redshift::ClusterSubnetGroup --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::Redshift::EventSubscription --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
echo "-------------------------------"
aws configservice list-discovered-resources --resource-type AWS::CloudTrail::Trail --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::CloudWatch::Alarm --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
aws configservice list-discovered-resources --resource-type AWS::CloudFormation::Stack --profile $profile --output text --query 'resourceIdentifiers[].[resourceType,resourceName]' | awk -F $"\t" -v var=${profile} '{printf "%-20s %-30s %-20s \n",var,$1, $2}'
}

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

geteverything
