#!/usr/bin/python

# This script allows users to access Display Manager through the command line.

import sys
import os
import re
import argparse
from display_manager_lib import *


class CommandSyntaxError(Exception):
    """
    Raised if commands have improper syntax (e.g.
    """
    pass


class CommandValueError(Exception):
    """
    Raised if commands have improper values
    """
    pass


# todo: this. see display_manager.py
def getCommand(commandString):
    return commandString


def parseCommands(string):
    """
    :param string: The string to get Commands from
    :return: Commands contained within the string
    """
    # The types of commands that can be issued
    verbs = ["list", "res", "brightness", "rotate", "underscan", "mirror"]

    # The first command does not start with a valid verb
    if sys.argv[1] not in verbs:
        # todo: add "showHelp" or analogous function here
        sys.exit(1)

    # Find all of the indices in string that are verbs
    verbIndices = []
    for i in range(1, len(string)):
        if string[i] in verbs:
            verbIndices.append(i)

    # User entered only one command
    if len(verbIndices) == 0:
        return getCommand(" ".join(string))
    # User entered multiple commands
    else:
        # Split string along between verbs
        commandStrings = [" ".join(string[0:verbIndices[0]])]
        for j in range(1, len(verbIndices)):
            commandStrings.append(" ".join(string[verbIndices[j - 1]:verbIndices[j]]))
        commandStrings.append(" ".join(string[verbIndices[-1]:]))

        commands = CommandList()
        for commandString in commandStrings:
            command = getCommand(commandString)
            if command:
                commands.addCommand(command)
        return commands


def main():
    # Attempt to parse the commands
    try:
        commands = parseCommands(sys.argv[1:])
    except CommandSyntaxError:
        # todo: add "showHelp" or analogous function here
        sys.exit(1)


if __name__ == "__main__":
    main()
