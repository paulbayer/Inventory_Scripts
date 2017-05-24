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

one(){
		echo 
		./all_my_instances.sh
		echo
		pause
}

# do something in two()
two(){
		echo 
		./all_my_buckets.sh
		echo
		pause
}

three(){
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
		echo "3. Display all profiles available in your credentials file"
		echo "4. Exit"
}
# read input from the keyboard and take an action
# invoke the one() when the user select 1 from the menu option.
# invoke the two() when the user select 2 from the menu option.
# Exit when user the user selects 4 form the menu option.
read_options(){
		local choice
		read -p "Enter choice [ 1 - 4] " choice
		case $choice in
				1) one ;;
				2) two ;;
				3) three ;;
				4) exit 0;;
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

