#!/usr/bin/python

# This script allows users to access the DisplayManager program through the command line.
# Passes command parameters into DisplayManager.


import sys
import argparse
import main.DisplayManager as dm


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


def parse():
    """
    Parse the user command-line input.
    """
    parser = argparse.ArgumentParser(add_help=False)
    args = parser.parse_known_args()
    subparsers = parser.add_subparsers(dest='subcommand')

    help = subparsers.add_parser('help', add_help=False)
    help.add_argument('command', choices=['set', 'show', 'brightness', 'underscan', 'mirroring'],
                      nargs='?', default=None)

    set = subparsers.add_parser('set', add_help=False)
    set.add_argument('command', choices=['help', 'closest', 'highest', 'exact'], nargs='?', default='closest')

    show = subparsers.add_parser('show', add_help=False)
    show.add_argument('command', choices=['help', 'all', 'closest', 'highest', 'current', 'displays'],
                      nargs='?', default='all')

    brightness = subparsers.add_parser('brightness', add_help=False)
    brightness.add_argument('command', choices=['help', 'show', 'set'])
    brightness.add_argument('brightness', type=float, nargs='?', default=1)

    rotate = subparsers.add_parser('rotate', add_help=False)
    rotate.add_argument('command', choices=['help', 'set', 'show'], nargs='?', default='show')
    rotate.add_argument('rotation', type=int, nargs='?', default=0)

    underscan = subparsers.add_parser('underscan', add_help=False)
    underscan.add_argument('command', choices=['help', 'show', 'set'])
    underscan.add_argument('underscan', type=float, nargs='?')

    mirroring = subparsers.add_parser('mirroring', add_help=False)
    mirroring.add_argument('command', choices=['help', 'enable', 'disable'])
    mirroring.add_argument('--mirror', type=int)

    # All of the subcommands have some similar arguments
    for subparser in [set, show, brightness, underscan, mirroring, rotate]:
        subparser.add_argument('--help', action='store_true')
        subparser.add_argument('--display', type=int, default=dm.getMainDisplayID())

    # These two subparsers have similar arguments
    for subparser in [set, show]:
        subparser.add_argument('-w', '--width', type=int)
        subparser.add_argument('-h', '--height', type=int)
        subparser.add_argument('-d', '--depth', type=int, default=32)
        subparser.add_argument('-r', '--refresh', type=int, default=0)
        subparser.add_argument('--no-hidpi', action='store_true')
        subparser.add_argument('--only-hidpi', action='store_true')

    return parser.parse_args(args[1])


def main():
    """
    Called on execution. Parses input and calls Display Manager.
    :return:
    """
    earlyExit()  # exits if the user didn't give enough information, or just wanted help
    args = parse()  # returns parsed args

    if args.subcommand == 'help':  # main help (default)
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

    if args.subcommand == 'set':
        command = dm.Command(args.command, args.subcommand, width=args.width, height=args.height, depth=args.depth,
                             refresh=args.refresh, displayID=args.display, hidpi=hidpi())
        dm.main(command)
    elif args.subcommand == 'show':
        command = dm.Command(args.command, args.subcommand, width=args.width, height=args.height, depth=args.depth,
                             refresh=args.refresh, displayID=args.display, hidpi=hidpi())
        dm.main(command)
    elif args.subcommand == 'brightness':
        command = dm.Command(args.command, args.subcommand, brightness=args.brightness, displayID=args.display)
        dm.main(command)
    elif args.subcommand == 'underscan':
        command = dm.Command(args.command, args.subcommand, underscan=args.underscan, displayID=args.display)
        dm.main(command)
    elif args.subcommand == 'mirroring':
        command = dm.Command(args.command, args.subcommand, displayID=args.brightness, mirrorDisplayID=args.mirror)
        dm.main(command)
    elif args.subcommand == 'rotate':
        command = dm.Command(args.command, args.subcommand, angle=args.rotation, displayID=args.display)
        dm.main(command)


if __name__ == '__main__':
    main()
