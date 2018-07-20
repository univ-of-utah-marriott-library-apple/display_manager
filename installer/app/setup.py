"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['../../gui.py']
APP_NAME = "Display Manager"
DATA_FILES = []
OPTIONS = {
	'iconfile': 'icon.icns',
	'argv_emulation': True,
	'plist': {
		'CFBundleName': APP_NAME,
		'CFBundleDisplayName': APP_NAME,
		'CFBundleIdentifier': "edu.utah.scl.display_manager",
		'CFBundleVersion': "1.0.0",
		'CFBundleShortVersionString': "1.0.0"
	}
}

setup(
	name=APP_NAME,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)