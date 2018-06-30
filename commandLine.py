#!/usr/bin/python

# This script allows users to access the DisplayManager program through the command line.
# Passes command parameters into DisplayManager.


import sys
import argparse
sys.path.append("..")  # to allow import from current directory
import DisplayManager as dm


def earlyExit():
    """
    Exits before actually doing anything when the user didn't enter enough parameters.
    """
    # If they don't include enough arguments, show help and exit with error
    if len(sys.argv) < 2:
        dm.showHelp()
        sys.exit(1)

    # Show help; exit is a success
    elif len(sys.argv) == 2 and sys.argv[1] == '--help':
        dm.showHelp()
        sys.exit(0)


def parse(parseList):
    """
    Parse the user command-line input.
    :return: A parser that has parsed all command-line arguments passed in.
    """
    parser = argparse.ArgumentParser(add_help=False)
    secondaries = parser.add_subparsers(dest='subcommand')

    help = secondaries.add_parser('help', add_help=False)
    help.add_argument('command', choices=['set', 'show', 'brightness', 'underscan', 'mirroring'],
                      nargs='?', default=None)

    set = secondaries.add_parser('set', add_help=False)
    set.add_argument('command', choices=['help', 'closest', 'highest', 'exact'], nargs='?', default='closest')

    show = secondaries.add_parser('show', add_help=False)
    show.add_argument('command', choices=['help', 'all', 'closest', 'highest', 'current', 'displays'],
                      nargs='?', default='all')

    brightness = secondaries.add_parser('brightness', add_help=False)
    brightness.add_argument('command', choices=['help', 'show', 'set'])
    brightness.add_argument('brightness', type=float, nargs='?', default=1)

    rotate = secondaries.add_parser('rotate', add_help=False)
    rotate.add_argument('command', choices=['help', 'set', 'show'], nargs='?', default='show')
    rotate.add_argument('rotation', type=int, nargs='?', default=0)

    underscan = secondaries.add_parser('underscan', add_help=False)
    underscan.add_argument('command', choices=['help', 'show', 'set'])
    underscan.add_argument('underscan', type=float, nargs='?')

    mirroring = secondaries.add_parser('mirroring', add_help=False)
    mirroring.add_argument('command', choices=['help', 'enable', 'disable'])
    mirroring.add_argument('--mirror', type=int)

    # All of the secondaries have some similar arguments
    for secondary in [set, show, brightness, underscan, mirroring, rotate]:
        secondary.add_argument('--help', action='store_true')
        secondary.add_argument('--display', type=int, default=dm.getMainDisplayID())

    # These two secondaries have similar arguments
    for secondary in [set, show]:
        secondary.add_argument('-w', '--width', type=int)
        secondary.add_argument('-h', '--height', type=int)
        secondary.add_argument('-d', '--depth', type=int, default=32)
        secondary.add_argument('-r', '--refresh', type=int, default=0)
        secondary.add_argument('--no-hidpi', action='store_true')
        secondary.add_argument('--only-hidpi', action='store_true')

    return parser.parse_args(parseList)


def getCommand(commandString):
    """
    Transforms input string into a Command.
    :returns: The resulting Command.
    """
    earlyExit()  # exits if the user didn't give enough information, or just wanted help

    parseList = []
    for element in commandString.split():
        parseList.append(element)
    args = parse(parseList)

    if args.subcommand == 'help':  # run help (default)
        dm.showHelp(command=args.command)
        sys.exit(0)

    if args.command == 'help' or args.help:  # subcommand-specific help
        dm.showHelp(command=args.subcommand)
        sys.exit(0)

    def hidpi():
        hidpi = 0  # show all modes (default)
        if args.only_hidpi or args.no_hidpi:
            if not (args.only_hidpi and args.no_hidpi):  # If they didn't give contrary instructions, proceed.
                if args.no_hidpi:
                    hidpi = 1  # do not show HiDPI modes
                elif args.only_hidpi:
                    hidpi = 2  # show only HiDPI modes
        return hidpi

    command = None
    if args.subcommand == 'set':
        command = dm.Command(args.subcommand, args.command, width=args.width, height=args.height, depth=args.depth,
                             refresh=args.refresh, displayID=args.display, hidpi=hidpi())
    elif args.subcommand == 'show':
        command = dm.Command(args.subcommand, args.command, width=args.width, height=args.height, depth=args.depth,
                             refresh=args.refresh, displayID=args.display, hidpi=hidpi())
    elif args.subcommand == 'brightness':
        command = dm.Command(args.subcommand, args.command, brightness=args.brightness, displayID=args.display)
    elif args.subcommand == 'underscan':
        command = dm.Command(args.subcommand, args.command, underscan=args.underscan, displayID=args.display)
    elif args.subcommand == 'mirroring':
        command = dm.Command(args.subcommand, args.command, displayID=args.brightness, mirrorDisplayID=args.mirror)
    elif args.subcommand == 'rotate':
        command = dm.Command(args.subcommand, args.command, angle=args.rotation, displayID=args.display)

    return command


def main():
    """
    Called on execution. Parses input and calls Display Manager.
    :return:
    """
    command = getCommand(' '.join(sys.argv[1:]))
    dm.run(command)


if __name__ == '__main__':
    main()
