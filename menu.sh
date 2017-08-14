#!/bin/bash

# A menu driven shell script sample template
## ----------------------------------
# Step #1: Define variables
# ----------------------------------
EDITOR=vim
PASSWD=/etc/passwd
RED='\033[0;41;30m'
STD='\033[0;0;39m'

# ----------------------------------
# Step #2: User defined function
# ----------------------------------
pause(){
		read -p "Press [Enter] key to continue..." fackEnterKey
}

# IAM Function Section
list_users_with_policies(){
		echo
		./all_my_users_with_policies.sh
		echo
		pause
}
list_groups_with_policies(){
		echo
		./all_my_groups_with_policies.sh
		echo
		pause
}
list_roles_with_policies(){
		echo
		./all_my_roles_with_policies.sh
		echo
		pause
}
list_policies(){
		echo
		./all_my_policies.sh
		echo
		pause
}

#DynamoDB Function Section
list_DDB_tables(){
		echo
		./all_my_DDB_tables.sh
		echo
		pause
}

#Lambda Functions
list_functions(){
		echo
		./all_my_functions.sh
		echo
		pause
}

#EC2 Instance functions
list_ec2(){
		echo
		./all_my_instances.sh
		echo
		pause
}

#S3 Stuff
list_s3(){
		echo
		./all_my_buckets.sh
		echo
		pause
}
list_s3_with_size(){
		echo
		./all_my_buckets_with_sizes.sh
		echo
		pause
}

#SNS Topics
list_topics(){
		echo
		./all_my_topics.sh
		echo
		pause
}

#Kinesis streams
list_streams(){
		echo
		./all_my_streams.sh
		echo
		pause
}

#CFT Stacks
list_cloudformation_stacks(){
		echo
		./all_my_stacks.sh
		echo
		pause
}

#CloudTrails
list_cloudtrail_trails(){
		echo
		./all_my_trails.sh
		echo
		pause
}

#EFS Filesystems
list_filesystems(){
		echo
		./all_my_filesystems.sh
		echo
		pause
}

#Config Rules
list_all_config_rules(){
		echo
		./all_my_config_rules.sh
		echo
		pause
}

profiles(){
		echo
		declare -a AllProfiles
		AllProfiles=$(egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r')
		printf "%-15s %-20s \n" "Profile Name" "Account Number"
		printf "%-15s %-20s \n" "------------" "--------------"
		for profile in ${AllProfiles[@]}; do
			AccountNumber=$(aws sts get-caller-identity --output text --query 'Account' --profile $profile)
			printf "%-15s %-20s \n" $profile $AccountNumber
		done
		pause
}

# function to display menus
show_menus() {
#		clear
		echo "~~~~~~~~~~~~~~~~~~~~~"
		echo " M A I N - M E N U"
		echo "~~~~~~~~~~~~~~~~~~~~~"
		echo "1. Display all EC2 Instances in all of your accounts"
		echo "2. Display all S3 buckets in all of your accounts"
		echo "3. Display all S3 buckets in all of your accounts with a total size at the bottom"
		echo "4. Display all SNS topics in all of your accounts"
		echo "5. Display all Kinesis streams in all of your accounts"
		echo "6. Display all Lambda functions in all of your accounts"
		echo "7. Display all DynamoDB Tables in all of your accounts"
		echo "8. Display all CloudFormation Stacks in all of your accounts"
		echo "9. Display all CloudTrail trails in all of your accounts"
		echo "10. Display all EFS Filesystems in all of your accounts"
		echo "21. Display all IAM Users (with attached policies) in all of your accounts (takes a while)"
		echo "22. Display all IAM Groups (with attached policies) in all of your accounts (takes a while)"
		echo "23. Display all IAM Roles (with attached policies) in all of your accounts (takes a while)"
		echo "24. Display all IAM Customer-Managed Policies in all of your accounts"
		echo "31. Display all Config Rules in all of your accounts"
		echo "P. Display all profiles available in your credentials file"
		echo "0. Exit"
}
# read input from the keyboard and take an action
# invoke the one() when the user select 1 from the menu option.
# invoke the two() when the user select 2 from the menu option.
# invoke the three() when the user select 3 from the menu option.
# Exit when user the user selects 4 from the menu option.
read_options(){
		local choice
		read -p "Enter choice [ 0 - 100] " choice
		case $choice in
				1) list_ec2 ;;
				2) list_s3 ;;
				3) list_s3_with_size ;;
				4) list_topics ;;
				5) list_streams ;;
				6) list_functions ;;
				7) list_DDB_tables ;;
				8) list_cloudformation_stacks ;;
				9) list_cloudtrail_trails ;;
				10) list_filesystems ;;
				21) list_users_with_policies ;;
				22) list_groups_with_policies ;;
				23) list_roles_with_policies ;;
				24) list_policies ;;
				31) list_all_config_rules ;;
				[Pp]) profiles ;;
				[0qQ]) exit 0;;
				*) echo -e "${RED}Error...${STD}" && sleep 2
		esac
}

# ----------------------------------------------
# Step #3: Trap CTRL+C, CTRL+Z and quit signals
# ----------------------------------------------
trap '' SIGINT SIGQUIT SIGTSTP

# -----------------------------------
# Step #4: Main logic - infinite loop
# ------------------------------------

while true
do
		show_menus
		read_options
done
