#!/bin/bash

filepath=$1

if [[ -n "$filepath" ]]; then
    directory=$filepath
fi

objects=(Badges Users Tags Votes Posts PostLinks Comments)

read -p "This will drop all tables. Are you sure? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then

for i in "${objects[@]}"
do
   : 
   printf "\nProcessing $i object ... \n"

   added_arguments=""
   if [ $i = "Posts" ]; then
     added_arguments="--with-post-body"
   else
     added_arguments="--with-comment-text"  
   fi

   ./load_into_pg.py $i --file $directory/$i.xml -d stackexchange --suppress-drop-warning $added_arguments
done

fi