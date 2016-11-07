#!/bin/bash


read -p "This will drop all tables. Are you sure? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
./load_into_pg.py Badges -d stackexchange --suppress-drop-warning
./load_into_pg.py Users -d stackexchange --suppress-drop-warning
./load_into_pg.py Tags -d stackexchange --suppress-drop-warning
./load_into_pg.py Votes -d stackexchange --suppress-drop-warning
./load_into_pg.py Posts -d stackexchange --suppress-drop-warning --with-post-body
./load_into_pg.py PostLinks -d stackexchange --suppress-drop-warning
./load_into_pg.py Comments -d stackexchange --suppress-drop-warning --with-comment-text
fi