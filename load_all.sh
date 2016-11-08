#!/bin/bash

directory_option=""
database_option=""

while getopts "d:t:" opt; do
  case $opt in
    d)
      database_option="-d $OPTARG"
      ;;
    t)
      directory_option="--file $OPTARG/"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done

objects=(Badges Users Tags Votes Posts PostLinks Comments)

read -p "This will drop all tables. Are you sure? " -n 1 -r

if [[ $REPLY =~ ^[Yy]$ ]]
then

for i in "${objects[@]}"
do
   : 
   printf "\nProcessing $i object ... \n"

   _directory_option=""
   added_arguments=""
   if [ $i = "Posts" ]; then
     added_arguments="--with-post-body"
   elif [ $i = "Comments" ]; then
     added_arguments="--with-comment-text"  
   fi


   if [[ !  -z  $directory_option ]]
   then
       _directory_option=$directory_option$i.xml
   fi

   ./load_into_pg.py $i $_directory_option $database_option --suppress-drop-warning $added_arguments
done

fi