#!/bin/bash

# Script to test out and time the various python shell scripts in this directory

tool_to_test=$1

function exists_in_list() {
    LIST=$1
    DELIMITER=$2
    VALUE=$3
    LIST_WHITESPACES=$(echo $LIST | tr "$DELIMITER" " ")
    for x in $LIST_WHITESPACES; do
        if [ "$x" = "$VALUE" ]; then
            return 0
        fi
    done
    return 1
}

scripts_to_not_test="Inventory_Modules.py recovery_stack_ids.py lock_down_stack_sets_role.py ArgumentsClass.py \
account_class.py ALZ_CheckAccount.py CT_CheckAccount.py delete_bucket_objects.py enable_drift_detection.py \
find_my_LZ_versions.py move_stack_instances.py RunOnMultiAccounts.py UpdateRoleToMemberAccounts.py vpc_modules.py \
recover_stack_ids.py setup.py"

declare -a arrScripts

if [[ -n "$tool_to_test" ]]
  then
    arrScripts=("$tool_to_test")
  else
    for file in *.py
    do
      if exists_in_list "$scripts_to_not_test" " " "$file" ;
        then
          echo "Not trying to run $file"
        else
          echo "Will test run $file"
          arrScripts=("${arrScripts[@]}" "$file")
      fi
    done
fi


for item in "${arrScripts[@]}"
do
  echo "Running $item"
  output_file="test_output_$item.txt"
  summary_file="test_output_summary.$(date).txt"
  echo $(date) > "$output_file"
#  echo $(tool_to_test) >> "$summary_file"
#  echo $(date) >> "$summary_file"
  $(begin_date=$(date) ; python "$item" >> "$output_file" ; echo $? >> "$output_file" ; echo $(date) >> "$output_file" ; echo $item >> "$summary_file"; echo $begin_date >> "$summary_file"; echo $(date) >> "$summary_file") &
done

