#!/bin/bash

lookupname=$1

echo ";;Name Server Information for $lookupname"
dig +answer +nocmd +nocomments +noquestion +nostats ns $lookupname. | sed "s/${lookupname}./@\t\t/"
echo ";;IP addres of Name Servers"
dig +answer +nocmd +nocomments +noquestion +nostats a `dig +short ns $lookupname.`

