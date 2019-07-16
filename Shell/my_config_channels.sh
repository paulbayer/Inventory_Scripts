#!/bin/bash

### Yes - I would love to write this in a Python format, except that the Boto3 SDK doesn't support the Config Recorder or Config Delivery Channel commands yet.

# set -x

profile=$1
region=$2
region=${region:="us-east-1"}
deletion_run=$3

if [[ -z $profile ]]
	then
		echo
		echo "This command requires that you pass in the AWS profile name you're looking up"
		echo "Therefore, the script should be run like this:"
		echo "	$0 <profile name>"
		echo
		echo "Optionally - you can also include a specific region or all regions, like this:"
		echo
		echo "	$0 <profile name> us-east-1"
		echo "	$0 <profile name> all"
		echo
		echo "Additionally - you can also choose to delete the Config Recorder and Delivery Channel by"
		echo "adding a 'true' to the end of the line, like this:"
		echo
		echo "	$0 <profile name> all true"
		exit 1
fi

echo "Outputting Config Delivery Channels, only from $profile, and only from region: $region"
format='%-20s %-20s %-8s %-40s \n'

printf "$format" "Profile" "Region" "Type" "Name"
printf "$format" "-------" "------" "----" "----"
if [[ ! $region == "all" ]]
	then # The case where $regions is a specific region
		config_recorder_name=( $(aws configservice describe-configuration-recorder-status --query 'ConfigurationRecordersStatus[].name' --output text --profile $profile --region $region) )
		delivery_channel=( $(aws configservice describe-delivery-channel-status  --query 'DeliveryChannelsStatus[].name' --output text --profile $profile --region $region) )
		printf "$format" $profile $region "Recorder" $config_recorder_name
		printf "$format" $profile $region "Channel" $delivery_channel
		if [[ $deletion_run && ! -z $config_recorder_name ]]
			then
				printf "$format" $profile $region $config_recorder_name
				echo "Deleting Config Recorder & Delivery Channel from ${region}"
				aws configservice delete-configuration-recorder --configuration-recorder-name ${config_recorder_name} --profile ${profile} --region ${region}
				aws configservice delete-delivery-channel --delivery-channel-name ${delivery_channel} --profile ${profile} --region ${region}
				echo "Config Recorder $config_recorder_name has been deleted"
				echo "Delivery Channel $delivery_channel has been deleted"
				if [[ ! -z $config_recorder_name ]]
					then
						printf "$format" $profile $singleregion "Recorder" $config_recorder_name
				fi
				if [[ ! -z $delivery_channel ]]
					then
						printf "$format" $profile $singleregion "Channel" $delivery_channel
				fi
		elif [[ -z $config_recorder_name ]]
			then
				echo "There was no Config Recorder enabled for profile: $profile in region $region"
				#statements
		fi
	else # The case where $regions = "all"
		declare -a regions
		regions=( $(aws ec2 describe-regions --query 'Regions[].RegionName' --output text | tr '\t' '\n' | sort) )
		for singleregion in ${regions[@]}; do
				echo -en "\rChecking $singleregion in profile $profile\033[0K\r"
				config_recorder_name=( $(aws configservice describe-configuration-recorder-status --query 'ConfigurationRecordersStatus[].name' --output text --profile $profile --region $singleregion 2>/dev/null ) )
				delivery_channel=( $(aws configservice describe-delivery-channel-status  --query 'DeliveryChannelsStatus[].name' --output text --profile $profile --region $singleregion 2>/dev/null ) )
				if [[ ! -z $config_recorder_name ]]
					then
						printf "$format" $profile $singleregion "Recorder" $config_recorder_name
				fi
				if [[ ! -z $delivery_channel ]]
					then
						printf "$format" $profile $singleregion "Channel" $delivery_channel
				fi
				if [[ $deletion_run && (! -z $config_recorder_name || ! -z $delivery_channel ) ]]
					then
						printf "$format" $profile $singleregion "Recorder" $config_recorder_name
						printf "$format" $profile $singleregion "Channel" $delivery_channel
						echo "Deleting Config Recorder and Delivery Channel from $singleregion"
						aws configservice delete-configuration-recorder --configuration-recorder-name ${config_recorder_name} --profile ${profile} --region ${singleregion}
						aws configservice delete-delivery-channel --delivery-channel-name ${delivery_channel} --profile ${profile} --region ${singleregion}
						echo "Config Recorder $config_recorder_name has been deleted"
						echo "Delivery Channel $delivery_channel has been deleted"
				fi
		done
fi
echo
exit 0
