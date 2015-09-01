#!/usr/bin/python

## Some info should go here.

#TODO: add these features:
# [ ] works in login window
# [ ] mirroring
# [x] brightness settings
# [ ] HDMI overscan
# [ ] AirPlay mirroring
# [x] set individual display settings

## Imports
import argparse
import objc
import os
import sys

import CoreFoundation
import Quartz

## Global Variables
attributes = {
    'long_name' : 'Display Manager',
    'name'      : os.path.basename(sys.argv[0]),
    'version'   : '0.6.0'
}

## Manual metadata loading.
def initialize_iokit_functions_and_variables():
    iokit = objc.initFrameworkWrapper(
        "IOKit",
        frameworkIdentifier="com.apple.iokit",
        frameworkPath=objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"),
        globals=globals()
        )
    functions = [
        ("IOServiceGetMatchingServices", b"iI@o^I"),
        ("IODisplayCreateInfoDictionary", b"@II"),
        ("IODisplayGetFloatParameter", b"iII@o^f"),
        ("IODisplaySetFloatParameter", b"iII@f"),
        ("IOObjectRelease", b"iI"),
        ("IOServiceMatching", b"@or*", "", dict(
            arguments=
            {
                0: dict(type=objc._C_PTR + objc._C_CHAR_AS_TEXT,
                        c_array_delimited_by_null=True,
                        type_modifier=objc._C_IN)
            }
        )),
        ("IOIteratorNext", "II"),
        ]
    variables = [
        ("kIODisplayNoProductName", b"I"),
        ("kIOMasterPortDefault", b"I"),
        ("kIODisplayBrightnessKey", b"*"),
        ("kDisplayVendorID", b"*"),
        ("kDisplayProductID", b"*"),
        ("kDisplaySerialNumber", b"*"),
        ]
    objc.loadBundleFunctions(iokit, globals(), functions)
    objc.loadBundleVariables(iokit, globals(), variables)
    global kDisplayBrightness
    kDisplayBrightness = CoreFoundation.CFSTR(kIODisplayBrightnessKey)

def CFNumberEqualsUInt32(number, uint32):
    if number is None:
        return uint32 == 0
    return number == uint32

def CGDisplayGetIOServicePort(display):
    # Get values from current display.
    vendor = Quartz.CGDisplayVendorNumber(display)
    model  = Quartz.CGDisplayModelNumber(display)
    serial = Quartz.CGDisplaySerialNumber(display)
    # Get matching service name.
    matching = IOServiceMatching("IODisplayConnect")
    # Get the iterator for all service ports.
    error, iterator = IOServiceGetMatchingServices(kIOMasterPortDefault, matching, None)
    if error:
        # Did we get an error?
        return 0
    # Begin iteration.
    service = IOIteratorNext(iterator)
    matching_service = 0
    while service != 0:
        # Until we find the desired service, keep iterating.
        # Get the information for the current service.
        info = IODisplayCreateInfoDictionary(service, kIODisplayNoProductName)
        # Get the vendor ID, product ID, and serial number.
        vendorID        = CoreFoundation.CFDictionaryGetValue(info, CoreFoundation.CFSTR(kDisplayVendorID))
        productID       = CoreFoundation.CFDictionaryGetValue(info, CoreFoundation.CFSTR(kDisplayProductID))
        serialNumber    = CoreFoundation.CFDictionaryGetValue(info, CoreFoundation.CFSTR(kDisplaySerialNumber))
        # Check if everything matches.
        if (
            CFNumberEqualsUInt32(vendorID, vendor) and
            CFNumberEqualsUInt32(productID, model) and
            CFNumberEqualsUInt32(serialNumber, serial)
            ):
            # If it does, then we've found our service port, so break out.
            matching_service = service
            break
        # Otherwise, keep searching.
        service = IOIteratorNext(iterator)
    # Return what we've found.
    return matching_service

kMaxDisplays = 32

## Struct-like thing for easy display.
class DisplayMode(object):
    def __init__(self, mode=None, width=None, height=None, bpp=None, refresh=None):
        if mode:
            self.width      = Quartz.CGDisplayModeGetWidth(mode)
            self.height     = Quartz.CGDisplayModeGetHeight(mode)
            self.bpp        = get_pixel_depth_from_encoding(Quartz.CGDisplayModeCopyPixelEncoding(mode))
            self.refresh    = Quartz.CGDisplayModeGetRefreshRate(mode)
            self.raw_mode   = mode
            self.dpi_scalar = get_hidpi_scalar(mode)
        else:
            for element in [width, height, bpp, refresh]:
                if element is None:
                    raise ValueError("Must give all of width, height, bits per pixel, and refresh rate to construct DisplayMode.")
            self.width      = width
            self.height     = height
            self.bpp        = bpp
            self.refresh    = refresh
            self.raw_mode   = None
            self.dpi_scalar = None
        self.pixels     = self.width * self.height
        self.ratio      = float(self.width) / float(self.height)
    def __str__(self):
        return "{width}x{height}; pixel depth: {bpp}; refresh rate: {refresh}; ratio: {ratio:.2f}:1{hidpi}".format(
            width   = self.width,
            height  = self.height,
            bpp     = self.bpp,
            refresh = self.refresh,
            ratio   = self.ratio,
            hidpi   = "; [HiDPI: x{}]".format(self.dpi_scalar) if self.dpi_scalar else ""
        )
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)   and
            self.width      == other.width      and
            self.height     == other.height     and
            self.bpp        == other.bpp        and
            self.refresh    == other.refresh    and
            self.dpi_scalar == other.dpi_scalar
        )
    def __ne__(self, other):
        return not self.__eq__(other)

## Helper Functions
def get_hidpi_scalar(mode):
    raw_width  = Quartz.CGDisplayModeGetPixelWidth(mode)
    raw_height = Quartz.CGDisplayModeGetPixelHeight(mode)
    res_width  = Quartz.CGDisplayModeGetWidth(mode)
    res_height = Quartz.CGDisplayModeGetHeight(mode)
    if raw_width == res_width and raw_height == res_height:
        return None
    else:
        if raw_width / res_width != raw_height / res_height:
            raise RuntimeError("Vertical and horizontal dimensions aren't scaled properly... mode: {}".format(mode))
        return raw_width / res_width

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
    (error, online_displays, displays_count) = Quartz.CGGetOnlineDisplayList(kMaxDisplays, None, None)
    if error:
        raise RuntimeError("Unable to get displays list.")
    return online_displays

def get_all_modes_for_display(display, hidpi=True):
    #TODO: The HiDPI call also gets extra things. Fix those.
    # Specifically, it includes not just HiDPI settings, but also settings for
    # different pixel encodings than the standard 8-, 16-, and 32-bit.
    # Unfortunately, the CGDisplayModeCopyPixelEncoding method cannot see other
    # encodings, leading to apparently-duplicated values. Not ideal.
    if hidpi:
        modes = [DisplayMode(mode=mode) for mode in Quartz.CGDisplayCopyAllDisplayModes(display, {Quartz.kCGDisplayShowDuplicateLowResolutionModes: Quartz.kCFBooleanTrue})]
    else:
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

def get_all_modes_for_all_displays(hidpi=True):
    modes = []
    for display in get_displays_list():
        modes.append( (display, get_all_modes_for_display(display, hidpi)) )
    return modes

def get_mode_closest_to_values(modes, width, height, depth, refresh):
    """
    :param modes: A list containing DisplayMode objects.
    """
    # Check we don't have an empty list of modes.
    if not modes:
        return None
    match_mode = DisplayMode(width=width, height=height, bpp=depth, refresh=refresh)
    match_ratio = width / height
    match_pixels = width * height
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
        if mode.ratio == match_ratio:
            # Got the right width:height ratio.
            close_matches.append(mode)
    if close_matches:
        # Sort by total pixels.
        close_matches.sort(key = lambda mode: mode.pixels, reverse = True)
        larger = None
        smaller = None
        # Find the closest matches by pixel count.
        for match in close_matches:
            if match.pixels > match_pixels:
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
        larger_dif = abs(larger.pixels - match_pixels)
        smaller_dif = abs(smaller.pixels - match_pixels)
        if smaller_dif < larger_dif:
            return smaller
        else:
            return larger
    # Still no good matches. Okay, now we're really reaching.
    # Let's try to find all of the displays with a sort-of-close aspect ratio,
    # and then find the one in there that has the closest total pixel count.
    ratios = []
    for mode in modes:
        ratios.append(mode.ratio)
    ratios = list(set(ratios))
    ratios.sort(reverse = True)
    larger_ratio = None
    smaller_ratio = None
    ideal_ratio = None
    for ratio in ratios:
        if ratio > match_ratio:
            larger_ratio = ratio
        else:
            smaller_ratio = ratio
            break
    if smaller_ratio and not larger_ratio:
        ideal_ratio = smaller_ratio
    elif larger_ratio and not smaller_ratio:
        ideal_ratio = larger_ratio
    else:
        larger_dif = abs(larger_ratio - match_ratio)
        smaller_dif = abs(smaller_ratio - match_ratio)
        if smaller_dif < larger_dif:
            ideal_ratio = smaller_ratio
        else:
            ideal_ratio = larger_ratio
    # Now find all the matches with the ideal ratio.
    close_matches = []
    for mode in modes:
        if mode.ratio == ideal_ratio:
            close_matches.append(mode)
    # And now we look through those for the closest match in pixel count.
    if close_matches:
        # Sort by total pixels.
        close_matches.sort(key = lambda mode: mode.pixels, reverse = True)
        larger = None
        smaller = None
        # Find the closest matches by pixel count.
        for match in close_matches:
            if match.pixels > match_pixels:
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
        larger_dif = abs(larger.pixels - match_pixels)
        smaller_dif = abs(smaller.pixels - match_pixels)
        if smaller_dif < larger_dif:
            return smaller
        else:
            return larger
    # We don't have any good resolutions available. Let's throw an error?
    return None

def set_display(display, mode, mirroring=False):
    print("Setting display {} to mode: {}".format(display, mode))
    # Begin the configuration.
    (error, config_ref) = Quartz.CGBeginDisplayConfiguration(None)
    # Check there were no errors.
    if error:
        print("Could not begin display configuration: error {}".format(error))
        sys.exit(8)
    # Enact the desired configuration.
    error = Quartz.CGConfigureDisplayWithDisplayMode(config_ref, display, mode.raw_mode, None)
    # Were there errors?
    if error:
        print("Failed to set display configuration: error {}".format(error))
        # Yeah, there were errors. Let's cancel the configuration.
        error = Quartz.CGCancelDisplayConfiguration(config_ref)
        if error:
            # Apparently this can fail too? Huh.
            print("Failed to cancel display configuraiton setting: error {}".format(error))
        sys.exit(9)
    # Did we want mirroring enabled?
    if mirroring:
        # Yes, so let's turn it on! We mirror the main display.
        main_display = Quartz.CGMainDisplayID()
        if display != main_display:
            Quartz.CGConfigureDisplayMirrorOfDisplay(config_ref, display, main_display)
    else:
        # I guess not. Don't mirror anything!
        Quartz.CGConfigureDisplayMirrorOfDisplay(config_ref, display, Quartz.kCGNullDirectDisplay)
    # Finish the configuration.
    Quartz.CGCompleteDisplayConfiguration(config_ref, Quartz.kCGConfigurePermanently)

def sub_set(command, width, height, depth, refresh, display=None, hidpi=True):
    main_display = Quartz.CGMainDisplayID()
    if command == "closest":
        for element in [width, height, depth, refresh]:
            if element is None:
                usage("set")
                print("Must have all of (width, height, depth, refresh) for closest setting.")
                sys.exit(2)
        all_modes = get_all_modes_for_all_displays(hidpi)
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found.")
            sys.exit(4)
        print("Setting closest supported display configuration(s).")
        # Inform what's going on.
        print("Setting for: {width}x{height} ({ratio:.2f}:1); {bpp} bpp; {refresh} Hz".format(
            width   = width,
            height  = height,
            ratio   = float(width) / float(height),
            bpp     = depth,
            refresh = refresh
        ))
        print('-' * 80)
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            closest = get_mode_closest_to_values(pair[1], width, height, depth, refresh)
            if closest:
                print("    {}".format(closest))
                set_display(pair[0], closest)
            else:
                print("    (no close matches found)")
    elif command == "highest":
        all_modes = get_all_modes_for_all_displays(hidpi)
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found.")
            sys.exit(4)
        print("Setting highest supported display configuration(s).")
        print('-' * 80)
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            print("    {}".format(pair[1][0]))
            set_display(pair[0], pair[1][0])


def sub_show(command, width, height, depth, refresh, display=None, hidpi=True):
    main_display = Quartz.CGMainDisplayID()
    if command == "all":
        all_modes = get_all_modes_for_all_displays(hidpi)
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found ({}).".format(display))
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
                usage("show")
                print("Must have all of (width, height, depth, refresh) for closest matching.")
                sys.exit(2)
        all_modes = get_all_modes_for_all_displays(hidpi)
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found ({}).".format(display))
            sys.exit(4)
        print("Finding closest supported display configuration(s).")
        # Inform what's going on.
        print("Searching for: {width}x{height} ({ratio:.2f}:1); {bpp} bpp; {refresh} Hz".format(
            width   = width,
            height  = height,
            ratio   = float(width) / float(height),
            bpp     = depth,
            refresh = refresh
        ))
        print('-' * 80)
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            closest = get_mode_closest_to_values(pair[1], width, height, depth, refresh)
            if closest:
                print("    {}".format(closest))
            else:
                print("    (no close matches found)")
    elif command == "highest":
        all_modes = get_all_modes_for_all_displays(hidpi)
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found ({}).".format(display))
            sys.exit(4)
        print("Showing highest supported display configuration(s).")
        print('-' * 80)
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            print("    {}".format(pair[1][0]))
    elif command == "exact":
        current_modes = get_all_current_configurations()
        if display:
            current_modes = [x for x in current_modes if x[0] == display]
        if not current_modes:
            print("No matching displays found ({}).".format(display))
            sys.exit(4)
        print("Showing current display configuration(s).")
        print('-' * 80)
        for pair in current_modes:
            print("Display: {}".format(pair[0]))
            print("    {}".format(pair[1]))
    elif command == "displays":
        for display in get_displays_list():
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))

def sub_brightness(command, brightness=1, display=None):
    main_display = Quartz.CGMainDisplayID()
    initialize_iokit_functions_and_variables()
    if not display:
        displays = get_displays_list()
    else:
        displays = [display]
    if command == "show":
        print("Showing current brightness setting(s).")
        print('-' * 80)
        for display in displays:
            service = CGDisplayGetIOServicePort(display)
            (error, display_brightness) = IODisplayGetFloatParameter(service, 0, kDisplayBrightness, None)
            if error:
                print("Failed to get brightness of display {}; error {}".format(display, error))
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
            print("    {:.2f}%".format(display_brightness * 100))
    elif command == "set":
        print("Setting display brightness to {:.2f}%".format(brightness * 100))
        print('-' * 80)
        for display in displays:
            service = CGDisplayGetIOServicePort(display)
            error = IODisplaySetFloatParameter(service, 0, kDisplayBrightness, brightness)
            if error:
                print("Failed ot set brightness of display {}; error {}".format(display, error))
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
            print("    {:.2f}%".format(brightness * 100))

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
        [-w width] [-h height] [-d depth] [-r refresh] [--display display] [--nohidpi]

SUBCOMMANDS
    help        Print this help information.
    closest     Set the display settings to the supported resolution that is
                closest to the specified values.
    highest     Set the display settings to the highest supported resolution.
    exact       Set the display settings to the specified values without
                checking whether that resolution is supported by the display.

OPTIONS
    -w width            Resolution width
    -h height           Resolution height
    -d depth            Color depth
    -r refresh          Refresh rate
    --display display   Specify a particular display
    --no-hidpi          Don't show HiDPI settings
''').format(name=attributes['name'])
    elif command == 'show':
        print('''\
usage: {name} show {{ help | all | closest | highest | exact }}
        [-w width] [-h height] [-d depth] [-r refresh] [--display display] [--nohidpi]

SUBCOMMANDS
    help        Print this help information.
    all         Show all supported resolutions for the display.
    closest     Show the closest matching supported resolution to the specified
                values.
    highest     Show the highest supported resolution.
    exact       Show the current display configuration.
    displays    Just list the current displays and their IDs.

OPTIONS
    -w width            Resolution width
    -h height           Resolution height
    -d depth            Color depth
    -r refresh          Refresh rate
    --display display   Specify a particular display
    --no-hidpi          Don't show HiDPI settings
''')
    elif command == 'brightness':
        print('''\
usage: {name} brightness {{ show }} [--display display]

SUBCOMMANDS
    help        Print this help information.
    show        Show the current brightness setting(s).

OPTIONS
    --display display   Specify a particular display
''')
    else:
        print('''\
usage: {name} {{ help | version | set | show }}

Use any of the subcommands with 'help' to get more information:
    help        Print this help information.
    version     Print the version information.
    set         Set the display configuration.
    show        See available display configurations.
    brightness  See or set the current display brightness.
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
    parser_help.add_argument('command', choices=['set', 'show', 'brightness'], nargs='?', default=None)

    # Subparser for 'set'.
    parser_set = subparsers.add_parser('set', add_help=False)
    parser_set.add_argument('command', choices=['help', 'closest', 'highest', 'exact'], nargs='?', default='closest')

    # Subparser for 'show'.
    parser_show = subparsers.add_parser('show', add_help=False)
    parser_show.add_argument('command', choices=['help', 'all', 'closest', 'highest', 'exact', 'displays'], nargs='?', default='all')

    # Subparser for 'brightness'.
    parser_brightness = subparsers.add_parser('brightness', add_help=False)
    parser_brightness.add_argument('command', choices=['help', 'show', 'set'])
    parser_brightness.add_argument('brightness', type=float, nargs='?')

    # All of the subcommands have some similar arguments.
    for subparser in [parser_set, parser_show, parser_brightness]:
        subparser.add_argument('-w', '--width', type=int)
        subparser.add_argument('-h', '--height', type=int)
        subparser.add_argument('-d', '--depth', type=int)
        subparser.add_argument('-r', '--refresh', type=int)
        subparser.add_argument('--no-hidpi', action='store_true')
        subparser.add_argument('--help', action='store_true')
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
        if subcommand not in ['set', 'show']:
            usage()
            print("Error: Cannot supply manual specifications for subcommand '{}'.".format(subcommand))
            sys.exit(1)
        for element in manual:
            if element is None:
                usage()
                print("Error: Must have either all or none of the manual specifications.")
                sys.exit(1)

    if args.subcommand == 'set':
        sub_set(args.command, args.width, args.height, args.depth, args.refresh, args.display, not args.no_hidpi)
    elif args.subcommand == 'show':
        sub_show(args.command, args.width, args.height, args.depth, args.refresh, args.display, not args.no_hidpi)
    elif args.subcommand == 'brightness':
        sub_brightness(args.command, args.brightness, args.display)
