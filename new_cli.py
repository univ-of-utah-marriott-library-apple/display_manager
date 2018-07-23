#!/usr/bin/python

# This script allows users to access Display Manager through the command line.

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


def showHelp(command=None):
    """
    :param command: The command to print information for.
    """
    print("Display Manager, version 1.0.0")

    usage = {"help": "\n".join([
        "usage: display_manager.py {{ help | set | show | brightness | rotate | mirror | underscan }}",
        "",
        "Use any of the commands with \"help\" to get more information:",
        "    help       Show this help information.",
        "    set        Set the display configuration.",
        "    show       Show available display configurations.",
        "    brightness Show or set the current display brightness.",
        "    rotate     Show or set display rotation.",
        "    mirror     Set mirroring configuration.",
        "    underscan  Show or set the current display underscan.",
    ]), "set": "\n".join([
        "usage: display_manager.py set {{ help | closest | highest | exact }}",
        "    [-d display] [-w width] [-h height] [-d pixel depth] [-r refresh]",
        "    [--no-hidpi] [--only-hidpi]",
        "",
        "commands",
        "    help       Print this help information.",
        "    closest    Set the display settings to the supported resolution that is closest to the specified values.",
        "    highest    Set the display settings to the highest supported resolution.",
        "    exact      Set the display settings to the specified values if they are supported. If they are not, "
        "don\'t change the display.",
        "",
        "OPTIONS",
        "    -w width           Resolution width.",
        "    -h height          Resolution height.",
        "    -p pixel-depth     Pixel color depth (default: 32).",
        "    -r refresh         Refresh rate (default: 0).",
        "    -d display         Specify a particular display (default: main display).",
        "    --no-hidpi         Don\'t show HiDPI settings.",
        "    --only-hidpi       Only show HiDPI settings.",
    ]), "show": "\n".join([
        "usage: display_manager.py show {{ help | all | closest | highest | current | displays }}",
        "    [-d display] [-w width] [-h height] [-d pixel depth] [-r refresh]",
        "    [--no-hidpi] [--only-hidpi]",
        "",
        "commands",
        "    help       Print this help information.",
        "    all        Show all supported resolutions for the display.",
        "    closest    Show the closest matching supported resolution to the specified values.",
        "    highest    Show the highest supported resolution.",
        "    current    Show the current display configuration.",
        "    displays   List the current displays and their IDs.",
        "",
        "OPTIONS",
        "    -w width           Resolution width.",
        "    -h height          Resolution height.",
        "    -p pixel-depth     Pixel color depth (default: 32).",
        "    -r refresh         Refresh rate (default: 0).",
        "    -d display         Specify a particular display (default: main display).",
        "    --no-hidpi         Don\'t show HiDPI settings.",
        "    --only-hidpi       Only show HiDPI settings.",
        "",
    ]), "brightness": "\n".join([
        "usage: display_manager.py brightness {{ help | show | set [val] }}",
        "    [-d display]",
        "",
        "commands",
        "    help       Print this help information.",
        "    show       Show the current brightness setting(s).",
        "    set [val]  Sets the brightness to the given value. Must be between 0 and 1.",
        "",
        "OPTIONS",
        "    -d display         Specify a particular display (default: main display).",
    ]), "rotate": "\n".join([
        "usage: display_manager.py rotate {{ help | show | set [val] }}",
        "    [-d display]",
        "commands",
        "    help       Print this help information.",
        "    show       Show the current display rotation.",
        "    set [val]  Set the rotation to the given angle (in degrees). Must be a multiple of 90.",
        "",
        "OPTIONS",
        "    -d display         Specify a particular display (default: main display).",
    ]), "underscan": "\n".join([
        "usage: display_manager.py underscan {{ help | show | set [val] }}",
        "    [-d display]",
        "",
        "commands",
        "    help       Print this help information.",
        "    show       Show the current underscan setting(s).",
        "    set [val]  Sets the underscan to the given value. Must be between 0 and 1.",
        "OPTIONS",
        "    -d display         Specify a particular display (default: main display).",
    ]), "mirror": "\n".join([
        "usage: display_manager.py mirror {{ help | set | disable }}",
        "    [-d display] [-m display]",
        "",
        "commands",
        "    help       Print this help information.",
        "    set        Activate mirroring.",
        "    disable    Deactivate all mirroring.",
        "",
        "OPTIONS",
        "    -d display         Change mirroring settings for \"display\" (default: main display).",
        "    -m display         Set the display to mirror \"display\".",
    ])}

    if command in usage:
        print(usage[command])
    else:
        print(usage["help"])


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
