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
        "usage: display_manager.py {{ help | show | res | brightness | rotate | underscan | mirror }}",
        "",
        "Type any of the commands after \"help\" to get command-specific usage information:",
        "   help        Show this help information.",
        "   res         Set the display resolution.",
        "   show        Show current/available display configurations.",
        "   brightness  Control display brightness.",
        "   rotate      Control display rotation.",
        "   underscan   Show or set the current display underscan.",
        "   mirror      Enable or disable screen mirroring.",
    ]), "res": "\n".join([
        "usage: display_manager.py res [command] [options] [scope]",
        "   [exact] [highest]",
        "   [-r refresh] [--no-hidpi] [--only-hidpi]",
        "",
        "COMMANDS",
        "   exact (default) Set the display settings to the exact specifications.",
        "   highest         Set the display settings to the highest supported resolution.",
        "",
        "OPTIONS",
        "   -r refresh      Refresh rate (default: 0).",
        "   --no-hidpi      Don\'t use HiDPI resolutions.",
        "   --only-hidpi    Only use HiDPI resolutions.",
        "",
        "SCOPE",
        "   main (default)  Perform this command on the main display.",
        "   ext<N>          Perform this command on external display number <N>.",
        "   all             Perform this command on all connected displays.",
    ]), "show": "\n".join([
        "usage: display_manager.py show [command] [options] [scope]",
        "   [--no-hidpi] [--only-hidpi]",
        "",
        "COMMANDS",
        "   current     Show current display settings.",
        "   highest     Show the highest available resolution, and current settings.",
        "   all         Show all available resolutions, and current settings.",
        "   displays    List the current displays and their display tags (for <SCOPE> fields).",
        "",
        "OPTIONS",
        "   --no-hidpi      Don\'t show HiDPI settings.",
        "   --only-hidpi    Only show HiDPI settings.",
        "",
        "SCOPE",
        "   main            Perform this command on the main display.",
        "   ext<N>          Perform this command on external display number <N>.",
        "   all (default)   Perform this command on all connected displays.",
    ]), "brightness": "\n".join([
        "usage: display_manager.py brightness [value] [scope]",
        "",
        "VALUE",
        "   A number between 0 and 1, where 0 is minimum brightness, and 1 is maximum brightness.",
        "",
        "SCOPE",
        "   main (default)  Perform this command on the main display.",
        "   ext<N>          Perform this command on external display number <N>.",
        "   all             Perform this command on all connected displays.",
    ]), "rotate": "\n".join([
        "usage: display_manager.py rotate [value] [scope]",
        "",
        "VALUE",
        "   The number of degrees to rotate the display. Must be a multiple of 90.",
        "",
        "SCOPE",
        "   main (default)  Perform this command on the main display.",
        "   ext<N>          Perform this command on external display number <N>.",
        "   all             Perform this command on all connected displays.",
    ]), "underscan": "\n".join([
        "usage: display_manager.py underscan [value] [scope]",
        "",
        "VALUE",
        "   A number between 0 and 1, where 0 is minimum underscan, and 1 is maximum underscan.",
        "",
        "SCOPE",
        "   main (default)  Perform this command on the main display.",
        "   ext<N>          Perform this command on external display number <N>.",
        "   all             Perform this command on all connected displays.",
    ]), "mirror": "\n".join([
        "usage: display_manager.py mirror [command] [source] [target]",
        "   [-d display] [-m display]",
        "",
        "COMMANDS",
        "   enable      Enable mirroring.",
        "   disable     Disable mirroring.",
        "",
        "SOURCE/TARGET",
        "   source  The display which will be mirrored by the target(s). Identified by <SCOPE> tag. Cannot be \"all\".",
        "   target  The display(s) which will mirror the source. Identified by <SCOPE> tag.",
        "",
        "SCOPE",
        "   main    The main display.",
        "   ext<N>  External display number <N>.",
        "   all     All connected displays besides [source]. Only available to [target].",
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
