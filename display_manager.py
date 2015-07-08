#!/usr/bin/env python

## Some info should go here.

attributes = {
    'long_name' : 'Display Manager',
    'name'      : 'display_manager',
    'version'   : '0.2.0'
}

## Imports
import argparse
import sys

def version():
    """
    :return: A string containing the version information for this program.
    """
    return (
        "{name}, version {version}\n".format(
            name=attributes['long_name'],
            version=attributes['version']
        )
    )

def usage(command=None):
    """
    Prints out the usage information.
    """
    # Give the version information always.
    print(version())
    
    if command == 'set':
        print('''\
usage: {name} set {{ help | closest | highest | exact }}
        [-w width] [-h height] [-d depth] [-r refresh]

SUBCOMMANDS
    help        Print this help information.
    closest     Set the display settings to the supported resolution that is
                closest to the specified values.
    highest     Set the display settings to the highest supported resolution.
    exact       Set the display settings to the specified values without
                checking whether that resolution is supported by the display.

OPTIONS
    -w width    Resolution width
    -h height   Resolution height
    -d depth    Color depth
    -r refresh  Refresh rate
''').format(name=attributes['name'])
    elif command == 'show':
        print('''\
usage: {name} show {{ help | all | closest | highest | exact }}
        [-w width] [-h height] [-d depth] [-r refresh]

SUBCOMMANDS
    help        Print this help information.
    all         Show all supported resolutions for the display.
    closest     Show the closest matching supported resolution to the specified
                values.
    highest     Show the highest supported resolution.
    exact       Show whether the specified values are a supported resolution.

OPTIONS
    -w width    Resolution width
    -h height   Resolution height
    -d depth    Color depth
    -r refresh  Refresh rate
''')
    else:
        print('''\
usage: {name} {{ help | set | show }}

Use any of the subcommands with 'help' to get more information:
    help    Print this help information.
    set     Set the display configuration.
    show    See available display configurations.
''').format(name=attributes['name'])

class ArgumentParser(argparse.ArgumentParser):
    """
    Custom argument parser for printing error messages a bit more nicely.
    """
    def error(self, message):
        print("Error: {}\n".format(message))
        usage()
        self.exit(2)

if __name__ == '__main__':
    # If they don't give any arguments, help them out.
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    
    # Do actual argument parsing.
    parser = ArgumentParser(usage='this is a test')
    parser.add_argument('-v', '--version', action='store_true')
    
    # Check whether user wanted version information.
    # Print the version information and quit.
    args = parser.parse_known_args()
    if args[0].version:
        print(version())
        sys.exit(0)
    
    # Add the subparsers.
    subparsers = parser.add_subparsers(dest='subcommand')
    
    # Subparser for 'help'.
    parser_help = subparsers.add_parser('help', add_help=False)
    parser_help.add_argument('command', choices=['set', 'show'], nargs='?', default=None)
    
    # Subparser for 'set'.
    parser_set = subparsers.add_parser('set', add_help=False)
    parser_set.add_argument('command', choices=['help', 'closest', 'highest', 'exact'], nargs='?', default='closest')
    
    # Subparser for 'show'.
    parser_show = subparsers.add_parser('show', add_help=False)
    parser_show.add_argument('command', choices=['help', 'all', 'closest', 'highest', 'exact'], nargs='?', default='all')
    
    # Both 'set' and 'show' have similar supported arguments.
    for subparser in [parser_set, parser_show]:
        subparser.add_argument('--help', action='store_true')
        subparser.add_argument('-w', '--width', type=int, default='1024')
        subparser.add_argument('-h', '--height', type=int, default='768')
        subparser.add_argument('-d', '--depth', type=int, default='32')
        subparser.add_argument('-r', '--refresh', type=int, default='75')
    
    # Parse the arguments.
    # Note that we have to use the leftover arguments from the
    # parser.parse_known_args() call up above.
    args = parser.parse_args(args[1])
    
    # If they used the 'help' subcommand, use it smartly.
    if args.subcommand == 'help':
        usage(command=args.command)
        sys.exit(0)
    
    # Print help information and quit.
    if args.command == 'help' or args.help:
        usage(command=args.subcommand)
        sys.exit(0)
