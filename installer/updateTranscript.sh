#!/bin/bash

if [[ $EUID -ne 0 ]] ; then  # script must be run as root
	echo "Script must be run as root."
	exit 1
fi

if [[ -z $1 ]] ; then  # if the first command-line argument (the version info) is an empty string
	echo "No version supplied."
	exit 1
fi

# Determine filename dynamically with date and version
filename="display-manager""_""$1""_"`date +%Y.%m.%d`"_""ad.T"

if [[ ! -f /Volumes/adamd/transcript/tech_adam/$filename ]] ; then  # can't "lcksum" a transcript that doesn't exist yet
	echo "No transcript for today yet. Make a new one!"
fi

# Copy new files to the radmind server
cp /Volumes/Data/Users/u1036693/projects/display_manager/display_manager_lib.py /Volumes/adamd/file/tech_adam/$filename/Library/Python/2.7/site-packages
cp /Volumes/Data/Users/u1036693/projects/display_manager/display_manager.py /Volumes/adamd/file/tech_adam/$filename/usr/local/bin

# Update transcript with new checksums
lcksum -Ic sha1 /Volumes/adamd/transcript/tech_adam/$filename
