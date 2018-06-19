#!/usr/bin/python

# Display Manager, version 1.0.0

# Manages Mac displays through the Objective-C bridge
# Controlled via command line arguments
# Can set screen resolution, color depth, refresh rate, screen mirroring, and brightness


import argparse
import objc
import os
import sys
import CoreFoundation
import Quartz
import subprocess


# TODO: remove these
## Global Variables
attributes = {
    'long_name' : 'Display Manager',
    'name'      : os.path.basename(sys.argv[0]),
    'version'   : '1.0.0'
    }

kMaxDisplays = 32


class DisplayMode(object):
    """
    This class describes a display mode, at least as I like to look at them.

    It has width, height, bits per pixel (pixel encoding), and refresh rate.
    It can also have the raw mode (if it's based on a real mode from the system)
    and a HiDPI scalar value (if the mode represents a scaled mode).

    This also calculates the total pixel count (width * height) and the display
    ratio (width / height). These are used to help with matching of different
    display modes with similar properties.
    """
    def __init__(self, mode=None, width=None, height=None, bpp=None, refresh=None):
        if mode:
            self.width      = Quartz.CGDisplayModeGetWidth(mode)
            self.height     = Quartz.CGDisplayModeGetHeight(mode)
            self.bpp        = getPixelDepth(Quartz.CGDisplayModeCopyPixelEncoding(mode))
            self.refresh    = Quartz.CGDisplayModeGetRefreshRate(mode)
            self.raw_mode   = mode
            self.dpi_scalar = getHidpiScalar(mode)
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
        self.pixels = self.width * self.height
        self.ratio  = float(self.width) / float(self.height)

    def __str__(self):
        return "{width}x{height}; pixel depth: {bpp}; refresh rate: {refresh}; ratio: {ratio:.2f}:1{hidpi}".format(
            width   = self.width,
            height  = self.height,
            bpp     = self.bpp,
            refresh = self.refresh,
            ratio   = self.ratio,
            hidpi   = "; [HiDPI: x{}]".format(self.dpi_scalar) if self.dpi_scalar else "")

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.width      == other.width        and
            self.height     == other.height       and
            self.bpp        == other.bpp          and
            self.refresh    == other.refresh      and
            self.dpi_scalar == other.dpi_scalar)

    def __ne__(self, other):
        return not self.__eq__(other)
        

class ArgumentParser(argparse.ArgumentParser):
    """
    Custom argument parser for printing error messages a bit more nicely.
    """
    def error(self, message):
        print("Error: {}\n".format(message))
        usage()
        self.exit(2)


## CoreFoundation-related functions
def iokitInit():
    """
    This handles the importing of specific functions and variables from the
    IOKit framework. IOKit is not natively bridged in PyObjC, and so the methods
    must be found and encoded manually to gain their functionality in Python.

    After calling this function, the following IOKit functions are available:
        IOServiceGetMatchingServices
            Look up the registered IOService objects that match the given dict.
        IODisplayCreateInfoDictionary
            Returns a dictionary with information about display hardware.
        IODisplayGetFloatParameter
            Finds a float value for a given parameter.
        IODisplaySetFloatParameter
            Sets a float value for a given parameter.
        IOServiceMatching
            Returns a dictionary that specifies an IOService class match.
        IOIteratorNext
            Finds the next object in an iteration.

    And the following variables are available:
        kIODisplayNoProductName
            Prevents IODisplayCreateInfoDictionary from including the
            kIODisplayProductName property.
        kIOMasterPortDefault
            The setDefault mach port used to initiate communication with IOKit.
        kIODisplayBrightnessKey
            The key used to get brightness from IODisplayGetFloatParameter.
        kDisplayVendorID
        kDisplayProductID
        kDisplaySerialNumber
            These are keys used to access display information.
    """

    # Retrieve the IOKit framework
    iokit = objc.initFrameworkWrapper(
        "IOKit",
        frameworkIdentifier="com.apple.iokit",
        frameworkPath=objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"),
        globals=globals()
        )

    # These are the Objective-C functions required
    functions = [
        ("IOServiceGetMatchingServices", b"iI@o^I"),
        ("IODisplayCreateInfoDictionary", b"@II"),
        ("IODisplayGetFloatParameter", b"iII@o^f"),
        ("IODisplaySetFloatParameter", b"iII@f"),
        ("IOServiceMatching", b"@or*", "", dict(
            # This one is obnoxious. The "*" gets pythonified as a char, not a
            # char*, so we have to make it interpret as a string.
            arguments=
            {
                0: dict(type=objc._C_PTR + objc._C_CHAR_AS_TEXT,
                        c_array_delimited_by_null=True,
                        type_modifier=objc._C_IN)
            }
        )),
        ("IOIteratorNext", "II"),
        ]

    # The Objective-C variables required
    variables = [
        ("kIODisplayNoProductName", b"I"),
        ("kIOMasterPortDefault", b"I"),
        ("kIODisplayBrightnessKey", b"*"),
        ("kDisplayVendorID", b"*"),
        ("kDisplayProductID", b"*"),
        ("kDisplaySerialNumber", b"*"),
        ]

    # Load variables, functions, and keys from Objective-C into the global namespace
    objc.loadBundleFunctions(iokit, globals(), functions)
    objc.loadBundleVariables(iokit, globals(), variables)
    global kDisplayBrightness
    kDisplayBrightness = CoreFoundation.CFSTR(kIODisplayBrightnessKey)
    global kDisplayUnderscan
    kDisplayUnderscan = CoreFoundation.CFSTR("pscn")


def CFNumberEqualsUInt32(number, uint32):
    """
    Determines whether a number and a uint32_t are equivalent.

    :param number: The returned result from a CFDictionaryGetValue call.
        This call can return "None", which does not match exactly with "0".
    :param uint32: The result from Quartz library calls for display information.
        This is an integer of sorts.
    :return: A boolean; whether the two values are equivalent.
    """
    if number is None:
        return uint32 == 0
    return number == uint32


def CGDisplayGetIOServicePort(display):
    """
    Since CGDisplayIOServicePort was deprecated in 10.9, we have to rebuild the
    equivalent function.

    This is effectively taken from:
        https://github.com/nriley/brightness/blob/master/brightness.c

    :param display: A display identifier.
    :return: The integer value of the matching service port (or 0 if none can
        be found).
    """
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


## Get helpers
def getHidpiScalar(mode):
    """
    Uses extra methods to find the HiDPI scalar for a display.

    :param mode: The raw mode from the Quartz library for the display.
    :return: Either None if there is no scaling, or else the value of the
        scaling scalar.
    """
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


def getHidpiValue(no_hidpi, only_hidpi):
    """
    Returns a numeric value describing the HiDPI mode desired.

    :param no_hidpi: Whether to exclude HiDPI modes from the search.
    :param only_hidpi: Whether to only include HiDPI modes.
    :return: An integer describing the combination of these.
    """
    if no_hidpi and not only_hidpi:
        return 0
    elif not no_hidpi and not only_hidpi:
        return 1
    elif not no_hidpi and only_hidpi:
        return 2
    else:
        raise ValueError("Error: Cannot require both no HiDPI and only HiDPI. Make up your mind.")


def getPixelDepth(encoding):
    """
    Takes a pixel encoding and returns an integer representing that encoding.

    :param encoding: A pixel encoding from Quartz's method
        CGDisplayModeCopyPixelEncoding.
    :return: An integer representing the pixel depth of that encoding.
    """
    if encoding == "PPPPPPPP":
        return 8
    elif encoding == "-RRRRRGGGGGBBBBB":
        return 16
    elif encoding == "--------RRRRRRRRGGGGGGGGBBBBBBBB":
        return 32
    elif encoding == "--RRRRRRRRRRGGGGGGGGGGBBBBBBBBBB":
        return 30
    else:
        raise RuntimeError("Unknown pixel encoding: {}".format(encoding))


def getAllConfigs():
    """
    Gets a list of all displays and their associated current display modes.

    :return: A list of tuples as:
        (display identifier, [current DisplayMode for that display])
    """
    modes = []
    for display in getDisplaysList():
        modes.append((display, GetCurrentMode(display)))
    return modes


def GetCurrentMode(display):
    """
    Gets the current display mode for a given display.

    :param: The identifier of the desired display.
    :return: The current DisplayMode used by that display.
    """
    return DisplayMode(mode=Quartz.CGDisplayCopyDisplayMode(display))


def getClosestMode(modes, width, height, depth, refresh):
    """
    Given a set of values and a list of available modes, attempts to find the
    closest matching supported mode in the list. "Closest matching" is
    determined as follows:

    1. Is the desired mode in the list exactly?
    2. If not, is there a mode with the desired resolution and bit depth?
      a. Find the closest matching refresh rate available.
    3. If not, is there a mode with the desired resolution?
      a. Find the closest matching bit depth available.
    4. If not, is there a mode with the desired Width:Height ratio?
      a. Find the closest resolution available.
    5. If not...
      a. Find the closest aspect ratio.
      b. Find the closest resolution.
    6. If there is still nothing, return None.

    :param modes: A list containing DisplayMode objects.
    :param width: An integer for display width.
    :param height: An integer for display height.
    :param depth: The pixel depth for the display.
    :param refresh: The refresh rate for the display.
    :return: The DisplayMode from the list that matches the values best.
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
    # todo: remove unnecessary?
    # ideal_ratio = None

    #####################################################################
    # TODO: FIGURE THE NEXT SIX LINES OUT; THEY'RE PROBABLY THE PROBLEM #
    for ratio in ratios:
        if ratio > match_ratio:
            larger_ratio = ratio
        else:
            smaller_ratio = ratio
            break
    #                                                                   #
    #####################################################################

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

    # We don't have any good resolutions available.
    return None


def getDisplaysList():
    """
    Gets a list of all current displays.

    :return: A tuple containing all currently-online displays.
        Each object in the tuple is a display identifier (as an integer).
    """
    (error, online_displays, displays_count) = Quartz.CGGetOnlineDisplayList(kMaxDisplays, None, None)
    if error:
        raise RuntimeError("Unable to get displays list.")
    return online_displays


def getAllModes(display, hidpi=1):
    """
    Given a display, this finds all of the available supported display modes.
    The resulting list is sorted so that the highest resolution, highest pixel
    depth, highest refresh rate modes are at the top.

    :param display: The identifier of the desired display.
    :param hidpi: The HiDPI usage mode, specified by getHidpiValue().
    :return: A list of DisplayMode objects, sorted.
    """
    #TODO: The HiDPI call also gets extra things. Fix those.
    # Specifically, it includes not just HiDPI settings, but also settings for
    # different pixel encodings than the standard 8-, 16-, and 32-bit.
    # Unfortunately, the CGDisplayModeCopyPixelEncoding method cannot see other
    # encodings, leading to apparently-duplicated values. Not ideal.
    if hidpi:
        modes = [DisplayMode(mode=mode) for mode in Quartz.CGDisplayCopyAllDisplayModes(display, {Quartz.kCGDisplayShowDuplicateLowResolutionModes: Quartz.kCFBooleanTrue})]
    else:
        modes = [DisplayMode(mode=mode) for mode in Quartz.CGDisplayCopyAllDisplayModes(display, None)]
    if hidpi == 2:
        # This removes extra modes, so only HiDPI-scaled modes are displayed.
        modes = [mode for mode in modes if mode.dpi_scalar is not None]
    # Sort the modes!
    modes.sort(key = lambda mode: mode.refresh, reverse = True)
    modes.sort(key = lambda mode: mode.bpp, reverse = True)
    modes.sort(key = lambda mode: mode.pixels, reverse = True)
    return modes


def getAllModesAllDisplays(hidpi=1):
    """
    Gets a list of displays and all available modes for each display.

    :param hidpi: Whether to include additional, "duplicate" modes.
    :return: A list of tuples as:
        (display identifier, [all valid DisplayModes for that display])
    """
    modes = []
    for display in getDisplaysList():
        modes.append((display, getAllModes(display, hidpi)))
    return modes


def getMainDisplayID():
    '''return display id of main display
    '''
    return Quartz.CGMainDisplayID()


## Subcommand handlers
def setHandler(command, width, height, depth=32, refresh=0, display=getMainDisplayID(), hidpi=1):
    """
    Handles all of the options for the "set" subcommand.

    :param command: The command passed in.
    :param width: Desired width.
    :param height: Desired height.
    :param depth: Desired pixel depth.
    :param refresh: Desired refresh rate.
    :param display: Specific display to configure.
    :param hidpi: Description of HiDPI settings from getHidpiValue().
    """
    main_display = getMainDisplayID()
    # Set defaults if they're not given (defaults in function definition overridden in certain cases)
    if depth is None:
        depth = 32
    if refresh is None:
        refresh = 0
    if display is None:
        display = getMainDisplayID()
    if hidpi is None:
        hidpi = 1

    if command == "closest":
        # Find the closest matching configuration and apply it.
        for element in [width, height]:
            # Make sure they supplied all of the necessary info.
            if element is None:
                usage("set")
                print("Must have both width and height for closest setting.")
                sys.exit(2)

        all_modes = getAllModesAllDisplays(hidpi)
        if display:
            all_modes = [x for x in all_modes if x[0] == display]

        if not all_modes:
            print("No matching displays found.")
            sys.exit(4)

        # todo: decide whether to delete or not
        # Print out what we ended up picking for "closest".
        # print("Setting for: {width}x{height} ({ratio:.2f}:1); {bpp} bpp; {refresh} Hz".format(
        #     width   = width,
        #     height  = height,
        #     ratio   = float(width) / float(height),
        #     bpp     = depth,
        #     refresh = refresh
        #     ))

        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            closest = getClosestMode(pair[1], width, height, depth, refresh)
            if closest:
                print("    {}".format(closest))
                setDisplay(pair[0], closest)
            else:
                print("    (no close matches found)")

    elif command == "highest":
        # Find the highest display mode and set it.
        all_modes = getAllModesAllDisplays(hidpi)
        if display:
            all_modes = [x for x in all_modes if x[0] == display]

        if not all_modes:
            print("No matching displays found.")
            sys.exit(4)

        for pair in all_modes:
            # This uses the first mode in the all_modes list, because it is
            # guaranteed that the list is sorted.
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            print("    {}".format(pair[1][0]))
            setDisplay(pair[0], pair[1][0])

    elif command == "exact":
        # Set the exact mode or don't set it at all.
        all_modes = getAllModesAllDisplays(hidpi)
        # Create a fake exact mode to match against.
        exact = DisplayMode(
            width   = width,
            height  = height,
            bpp     = depth,
            refresh = refresh
            )
        if display:
            all_modes = [x for x in all_modes if x[0] == display]

        if not all_modes:
            print("No matching displays found.")
            sys.exit(4)

        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            closest = getClosestMode(pair[1], width, height, depth, refresh)
            if closest and closest == exact:
                print("    {}".format(closest))
                setDisplay(pair[0], closest)
            else:
                print("    (no exact matches found)")


def showHandler(command, width, height, depth=32, refresh=0, display=getMainDisplayID(), hidpi=1):
    """
    Handles all the options for the "show" subcommand.

    :param command: The command passed in.
    :param width: Desired width.
    :param height: Desired height.
    :param depth: Desired pixel depth.
    :param refresh: Desired refresh rate.
    :param display: Specific display to configure.
    :param hidpi: Description of HiDPI settings from getHidpiValue().
    """
    # Get the main display's identifier since it gets used a lot.
    main_display = getMainDisplayID()
    # Set defaults if they're not given (function definition overridden in certain cases)
    if depth is None:
        depth = 32
    if refresh is None:
        refresh = 0
    if display is None:
        display = getMainDisplayID()
    if hidpi is None:
        hidpi = 1
    # Iterate over the supported commands.
    if command == "all":
        # Show all the modes.
        all_modes = getAllModesAllDisplays(hidpi)
        if not all_modes:
            print("No matching displays found ({}).".format(display))
            sys.exit(4)
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            for mode in pair[1]:
                print("    {}".format(mode))
    elif command == "closest":
        # Only show the closest mode to whatever was specified.
        for element in [width, height]:
            if element is None:
                usage("show")
                print("Must have both width and height for closest matching.")
                sys.exit(2)
        all_modes = getAllModesAllDisplays(hidpi)
        # They only wanted to show one display's configuration.
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found ({}).".format(display))
            sys.exit(4)
        print("Finding closest supported display configuration(s).")
        # todo: delete? this one might actually be useful
        # Inform what's going on.
        # print("Searching for: {width}x{height} ({ratio:.2f}:1); {bpp} bpp; {refresh} Hz".format(
        #     width   = width,
        #     height  = height,
        #     ratio   = float(width) / float(height),
        #     bpp     = depth,
        #     refresh = refresh
        #     ))
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            closest = getClosestMode(pair[1], width, height, depth, refresh)
            if closest:
                print("    {}".format(closest))
            else:
                print("    (no close matches found)")
    elif command == "highest":
        # Show the highest supported display configuration.
        all_modes = getAllModesAllDisplays(hidpi)
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found ({}).".format(display))
            sys.exit(4)
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            print("    {}".format(pair[1][0]))
    elif command == "exact":
        # Show the current display configuration.
        current_modes = getAllConfigs()
        if display:
            current_modes = [x for x in current_modes if x[0] == display]
        if not current_modes:
            print("No matching displays found ({}).".format(display))
            sys.exit(4)
        for pair in current_modes:
            print("Display: {}".format(pair[0]))
            print("    {}".format(pair[1]))
    elif command == "displays":
        # Print a list of online displays.
        for display in getDisplaysList():
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))


def brightnessHandler(command, brightness=1, display=getMainDisplayID()):
    """
    Handles all the options for the "brightness" subcommand.

    :param command: The command passed in.
    :param brightness: The level of brightness to change to.
    :param display: Specific display to configure.
    """
    main_display = getMainDisplayID()
    # Set default if it's not given (function definition overridden in certain cases)
    if display is None:
        display = getMainDisplayID()

    # We need extra IOKit stuff for this.
    iokitInit()

    if command == "show":
        displays = getDisplaysList()
        for display in displays:
            service = CGDisplayGetIOServicePort(display)
            (error, display_brightness) = IODisplayGetFloatParameter(service, 0, kDisplayBrightness, None)
            if error:
                print("Failed to get brightness of display {}; error {}".format(display, error))
                continue
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
            print("    {:.2f}%".format(display_brightness * 100))

    elif command == "set":
        # Set the brightness setting.
        service = CGDisplayGetIOServicePort(display)
        error = IODisplaySetFloatParameter(service, 0, kDisplayBrightness, brightness)
        if error:
            print("Failed to set brightness of display {}; error {}".format(display, error))
            # External display brightness probably can't be managed this way
            print("External displays may not be compatible with Display Manager. \n"
                  "If this is an external display, try setting manually on device hardware.")


def rotateHandler(command, rotation=0, display=getMainDisplayID()):
    """
    Handles all the options for the "rotation" subcommand.

    :param command: The command passed in.
    :param rotation: The display to configure rotation on.
    :param display: The display to configure rotation on.
    """
    # Set default if it's not given (function definition overridden in certain cases)
    if display is None:
        display = getMainDisplayID()

    iokitInit()

    if command == "show":
        output = subprocess.check_output(["./fb-rotate/fb-rotate -i"], shell=True)
        outputLines = output.split("\n")
        parsedOutput = []
        for line in outputLines[1:]:
            parsedOutput.append(line.split())
        for line in parsedOutput:
            if line:
                if "main" in line[-1]:  # main display
                    print("Display: {0} (Main Display)".format(str(int(line[1], 16))))
                    print("    Rotation: {0} degrees".format(line[-2]))
                elif line[0].isdigit():  # external display
                    print("Display: {0}".format(str(int(line[1], 16))))
                    print("    Rotation: {0} degrees".format(line[-1]))

        Quartz.CGDisplayRotation(display)

    elif command == "set":
        # todo: remove old
        # displays = getDisplaysList()
        # for display in displays:
        #     service = CGDisplayGetIOServicePort(display)
        #     settings = (0x00000400 | kIOScaleRotate90 << 16)
        #     notSure = IOServiceRequestProbe(service, settings)  # (service, 32-bit-int options)
        #     print(notSure)

        if rotation % 90 == 0:
            display = hex(display)
            subprocess.call("./fb-rotate/fb-rotate -d {0} -r {1}".format(str(display),
                str(rotation % 360)), shell=True)
        else:
            print("Can only rotate by multiples of 90 degrees.")
            sys.exit(1)

        service = Quartz.CGDisplayIOServicePort(display)


def underscanHandler(command, underscan=1, display=getMainDisplayID()):
    """
    Handles all the options for the "underscan" subcommand.

    :param command: The command passed in.
    :param underscan: The value to set on the underscan slider.
    :param display: Specific display to configure.
    """
    iokitInit()
    main_display = getMainDisplayID()

    # Set defaults if they're not given (function definition overridden in certain cases)
    if display is None:
        display = getMainDisplayID()
    if not display:
        displays = getDisplaysList()
    else:
        displays = [display]

    if command == "show":
        for display in displays:
            service = CGDisplayGetIOServicePort(display)
            (error, display_underscan) = IODisplayGetFloatParameter(service, 0, kDisplayUnderscan, None)
            if error:
                print("Failed to get underscan value of display {}; error {}".format(display, error))
                continue
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
            print("    {:.2f}%".format(display_underscan * 100))

    elif command == "set":
        for display in displays:
            service = CGDisplayGetIOServicePort(display)
            error = IODisplaySetFloatParameter(service, 0, kDisplayUnderscan, underscan)
            if error:
                print("Failed to set underscan of display {}; error {}".format(display, error))
                continue
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
            print("    {:.2f}%".format(underscan * 100))


def mirroringHandler(command, display, display_to_mirror=getMainDisplayID()):
    """
    Handles all the options for the "mirroring" subcommand.

    :param command: The command passed in.
    :param display: The display to configure mirroring on.
    :param display_to_mirror: The display to become a mirror of.
    """
    main_display = getMainDisplayID()
    if not display:
        displays = getDisplaysList()
    else:
        displays = [display]
    # Get the current modes for each display.
    modes = []
    for display in displays:
        modes.append((display, GetCurrentMode(display)))
    # If we're disabling, then set the mirror target to the null display.
    if command == "enable":
        enable_mirroring = True
        print("Enabling mirroring with target display: {}{}".format(display_to_mirror, " (Main Display)" if display_to_mirror == main_display else ""))
    if command == "disable":
        display_to_mirror = Quartz.kCGNullDirectDisplay
        enable_mirroring = False
    # Effect the changes!
    for display, mode in modes:
        print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
        setDisplay(display, mode, enable_mirroring, display_to_mirror)


## Actually set display (resolution and mirroring)
def setDisplay(display, mode, mirroring=False, mirror_display=getMainDisplayID()):
    """
    Sets a display to a given configuration.

    :param display: The identifier of the desired display.
    :param mode: The DisplayMode to set the display to.
    :param mirroring: Whether to activate mirroring.
    :param mirror_display: The identifier of the display to mirror.
    """
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
        # Yes, so let's turn it on! We mirror the specified display.
        if display != mirror_display:
            Quartz.CGConfigureDisplayMirrorOfDisplay(config_ref, display, mirror_display)
    else:
        # I guess not. Don't mirror anything!
        Quartz.CGConfigureDisplayMirrorOfDisplay(config_ref, display, Quartz.kCGNullDirectDisplay)
    # Finish the configuration.
    Quartz.CGCompleteDisplayConfiguration(config_ref, Quartz.kCGConfigurePermanently)


## main() and its helper functions
def earlyExit():
    """
    Exits early in specific cases; exit return value sensitive to specific conditions
    """
    # If they don't include enough arguments, show help and exit with error
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    # Still show help, but do not exit with error
    elif len(sys.argv) == 2 and sys.argv[1] == '--help':
        usage()
        sys.exit(0)


def parse():
    # Do actual argument parsing
    parser = ArgumentParser(add_help=False)

    # Isolate parser args
    args = parser.parse_known_args()

    # Add the subparsers.
    subparsers = parser.add_subparsers(dest='subcommand')

    # Subparser for 'help'
    parser_help = subparsers.add_parser('help', add_help=False)
    parser_help.add_argument(
        'command',
        choices=['set', 'show', 'brightness', 'underscan', 'mirroring'],
        nargs='?',
        default=None
    )

    # Subparser for 'set'
    parser_set = subparsers.add_parser('set', add_help=False)
    parser_set.add_argument(
        'command',
        choices=['help', 'closest', 'highest', 'exact'],
        nargs='?',
        default='closest'
    )

    # Subparser for 'show'
    parser_show = subparsers.add_parser('show', add_help=False)
    parser_show.add_argument(
        'command',
        choices=['help', 'all', 'closest', 'highest', 'exact', 'displays'],
        nargs='?',
        default='all'
    )

    # Subparser for 'brightness'
    parser_brightness = subparsers.add_parser('brightness', add_help=False)
    parser_brightness.add_argument('command', choices=['help', 'show', 'set'])
    parser_brightness.add_argument('brightness', type=float, nargs='?')

    # Subparser for 'rotate'
    parser_rotate = subparsers.add_parser('rotate', add_help=False)
    parser_rotate.add_argument(
        'command',
        choices=['help', 'set', 'show'],
        nargs='?',
        default='show'
    )
    parser_rotate.add_argument(
        'rotation',
        type=int,
        default=0,
        nargs='?'
    )

    # Subparser for 'underscan'
    parser_underscan = subparsers.add_parser('underscan', add_help=False)
    parser_underscan.add_argument('command', choices=['help', 'show', 'set'])
    parser_underscan.add_argument('underscan', type=float, nargs='?')

    # Subparser for 'mirroring'
    parser_mirroring = subparsers.add_parser('mirroring', add_help=False)
    parser_mirroring.add_argument('command', choices=['help', 'enable', 'disable'])
    parser_mirroring.add_argument('--mirror-of-display', type=int, default=getMainDisplayID())

    # All of the subcommands have some similar arguments
    for subparser in [parser_set, parser_show, parser_brightness, parser_underscan, parser_mirroring, parser_rotate]:
        subparser.add_argument('--help', action='store_true')
        subparser.add_argument('--display', type=int)

    # These two subparsers have similar arguments
    for subparser in [parser_set, parser_show]:
        subparser.add_argument('-w', '--width', type=int)
        subparser.add_argument('-h', '--height', type=int)
        subparser.add_argument('-d', '--depth', type=int)
        subparser.add_argument('-r', '--refresh', type=int)
        subparser.add_argument('--no-hidpi', action='store_true')
        subparser.add_argument('--only-hidpi', action='store_true')

    # Parse the arguments
    # Note that we have to use the leftover arguments from the parser.parse_known_args() call up above
    return parser.parse_args(args[1])


def version():
    """
    Helpful command-line information
    :return: A string containing the version information for this program.
    """
    return ("{name}, version {version}\n".format(
        name    = attributes['long_name'],
        version = attributes['version']
        ))


def usage(command=None):
    """
    Prints out the usage information.

    :param command: The subcommand to print information for.
    """
    # Give the version information always.
    print(version())

    information = {}

    information['set'] = '\n'.join([
        "usage: {name} set {{ help | closest | highest | exact }}",
        "    [-w width] [-h height] [-d depth] [-r refresh]",
        "    [--display display] [--nohidpi]",
        "",
        "SUBCOMMANDS",
        "    help        Print this help information.",
        "    closest     Set the display settings to the supported resolution that is",
        "                closest to the specified values.",
        "    highest     Set the display settings to the highest supported resolution.",
        "    exact       Set the display settings to the specified values if they are",
        "                supported. If they are not, don't change the display.",
        "",
        "OPTIONS",
        "    -w width            Resolution width.",
        "    -h height           Resolution height.",
        "    -d depth            Pixel color depth (default: 32).",
        "    -r refresh          Refresh rate (default: 0).",
        "    --display display   Specify a particular display (default: main display).",
        "    --no-hidpi          Don't show HiDPI settings.",
        "    --only-hidpi        Only show HiDPI settings.",
        "",
    ]).format(name=attributes['name'])

    information['show'] = '\n'.join([
        "usage: {name} show {{ help | all | closest | highest | exact }}",
        "    [-w width] [-h height] [-d depth] [-r refresh]",
        "    [--display display] [--nohidpi]",
        "",
        "SUBCOMMANDS",
        "    help        Print this help information.",
        "    all         Show all supported resolutions for the display.",
        "    closest     Show the closest matching supported resolution to the specified",
        "                values.",
        "    highest     Show the highest supported resolution.",
        "    exact       Show the current display configuration.",
        "    displays    Just list the current displays and their IDs.",
        "",
        "OPTIONS",
        "    -w width            Resolution width.",
        "    -h height           Resolution height.",
        "    -d depth            Pixel color depth (default: 32).",
        "    -r refresh          Refresh rate (default: 32).",
        "    --display display   Specify a particular display (default: main display).",
        "    --no-hidpi          Don't show HiDPI settings.",
        "    --only-hidpi        Only show HiDPI settings.",
        "",
    ]).format(name=attributes['name'])

    information['brightness'] = '\n'.join([
        "usage: {name} brightness {{ help | show | set [value] }}",
        "    [--display display]",
        "",
        "SUBCOMMANDS",
        "    help        Print this help information.",
        "    show        Show the current brightness setting(s).",
        "    set [value] Sets the brightness to the given value. Must be between 0 and 1.",
        "",
        "OPTIONS",
        "    --display display   Specify a particular display (default: main display).",
        "",
    ]).format(name=attributes['name'])

    information['rotate'] = '\n'.join([
        "usage: {name} rotate {{ help | show | set }}"
        "    [--display display]",
        "SUBCOMMANDS",
        "    help        Print this help information.",
        "    show        Show the current display rotation.",
        "    set [value] Set the rotation to the given value (in degrees). Must be a multiple of 90.",
        "",
        "OPTIONS",
        "    --display display   Specify a particular display (default: main display).",
        ""
    ]).format(name=attributes['name'])

    information['underscan'] = '\n'.join([
        "usage: {name} underscan {{ help | show | set [value] }}",
        "    [--display display]",
        "",
        "SUBCOMMANDS",
        "    help        Print this help information.",
        "    show        Show the current underscan setting(s).",
        "    set [value] Sets the underscan to the given value. Must be between 0 and 1.",
        "",
        "NOTES",
        "    The underscan setting is provided for by a private Apple API. This means that,",
        "    while it works fine for now, they could change the functionality at any point",
        "    without warning.",
        "",
    ]).format(name=attributes['name'])

    information['mirroring'] = '\n'.join([
        "usage: {name} brightness {{ help | enable | disable }}",
        "    [--diplay display] [--mirror-of-display display]",
        "",
        "SUBCOMMANDS",
        "    help        Print this help information.",
        "    enable      Activate mirroring.",
        "    disable     Deactivate mirroring.",
        "",
        "OPTIONS",
        "    --display display               Change mirroring settings for 'display'.",
        "    --mirror-of-display display     Set the display to mirror 'display' (default: main display).",
        "",
    ]).format(name=attributes['name'])

    if command in information:
        print(information[command])
    else:
        print('\n'.join([
            "usage: {name} {{ help | set | show | mirroring | brightness | rotate }}",
            "",
            "Use any of the subcommands with 'help' to get more information:",
            "    help        Show this help information.",
            "    set         Set the display configuration.",
            "    show        Show available display configurations.",
            "    brightness  Show or set the current display brightness.",
            "    rotate      Show or set display rotation.",
            "    underscan   Show or set the current display underscan.",
            "    mirroring   Set mirroring configuration.",
            "",
        ])).format(name=attributes['name'])


def main():
    earlyExit()  # exits if the user didn't give enough information, or just wanted help
    args = parse()  # returns parsed args

    # If they used the 'help' subcommand, display that subcommand's help information
    if args.subcommand == 'help':
        usage(command=args.command)
        sys.exit(0)

    # Check if they wanted help with the subcommand.
    if args.command == 'help' or args.help:
        usage(command=args.subcommand)
        sys.exit(0)

    # todo: remove deprecated
    # Check we have either all or none of the manual specifications.
    # try:
    #     manual = [args.width, args.height]
    #     if any(manual):
    #         # if args.subcommand not in ['set', 'show']:
    #         #     usage()
    #         #     print("Error: Cannot supply manual specifications for subcommand '{}'.".format(subcommand))
    #         #     sys.exit(1)
    #         for element in manual:
    #             if element is None:
    #                 usage()
    #                 print("Error: Must have either all or none of the manual specifications.")
    #                 sys.exit(1)
    # except AttributeError:
    #     # Evidently we're using a subparser without these attributes.
    #     # Not an issue.
    #     pass

    # Check if we have specified both not to use HiDPI and only to use HiDPI.
    try:
        hidpi = getHidpiValue(args.no_hidpi, args.only_hidpi)
    except AttributeError:
        # Probably using a subparser that doesn't check HiDPI settings.
        # And that's okay.
        pass

    # todo: look into how this works (log)
    # scriptname = os.path.basename(sys.argv[0])
    # Actual logger:
    # logger = loggers.FileLogger(name=scriptname, level=loggers.DEBUG)

    # Debug logger:
    # logger = loggers.StreamLogger(name=scriptname, level=loggers.DEBUG)

    # loggers.debug("{0} started".format(scriptname))

    if args.subcommand == 'set':
        setHandler(args.command, args.width, args.height, args.depth, args.refresh, args.display, hidpi)
    elif args.subcommand == 'show':
        showHandler(args.command, args.width, args.height, args.depth, args.refresh, args.display, hidpi)
    elif args.subcommand == 'brightness':
        brightnessHandler(args.command, args.brightness, args.display)
    elif args.subcommand == 'underscan':
        underscanHandler(args.command, args.underscan, args.display)
    elif args.subcommand == 'mirroring':
        mirroringHandler(args.command, args.display, args.mirror_of_display)
    elif args.subcommand == 'rotate':
        rotateHandler(args.command, args.rotation, args.display)

    # loggers.debug("{0} finished".format(scriptname))


if __name__ == '__main__':
    main()
