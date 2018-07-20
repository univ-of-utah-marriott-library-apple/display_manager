#!/bin/bash

if [ $EUID -ne 0 ] ; then  # script must be run as root
	echo "Script must be run as root."
	exit 1
fi

if [ -z $1 ] ; then  # if the first command-line argument (the version info) is an empty string
	echo "No version supplied."
	exit 1
fi

# Make sure we're working in the right directory
cd "/Volumes/Data/Users/u1036693/projects/display_manager/installer"

# Copy all necessary files to ROOT
mkdir -p ROOT/Library/Python/2.7/site-packages
cp ../display_manager_lib.py ROOT/Library/Python/2.7/site-packages
mkdir -p ROOT/usr/local/bin
cp ../display_manager.py ROOT/usr/local/bin

# Make a standalone app out of gui.py, then move it to the necessary location
cd app  # if we don't "cd", then we create extra trash files in the wrong place
/usr/bin/python setup.py py2app
cd ..  # go back to script-level dir
mkdir -p ROOT/Applications
mv "app/dist/Display Manager.app" ROOT/Applications
	
# Builds a preliminary package which is referenced in "distribution.xml"
pkgbuild --identifier edu.utah.scl.display_manager --version $1 --root ./ROOT prelim.pkg
# Rebuilds the former package with "distribution.xml" and "Resources/"
productbuild --distribution distribution.xml --resources Resources/ "Display Manager.pkg"

# Builds the uninstaller
pkgbuild --nopayload --scripts scripts/ --identifier edu.scl.display_manager "Uninstall Display Manager.pkg"

# Move the packages to the pkg folder for imaging
mkdir pkg
mv "Display Manager.pkg" "./pkg/Display Manager.pkg"
mv "Uninstall Display Manager.pkg" "./pkg/Uninstall Display Manager.pkg"
# Create an image from the pkg folder
hdiutil create -srcfolder pkg/ -volname "Display Manager" -ov "../versions/Display Manager v$1"

# Remove unnecessary helper files
rm -rf prelim.pkg
rm -rf ROOT/
rm -rf pkg/
rm -rf app/build
rm -rf app/dist

# Very important reminder!
echo "REMEMBER TO CHANGE THE LINK TO CURRENT PACKAGE INSTALLER IN README.md, IN BOTH PLACES"
