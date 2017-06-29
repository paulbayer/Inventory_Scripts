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

list_ec2(){
		echo
		./all_my_instances.sh
		echo
		pause
}

# do something in two()
list_s3(){
		echo
		./all_my_buckets.sh
		echo
		pause
}

list_topics(){
		echo
		./all_my_topics.sh
		echo
		pause
}

list_streams(){
		echo
		./all_my_streams.sh
		echo
		pause
}

list_s3_with_size(){
		echo
		./all_my_buckets_with_sizes.sh
		echo
		pause
}

profiles(){
		echo
		egrep '\[.*\]' ~/.aws/credentials | tr -d '[]\r'
		echo
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
		echo "9. Display all profiles available in your credentials file"
		echo "0. Exit"
}
# read input from the keyboard and take an action
# invoke the one() when the user select 1 from the menu option.
# invoke the two() when the user select 2 from the menu option.
# invoke the three() when the user select 3 from the menu option.
# Exit when user the user selects 4 from the menu option.
read_options(){
		local choice
		read -p "Enter choice [ 0 - 9] " choice
		case $choice in
				1) list_ec2 ;;
				2) list_s3 ;;
				3) list_s3_with_size ;;
				4) list_topics ;;
				5) list_streams ;;
				9) profiles ;;
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
