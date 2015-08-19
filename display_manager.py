#!/usr/bin/python

## Some info should go here.

#TODO: add these features:
# [ ] HDMI overscan
# [ ] AirPlay mirroring
# [ ] set individual display settings

## Imports
import argparse
import os
import sys

import Quartz

## Global Variables
attributes = {
    'long_name' : 'Display Manager',
    'name'      : os.path.basename(sys.argv[0]),
    'version'   : '0.3.0'
}

MAX_DISPLAYS = 32

## Struct-like thing for easy display.
class DisplayMode(object):
    def __init__(self, mode):
        self.width      = Quartz.CGDisplayModeGetWidth(mode)
        self.height     = Quartz.CGDisplayModeGetHeight(mode)
        self.pixels     = self.width * self.height
        self.bpp        = get_pixel_depth_from_encoding(Quartz.CGDisplayModeCopyPixelEncoding(mode))
        self.refresh    = Quartz.CGDisplayModeGetRefreshRate(mode)
        self.raw_mode   = mode
    def __str__(self):
        return "{width}x{height}; pixel depth: {bpp}; refresh rate: {refresh}".format(
            width   = self.width,
            height  = self.height,
            bpp     = self.bpp,
            refresh = self.refresh
        )
    def __repr__(self):
        return self.__str__()

## Helper Functions
def get_pixel_depth_from_encoding(encoding):
    if encoding == "PPPPPPPP":
        return 8
    elif encoding == "-RRRRRGGGGGBBBBB":
        return 16
    elif encoding == "--------RRRRRRRRGGGGGGGGBBBBBBBB":
        return 32
    else:
        raise RuntimeError("Unknown pixel encoding: {}".format(encoding))

def get_displays_list():
    (error, online_displays, displays_count) = Quartz.CGGetOnlineDisplayList(MAX_DISPLAYS, None, None)
    if error:
        raise RuntimeError("Unable to get displays list.")
    return online_displays

def get_all_modes_for_display(display):
    modes = [DisplayMode(mode) for mode in Quartz.CGDisplayCopyAllDisplayModes(display, None)]
    modes.sort(key = lambda mode: mode.pixels, reverse = True)
    return modes

def get_current_mode_for_display(display):
    mode = DisplayMode(Quartz.CGDisplayCopyDisplayMode(display))
    return mode

def get_all_current_configurations():
    modes = []
    for display in get_displays_list():
        modes.append( (display, get_current_mode_for_display(display)) )
    return modes

def get_all_modes_for_all_displays():
    modes = []
    for display in get_displays_list():
        modes.append( (display, get_all_modes_for_display(display)) )
    return modes

def get_mode_closest_to_values(modes, width, height, depth, refresh):
    pixels = width * height
    close_matches = []
    for mode in modes:
        if mode.width == width and mode.height == height and mode.depth == depth and mode.refresh == refresh:
            return mode
        if mode.pixels == pixels:
            close_matches.append(mode)
    if len(close_matches) == 0:
        larger = None
        smaller = None
        for mode in modes:
            if mode.pixels > pixels:
                larger = mode
            else:
                smaller = mode
                break
        # Check some edge cases.
        if smaller and not larger:
            # The desired resolution is greater than any available.
            return smaller
        if larger and not smaller:
            # The desired resolution is lesser than any available.
            return larger
        larger_dif = abs(larger.pixels - pixels)
        smaller_dif = abs(smaller.pixels - pixels)
        # Check which size is closer
        if smaller_dif < larger_dif:
            # The smaller size is closer.
            return smaller
        if larger_dif < smaller_dif:
            # The larger size is closer.
            return larger
    if len(close_matches) == 1:
        # We only had one match, so let's use it!
        return close_matches[0]
    if len(close_matches) > 1:
        # We had multiple matches at the same pixel count.
        res_matches = []
        for match in close_matches:
            if match.width == width and match.height == height:
                res_matches.append(match)

# def get_highest_supported_resolution_for_display(display):
#     return get_all_modes_for_display(display)[0]
#
# def get_highest_supported_resolution_for_all_displays():
#     modes = []
#     for display in get_displays_list():
#         modes.append( (display, get_highest_supported_resolution_for_display(display)) )
#     return modes

def sub_set(command, width, height, depth, refresh):
    pass

def sub_show(command, width, height, depth, refresh):
    if command == "all":
        all_modes = get_all_modes_for_all_displays()
        print("Showing all possible display configurations.")
        print('-' * 80)
        for pair in all_modes:
            print("Display: {}".format(pair[0]))
            for mode in pair[1]:
                print("    {}".format(mode))
    elif command == "closest":
        if not all([width, height, depth, refresh]):
            print("Must have all of (width, height, depth, refresh) for closest matching.")
            sys.exit(2)
    elif command == "highest":
        all_modes = get_all_modes_for_all_displays()
        print("Showing highest supported display configurations.")
        print('-' * 80)
        for pair in all_modes:
            print("Display: {}".format(pair[0]))
            print("    {}".format(pair[1][0]))
    elif command == "exact":
        current_modes = get_all_current_configurations()
        print("Showing current display configurations.")
        print('-' * 80)
        for pair in current_modes:
            print("Display: {}".format(pair[0]))
            print("    {}".format(pair[1]))

## Helpful command-line information

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
    exact       Show the current display configuration.

OPTIONS
    -w width    Resolution width
    -h height   Resolution height
    -d depth    Color depth
    -r refresh  Refresh rate
''')
    else:
        print('''\
usage: {name} {{ help | version | set | show }}

Use any of the subcommands with 'help' to get more information:
    help    Print this help information.
    version Print the version information.
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

    if len(sys.argv) == 2 and sys.argv[1] == '--help':
        usage()
        sys.exit(0)

    # Do actual argument parsing.
    parser = ArgumentParser(add_help=False)
    parser.add_argument('-v', '--version', action='store_true')

    # Check whether user wanted version information.
    # Print the version information and quit.
    args = parser.parse_known_args()
    if args[0].version:
        print(version())
        sys.exit(0)

    # Add the subparsers.
    subparsers = parser.add_subparsers(dest='subcommand')

    # Subparser for 'version'.
    parser_version = subparsers.add_parser('version', add_help=False)

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
        subparser.add_argument('-w', '--width', type=int)
        subparser.add_argument('-h', '--height', type=int)
        subparser.add_argument('-d', '--depth', type=int)
        subparser.add_argument('-r', '--refresh', type=int)

    # Parse the arguments.
    # Note that we have to use the leftover arguments from the
    # parser.parse_known_args() call up above.
    args = parser.parse_args(args[1])

    # If they used the 'help' subcommand, use it smartly.
    if args.subcommand == 'help':
        usage(command=args.command)
        sys.exit(0)

    if args.subcommand == 'version':
        print(version())
        sys.exit(0)

    # Check if they wanted help with the subcommand.
    if args.command == 'help' or args.help:
        usage(command=args.subcommand)
        sys.exit(0)

    # Check we have either all or none of the manual specifications.
    manual = [args.width, args.height, args.depth, args.refresh]
    if any(manual) and not all(manual):
        usage()
        print("Error: Must have either all or none of the manual specifications.")
        sys.exit(1)

    if args.subcommand == 'set':
        sub_set(args.command, args.width, args.height, args.depth, args.refresh)
    else:
        sub_show(args.command, args.width, args.height, args.depth, args.refresh)
