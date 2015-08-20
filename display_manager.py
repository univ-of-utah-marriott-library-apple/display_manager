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
    'version'   : '0.5.0'
}

MAX_DISPLAYS = 32

## Struct-like thing for easy display.
class DisplayMode(object):
    def __init__(self, mode=None, width=None, height=None, bpp=None, refresh=None):
        if mode:
            self.width      = Quartz.CGDisplayModeGetWidth(mode)
            self.height     = Quartz.CGDisplayModeGetHeight(mode)
            self.bpp        = get_pixel_depth_from_encoding(Quartz.CGDisplayModeCopyPixelEncoding(mode))
            self.refresh    = Quartz.CGDisplayModeGetRefreshRate(mode)
            self.raw_mode   = mode
        else:
            for element in [width, height, bpp, refresh]:
                if element is None:
                    raise ValueError("Must give all of width, height, bits per pixel, and refresh rate to construct DisplayMode.")
            self.width      = width
            self.height     = height
            self.bpp        = bpp
            self.refresh    = refresh
            self.raw_mode   = None
        self.pixels     = self.width * self.height
        self.ratio      = float(self.width) / float(self.height)
    def __str__(self):
        return "{width}x{height}; pixel depth: {bpp}; refresh rate: {refresh}; ratio: {ratio}:1".format(
            width   = self.width,
            height  = self.height,
            bpp     = self.bpp,
            refresh = self.refresh,
            ratio   = self.ratio,
        )
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)   and
            self.width      == other.width      and
            self.height     == other.height     and
            self.bpp        == other.bpp        and
            self.refresh    == other.refresh
        )
    def __ne__(self, other):
        return not self.__eq__(other)

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
    modes = [DisplayMode(mode=mode) for mode in Quartz.CGDisplayCopyAllDisplayModes(display, None)]
    modes.sort(key = lambda mode: mode.refresh, reverse = True)
    modes.sort(key = lambda mode: mode.bpp, reverse = True)
    modes.sort(key = lambda mode: mode.pixels, reverse = True)
    return modes

def get_current_mode_for_display(display):
    mode = DisplayMode(mode=Quartz.CGDisplayCopyDisplayMode(display))
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
    """
    :param modes: A list containing DisplayMode objects.
    """
    # Check we don't have an empty list of modes.
    if not modes:
        return None
    match_mode = DisplayMode(width=width, height=height, bpp=depth, refresh=refresh)
    ratio = width / height
    pixels = width * height
    # Search for an exact match.
    for mode in modes:
        if mode == match_mode:
            return mode
    # No exact match, so let's check if there's a resolution and bit depth match.
    close_matches = []
    for mode in modes:
        if mode.width == width and mode.height == height and mode.bpp == depth:
            # Found one with the correct resolution.
            close_matches.append(mode)
    if close_matches:
        # There's at least one match at the correct resolution and bit depth.
        close_matches.sort(key = lambda mode: mode.refresh, reverse = True)
        larger = None
        smaller = None
        # Find the two closest matches by refresh rate.
        for match in close_matches:
            if match.refresh > refresh:
                larger = match
            else:
                smaller = match
                break
        # Check some edge cases.
        if smaller and not larger:
            # All the available refresh rates are lesser than the desired.
            return smaller
        if larger and not smaller:
            # There's only one element in the list, and it's larger than we
            # ideally wanted. Oh well.
            return larger
        # Okay, now we have two elements, and neither is perfect.
        # Find the closer of the two.
        larger_dif = abs(larger.refresh - refresh)
        smaller_dif = abs(smaller.refresh - refresh)
        if smaller_dif < larger_dif:
            return smaller
        else:
            return larger
    # No matches for WHD, so let's check that bit depth.
    close_matches = []
    for mode in modes:
        if mode.width == width and mode.height == height:
            # Found one with the right resolution.
            close_matches.append(mode)
    if close_matches:
        # We have the correct resolution. Let's find the closest bit depth.
        close_matches.sort(key = lambda mode: mode.bpp, reverse = True)
        larger = None
        smaller = None
        # Find the two closest matches by bit depth.
        for match in close_matches:
            if match.bpp > depth:
                larger = match
            else:
                smaller = match
                break
        # Check some edge cases.
        if smaller and not larger:
            # All the available bit depths are lesser than the desired.
            return smaller
        if larger and not smaller:
            # There's only one element in the list, and it's larger than we
            # ideally wanted. Oh well.
            return larger
        # Okay, now we have two elements, and neither is perfect.
        # Find the closer of the two.
        larger_dif = abs(larger.bpp - depth)
        smaller_dif = abs(smaller.bpp - depth)
        if smaller_dif < larger_dif:
            return smaller
        else:
            return larger
    # At this point, we don't even have a good resolution match.
    # Let's find all the modes with the appropriate ratio, and then find the
    # closest total pixel count.
    close_matches = []
    for mode in modes:
        if mode.ratio == ratio:
            # Got the right width:height ratio.
            close_matches.append(mode)
    if close_matches:
        # Sort by total pixels.
        close_matches.sort(key = lambda mode: mode.pixels, reverse = True)
        larger = None
        smaller = None
        # Find the closest matches by pixel count.
        for match in close_matches:
            if match.pixels > pixels:
                larger = match
            else:
                smaller = match
                break
        # Check some edge cases.
        if smaller and not larger:
            # All the available pixel counts are lesser than the desired.
            return smaller
        if larger and not smaller:
            # There's only one element in the list, and it's larger than we
            # ideally wanted. Oh well.
            return larger
        # Okay, now we have two elements, and neither is perfect.
        # Find the closer of the two.
        larger_dif = abs(larger.pixels - pixels)
        smaller_dif = abs(smaller.pixels - pixels)
        if smaller_dif < larger_dif:
            return smaller
        else:
            return larger
    # We don't have any good resolutions available. Let's throw an error?
    return None

def sub_set(command, width, height, depth, refresh, display=None):
    pass

def sub_show(command, width, height, depth, refresh, display=None):
    main_display = Quartz.CGMainDisplayID()
    if command == "all":
        all_modes = get_all_modes_for_all_displays()
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found.")
            sys.exit(4)
        print("Showing all possible display configurations.")
        print('-' * 80)
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            for mode in pair[1]:
                print("    {}".format(mode))
    elif command == "closest":
        for element in [width, height, depth, refresh]:
            if element is None:
                usage()
                print("Must have all of (width, height, depth, refresh) for closest matching.")
                sys.exit(2)
        all_modes = get_all_modes_for_all_displays()
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found.")
            sys.exit(4)
        print("Finding closest supported display configurations.")
        print('-' * 80)
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            closest = get_mode_closest_to_values(pair[1], width, height, depth, refresh)
            if closest:
                print("    {}".format(closest))
            else:
                print("    (no close matches found)")
    elif command == "highest":
        all_modes = get_all_modes_for_all_displays()
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found.")
            sys.exit(4)
        print("Showing highest supported display configurations.")
        print('-' * 80)
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            print("    {}".format(pair[1][0]))
    elif command == "exact":
        current_modes = get_all_current_configurations()
        print("Showing current display configurations.")
        print('-' * 80)
        for pair in current_modes:
            print("Display: {}".format(pair[0]))
            print("    {}".format(pair[1]))
    elif command == "displays":
        for display in get_displays_list():
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))

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
    parser_show.add_argument('command', choices=['help', 'all', 'closest', 'highest', 'exact', 'displays'], nargs='?', default='all')

    # Both 'set' and 'show' have similar supported arguments.
    for subparser in [parser_set, parser_show]:
        subparser.add_argument('--help', action='store_true')
        subparser.add_argument('-w', '--width', type=int)
        subparser.add_argument('-h', '--height', type=int)
        subparser.add_argument('-d', '--depth', type=int)
        subparser.add_argument('-r', '--refresh', type=int)
        subparser.add_argument('--display', type=int)

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
    if any(manual):
        for element in manual:
            if element is None:
                usage()
                print("Error: Must have either all or none of the manual specifications.")
                sys.exit(1)

    if args.subcommand == 'set':
        sub_set(args.command, args.width, args.height, args.depth, args.refresh, args.display)
    else:
        sub_show(args.command, args.width, args.height, args.depth, args.refresh, args.display)
