#!/usr/bin/python

# This script allows users to access Display Manager through the command line.

import sys
import os
import re
import argparse
from display_manager_lib import *


def main():
    # The types of commands that can be issued
    verbs = ["list", "resolution", "brightness", "rotate", "underscan", "mirror"]
    rawCommandString = sys.argv[1:]

    for word in rawCommandString:
        if word in verbs:
            # todo: you know what to do
            pass

    # No valid commands were received
    if verbs not in rawCommandString:
        # todo: add "showHelp" or analogous function here
        sys.exit(1)


if __name__ == "__main__":
    main()
