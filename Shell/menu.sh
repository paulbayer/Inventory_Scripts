#!/bin/bash

# This stuff enables the menu to look nice.
# Perhaps I'd refine this to take into account the terminal type,
# but I'm not that fancy right now.
RED=$(tput setaf 9) #'\033[0;41;30m'
ATTN=$(tput bold)
GREY=$(tput setaf 7)
RedError=$(tput setaf 9; tput setab 249; tput blink)
STD=$(tput init) #'\033[0;0;39m'

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
list_users_with_policies_single_profile(){
	read -t 10 -p "Enter the profile name you're interested in (default): " profile_name
	./users_with_policies.sh ${profile_name:=default}
	echo
	pause
}
list_groups_with_policies_single_profile(){
	read -t 10 -p "Enter the profile name you're interested in (default): " profile_name
	./groups_with_policies.sh ${profile_name:=default}
	echo
	pause
}
list_roles_with_policies_single_profile(){
	read -t 10 -p "Enter the profile name you're interested in (default): " profile_name
	./roles_with_policies.sh ${profile_name:=default}
	echo
	pause
}
list_policies_single_profile(){
	echo
	echo "This doesn't quite work yet..."
	#		./policies.sh
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
#RDS Function Section
list_RDS_clusters(){
	echo
	./all_my_rds.sh
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
# EC2 Security Group Listing for only the specified profile
list_secgrps_single_profile(){
	read -t 10 -p "Enter the profile name you're interested in (default): " profile_name
	./my_sec_groups.sh ${profile_name:=default}
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

# VPC Stuff
list_vpcs(){
	echo
	./all_my_vpcs.sh
	echo
	pause
}

list_subnets(){
	echo
	./all_my_subnets.sh
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
	./Allprofiles.sh
	echo
	pause
}

accountnumber(){
	read -t 10 -p "Enter the profile name you're interested in (default): " profile_name
	./my_account_number.sh ${profile_name:=default}
	echo
	pause
}

# function to display menus
show_menus() {
#		clear
	echo "~~~~~~~~~~~~~~~~~~~~~"
	echo " M A I N - M E N U"
	echo "~~~~~~~~~~~~~~~~~~~~~"
	echo "|Single |All"
	echo "|Accnts |Accounts"
	echo $RED"*** EC2 Stuff ***"$STD
	echo "|1s. 	|1a.	| Display EC2 Instances in ${ATTN}specified / all${STD} profile"
	echo "|6. 	|${GREY}106.${STD}	| Display EC2 Security Groups in your ${ATTN}specified${STD} profile"
	echo $RED"*** S3 Stuff ***"$STD
	echo "|${GREY}2.${STD}	|102.	| Display all S3 buckets in ${ATTN}specified / all${STD} of your profiles"
	echo "|${GREY}3.${STD}	|103.	| Display all S3 buckets in ${ATTN}specified / all${STD} of your profiles with a total size at the bottom"
	echo $RED"*** Networking Stuff ***"$STD
	echo "|	|111.	| Display all VPCs in ${ATTN}all${STD} of your profiles, with state and CIDR block"
	echo "|	|112.	| Display all subnets from ${ATTN}all${STD} of your profiles, with VPC assignments"
	echo $RED"***	| IAM Stuff for all of your accounts ***"$STD
	echo "|	|121.	| Display all IAM Users (with attached policies) in ${ATTN}all${STD} of your profiles (takes a while)"
	echo "|	|122.	| Display all IAM Groups (with attached policies) in ${ATTN}all${STD} of your profiles (takes a while)"
	echo "|	|123.	| Display all IAM Roles (with attached policies) in ${ATTN}all${STD} of your profiles (takes a while)"
	echo "|	|124.	| Display all IAM Customer-Managed Policies in ${ATTN}all${STD} of your profiles"
	echo $RED"***	| Config Rules for all of your accounts ***"$STD
	echo "|	|131.	| Display all Config Rules in ${ATTN}all${STD} of your profiles"
	echo $RED"***	| IAM Stuff for your specified profile ***"$STD
	echo "|51.	|	| Display all IAM Users (with attached policies) in your ${ATTN}specified${STD} profile"
	echo "|52.	|	| Display all IAM Groups (with attached policies) in your ${ATTN}specified${STD} profile"
	echo "|53.	|	| Display all IAM Roles (with attached policies) in your ${ATTN}specified${STD} profile"
	echo "|54.	|	| Display all IAM Customer-Managed Policies in your ${ATTN}specified${STD} profile"
	echo $RED"*** Database Stuff ***"$STD
	echo "|	|171.	| Display all DynamoDB Tables in ${ATTN}all${STD} of your profiles"
	echo "|	|172.	| Display all RDS Clusters in ${ATTN}all${STD} of your profiles"
	echo $RED"*** Other stuff ***"$STD
	echo "|	|190.	| Display all EFS Filesystems in ${ATTN}all${STD} of your profiles"
#	echo "|	|191.	| Display all Athena queries in all of your accounts"
	echo "|	|194.	| Display all SNS topics in ${ATTN}all${STD} of your profiles"
	echo "|	|195.	| Display all Kinesis streams in ${ATTN}all${STD} of your profiles"
	echo "|	|196.	| Display all Lambda functions in ${ATTN}all${STD} of your profiles"
	echo "|	|197.	| Display all CloudWatch Logs in ${ATTN}all${STD} of your profiles"
	echo "|	|198.	| Display all CloudFormation Stacks in ${ATTN}all${STD} of your profiles"
	echo "|	|199.	| Display all CloudTrail trails in ${ATTN}all${STD} of your profiles"
	echo $RED"P. Display all profiles available in your credentials file"$STD
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
				7) echo "Not ready yet" ;;
				8) list_cloudformation_stacks ;;
				9) list_cloudtrail_trails ;;
				10) list_filesystems ;;
				11) list_vpcs ;;
				12) list_subnets ;;
				21) list_users_with_policies ;;
				22) list_groups_with_policies ;;
				23) list_roles_with_policies ;;
				24) list_policies ;;
				31) list_all_config_rules ;;
				51) list_users_with_policies_single_profile ;;
				52) list_groups_with_policies_single_profile ;;
				53) list_roles_with_policies_single_profile ;;
				54) list_policies_single_profile ;;
				61) list_secgrps_single_profile ;;
				71) list_DDB_tables ;;
				72) list_RDS_clusters ;;
				[Pp]) profiles ;;
				[0qQ]) exit 0;;
				*) echo -e "${RedError} *** Error *** ${STD}" && sleep 2
		esac
}

# ----------------------------------------------
# Step #3: Trap CTRL+C, CTRL+Z and quit signals
# ----------------------------------------------
trap '' SIGINT SIGQUIT SIGTSTP

# -----------------------------------
# Step #4: Main logic - infinite loop
# ------------------------------------

cd ~/GitRepos/Inventory_Scripts
while true
do
		show_menus
		read_options
done
