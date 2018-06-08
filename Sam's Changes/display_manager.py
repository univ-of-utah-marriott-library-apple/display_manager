#!/System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python

## Some info should go here.

#TODO: add these features:
# [ ] works in login window
# [x] mirroring
# [x] brightness settings
# [x] HDMI overscan
# [ ] AirPlay mirroring
# [x] set individual display settings
# [x] HiDPI/no HiDPI options

## Imports
import argparse
import objc
import os
import sys
import plistlib
from pprint import pprint

import CoreFoundation
import Quartz

## Global Variables
attributes = {
    'long_name' : 'Display Manager',
    'name'      : os.path.basename(sys.argv[0]),
    'version'   : '0.10.0'
    }

kMaxDisplays = 32

## Manual metadata loading.
def initialize_iokit_functions_and_variables():
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
    # Grab the IOKit framework.
    iokit = objc.initFrameworkWrapper(
        "IOKit",
        frameworkIdentifier="com.apple.iokit",
        frameworkPath=objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"),
        globals=globals()
        )
    # These are the functions we're going to need.
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
    # Variables we'll need.
    variables = [
        ("kIODisplayNoProductName", b"I"),
        ("kIOMasterPortDefault", b"I"),
        ("kIODisplayBrightnessKey", b"*"),
        ("kDisplayVendorID", b"*"),
        ("kDisplayProductID", b"*"),
        ("kDisplaySerialNumber", b"*"),
        ]
    # Load the things!
    objc.loadBundleFunctions(iokit, globals(), functions)
    objc.loadBundleVariables(iokit, globals(), variables)
    # Set this key for later use.
    global kDisplayBrightness
    kDisplayBrightness = CoreFoundation.CFSTR(kIODisplayBrightnessKey)
    # This key is a private API for Apple. Use at your own risk.
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

## Struct-like thing for easy display.
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
            self.bpp        = get_pixel_depth_from_encoding(Quartz.CGDisplayModeCopyPixelEncoding(mode))
            self.refresh    = Quartz.CGDisplayModeGetRefreshRate(mode)
            self.raw_mode   = mode
            r_w, r_h = get_hidpi_scalar2(mode)
            self.raw_height = r_h
            self.raw_width = r_w
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

    def debug(self):
        s = "\n{}\n".format(self) \
            + "   width: {}\n".format(self.width) \
            + "  height: {}\n".format(self.height) \
            + "     bpp: {}\n".format(self.bpp) \
            + " refresh: {}\n".format(self.refresh) \
            + "   HiDPI: {}\n".format(self.dpi_scalar) \
            + "  pixels: {}\n".format(self.pixels) \
            + "     r_w: {}\n".format(self.raw_width) \
            + "     r_h: {}\n".format(self.raw_height) \
            + "   ratio: {}\n".format(self.ratio) \
            + "   mode: {}\n".format(self.raw_mode) \
            + "-" * 80 
        return s

    def __str__(self):
        hidpi = "; [HiDPI: x{0}]".format(self.dpi_scalar) if self.dpi_scalar else ''
        return "{0}x{1}; pixel depth: {2}; refresh rate: {3}; ratio: {4:.2f}:1{5}".format(
                    self.width, self.height, self.bpp, 
                    self.refresh, self.ratio, hidpi)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (isinstance(other, self.__class__) 
                and self.width == other.width 
                and self.height == other.height 
                and self.bpp == other.bpp 
                and self.refresh == other.refresh
                and self.dpi_scalar == other.dpi_scalar)

    def __ne__(self, other):
        return not self.__eq__(other)
        

## Helper Functions
def get_hidpi_scalar(mode):
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

## Helper Functions
def get_hidpi_scalar2(mode):
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
    return raw_width, raw_height
    if raw_width == res_width and raw_height == res_height:
        return None
    else:
        if raw_width / res_width != raw_height / res_height:
            raise RuntimeError("Vertical and horizontal dimensions aren't scaled properly... mode: {}".format(mode))
#         return raw_width / res_width
        return raw_width, raw_height

def get_hidpi_value(no_hidpi, only_hidpi):
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

def get_pixel_depth_from_encoding(encoding):
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

def get_displays_list():
    """
    Gets a list of all current displays.

    :return: A tuple containing all currently-online displays.
        Each object in the tuple is a display identifier (as an integer).
    """
    (error, online_displays, displays_count) = Quartz.CGGetOnlineDisplayList(kMaxDisplays, None, None)
    if error:
        raise RuntimeError("Unable to get displays list.")
    return online_displays

def get_all_modes_for_display(display, hidpi=1):
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

def get_current_mode_for_display(display):
    """
    Gets the current display mode for a given display.

    :param: The identifier of the desired display.
    :return: The current DisplayMode used by that display.
    """
    return DisplayMode(mode=Quartz.CGDisplayCopyDisplayMode(display))

def get_all_current_configurations():
    """
    Gets a list of all displays and their associated current display modes.

    :return: A list of tuples as:
        (display identifier, [current DisplayMode for that display])
    """
    modes = []
    for display in get_displays_list():
        modes.append( (display, get_current_mode_for_display(display)) )
    return modes

def get_all_modes_for_all_displays(hidpi=1):
    """
    Gets a list of displays and all available modes for each display.

    :param hidpi: Whether to include additional, "duplicate" modes.
    :return: A list of tuples as:
        (display identifier, [all valid DisplayModes for that display])
    """
    modes = []
    for display in get_displays_list():
        modes.append( (display, get_all_modes_for_display(display, hidpi)) )
    return modes

def get_mode_closest_to_values(modes, width, height, depth, refresh):
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

def show_as_plist(main_display_id, modes):
    pprint(modes)
    data = {'displays': []}
    for id, mode in modes:
        for m in mode:
            print(m.debug())
#         data['displays'].append({
#             'id': id,
#             'main': True if id == main_display_id else False,
#             'height': mode.height,
#             'width': mode.width,
#             'depth': mode.bpp,
#             'refresh': mode.refresh,
#             'hidpi': mode.dpi_scalar
#         })
    print plistlib.writePlistToString(data)
    

def set_display(display, mode, mirroring=False, mirror_display=Quartz.CGMainDisplayID()):
    """
    Sets a display to a given configuration.

    :param display: The identifier of the desired display.
    :param mode: The DisplayMode to set the display to.
    :param mirroring: Whether to activate mirroring.
    :param mirror_display: The identifier of the display to mirror.
    """
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
        # Yes, so let's turn it on! We mirror the specified display.
        if display != mirror_display:
            Quartz.CGConfigureDisplayMirrorOfDisplay(config_ref, display, mirror_display)
    else:
        # I guess not. Don't mirror anything!
        Quartz.CGConfigureDisplayMirrorOfDisplay(config_ref, display, Quartz.kCGNullDirectDisplay)
    # Finish the configuration.
    Quartz.CGCompleteDisplayConfiguration(config_ref, Quartz.kCGConfigurePermanently)

def sub_set(command, width, height, depth, refresh, display=None, hidpi=1):
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
    # Get the main display's identifier (since it gets used a lot).
    main_display = Quartz.CGMainDisplayID()
    # Iterate over the supported commands.
    if command == "closest":
        # Find the closest matching configuration and apply it.
        for element in [width, height, depth, refresh]:
            # Make sure they supplied all of the necessary info.
            if element is None:
                usage("set")
                print("Must have all of (width, height, depth, refresh) for closest setting.")
                sys.exit(2)
        all_modes = get_all_modes_for_all_displays(hidpi)
        # They only wanted to set one display.
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
        # Make it so!
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            closest = get_mode_closest_to_values(pair[1], width, height, depth, refresh)
            if closest:
                print("    {}".format(closest))
                set_display(pair[0], closest)
            else:
                print("    (no close matches found)")
    elif command == "highest":
        # Find the highest display mode and set it.
        all_modes = get_all_modes_for_all_displays(hidpi)
        # They only wanted to set one display.
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found.")
            sys.exit(4)
        print("Setting highest supported display configuration(s).")
        print('-' * 80)
        for pair in all_modes:
            # This uses the first mode in the all_modes list, because it is
            # guaranteed that the list is sorted.
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            print("    {}".format(pair[1][0]))
            set_display(pair[0], pair[1][0])
    elif command == "exact":
        # Set the exact mode or don't set it at all.
        all_modes = get_all_modes_for_all_displays(hidpi)
        # Create a fake exact mode to match against.
        exact = DisplayMode(
            width   = width,
            height  = height,
            bpp     = depth,
            refresh = refresh
            )
        # They only wanted to set one display.
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found.")
            sys.exit(4)
        print("Setting exact mode or quitting.")
        print('-' * 80)
        for pair in all_modes:
            print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
            closest = get_mode_closest_to_values(pair[1], width, height, depth, refresh)
            if closest and closest == exact:
                print("    {}".format(closest))
                set_display(pair[0], closest)
            else:
                print("    (no exact matches found)")

def sub_show(command, width, height, depth, refresh, display=None, hidpi=1, plist=False):
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
    debug = "DEBUG:\n" \
          + "   command: {}\n".format(command) \
          + "     width: {}\n".format(width) \
          + "    height: {}\n".format(height) \
          + "     depth: {}\n".format(depth) \
          + "   refresh: {}\n".format(refresh) \
          + "   display: {}\n".format(display) \
          + "     hidpi: {}\n".format(hidpi) \
          + "     plist: {}".format(plist)
          
    print debug
          
    
    # Get the main display's identifier since it gets used a lot.
    main_display = Quartz.CGMainDisplayID()
    # Iterate over the supported commands.
    if command == "all":
        # Show all the modes.
        all_modes = get_all_modes_for_all_displays(hidpi)
        # Check if they only wanted to show one display's configuration.
        if display:
            all_modes = [x for x in all_modes if x[0] == display]
        if not all_modes:
            print("No matching displays found ({}).".format(display))
            sys.exit(4)
        if not plist:
            print("Showing all possible display configurations.")
            print('-' * 80)
            for pair in all_modes:
                print("Display: {}{}".format(pair[0], " (Main Display)" if pair[0] == main_display else ""))
                for mode in pair[1]:
                    print("    {}".format(mode))
        else:
            show_as_plist(main_display, all_modes)
    elif command == "closest":
        # Only show the closest mode to whatever was specified.
        for element in [width, height, depth, refresh]:
            if element is None:
                usage("show")
                print("Must have all of (width, height, depth, refresh) for closest matching.")
                sys.exit(2)
        all_modes = get_all_modes_for_all_displays(hidpi)
        # They only wanted to show one display's configuration.
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
        # Show the highest supported display configuration.
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
        # Show the current display configuration.
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
        # Print a list of online displays.
        for display in get_displays_list():
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
    elif command == "plist":
        # Show the current display configuration(s) in plist form.
        current_modes = get_all_current_configurations()
        if display:
            current_modes = [x for x in current_modes if x[0] == display]
        if not current_modes:
            print("No matching displays found ({}).".format(display))
            sys.exit(4)
        data = {'displays': []}
        for id, mode in current_modes:
            data['displays'].append({
                'id': id,
                'main': True if id == main_display else False,
                'height': mode.height,
                'width': mode.width,
                'depth': mode.bpp,
                'refresh': mode.refresh,
                'hidpi': mode.dpi_scalar
            })
        print plistlib.writePlistToString(data)
            
def sub_brightness(command, brightness=1, display=None):
    """
    Handles all the options for the "brightness" subcommand.

    :param command: The command passed in.
    :param brightness: The level of brightness to change to.
    :param display: Specific display to configure.
    """
    main_display = Quartz.CGMainDisplayID()
    # We need extra IOKit stuff for this.
    initialize_iokit_functions_and_variables()
    if not display:
        displays = get_displays_list()
    else:
        displays = [display]
    # Iterate over the available options.
    if command == "show":
        # Show the current brightness setting.
        print("Showing current brightness setting(s).")
        print('-' * 80)
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
        print("Setting display brightness to {:.2f}%".format(brightness * 100))
        print('-' * 80)
        for display in displays:
            service = CGDisplayGetIOServicePort(display)
            error = IODisplaySetFloatParameter(service, 0, kDisplayBrightness, brightness)
            if error:
                print("Failed to set brightness of display {}; error {}".format(display, error))
                continue
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
            print("    {:.2f}%".format(brightness * 100))

def sub_underscan(command, underscan=1, display=None):
    """
    Handles all the options for the "underscan" subcommand.

    :param command: The command passed in.
    :param underscan: The value to set on the underscan slider.
    :param display: Specific display to configure.
    """
    main_display = Quartz.CGMainDisplayID()
    # We need extra IOKit stuff for this.
    initialize_iokit_functions_and_variables()
    if not display:
        displays = get_displays_list()
    else:
        displays = [display]
    # Iterate over the available options.
    if command == "show":
        # Show the current underscan setting.
        print("Showing current underscan setting(s).")
        print('-' * 80)
        for display in displays:
            service = CGDisplayGetIOServicePort(display)
            (error, display_underscan) = IODisplayGetFloatParameter(service, 0, kDisplayUnderscan, None)
            if error:
                print("Failed to get underscan value of display {}; error {}".format(display, error))
                continue
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
            print("    {:.2f}%".format(display_underscan * 100))
    elif command == "set":
        # Set the underscan setting.
        print("Setting display underscan to {:.2f}%".format(underscan * 100))
        print('-' * 80)
        for display in displays:
            service = CGDisplayGetIOServicePort(display)
            error = IODisplaySetFloatParameter(service, 0, kDisplayUnderscan, underscan)
            if error:
                print("Failed to set underscan of display {}; error {}".format(display, error))
                continue
            print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
            print("    {:.2f}%".format(underscan * 100))

def sub_mirroring(command, display, display_to_mirror=Quartz.CGMainDisplayID()):
    """
    Handles all the options for the "mirroring" subcommand.

    :param command: The command passed in.
    :param display: The display to configure mirroring on.
    :param display_to_mirror: The display to become a mirror of.
    """
    main_display = Quartz.CGMainDisplayID()
    if not display:
        displays = get_displays_list()
    else:
        displays = [display]
    # Get the current modes for each display.
    modes = []
    for display in displays:
        modes.append( (display, get_current_mode_for_display(display)) )
    # If we're disabling, then set the mirror target to the null display.
    if command == "enable":
        enable_mirroring = True
        print("Enabling mirroring with target display: {}{}".format(display_to_mirror, " (Main Display)" if display_to_mirror == main_display else ""))
    if command == "disable":
        print("Disabling mirroring.")
        display_to_mirror = Quartz.kCGNullDirectDisplay
        enable_mirroring = False
    print('-' * 80)
    # Effect the changes!
    for display, mode in modes:
        print("Display: {}{}".format(display, " (Main Display)" if display == main_display else ""))
        set_display(display, mode, enable_mirroring, display_to_mirror)

## Helpful command-line information

def version():
    """
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
        "    -d depth            Color depth.",
        "    -r refresh          Refresh rate.",
        "    --display display   Specify a particular display.",
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
        "    -d depth            Color depth.",
        "    -r refresh          Refresh rate.",
        "    --display display   Specify a particular display.",
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
        "    --display display   Specify a particular display.",
        "",
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
        "    --mirror-of-display display     Set the display to mirror 'display'.",
        "",
    ]).format(name=attributes['name'])

    if command in information:
        print(information[command])
    else:
        print('\n'.join([
            "usage: {name} {{ help | version | set | show | mirroring | brightness }}",
            "",
            "Use any of the subcommands with 'help' to get more information:",
            "    help        Print this help information.",
            "    version     Print the version information.",
            "    set         Set the display configuration.",
            "    show        See available display configurations.",
            "    brightness  See or set the current display brightness.",
            "    underscan   See or set the current display underscan.",
            "    mirroring   Set mirroring configuration.",
            "",
        ])).format(name=attributes['name'])

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
    parser_help.add_argument(
        'command',
        choices = [
            'set',
            'show',
            'brightness',
            'underscan',
            'mirroring'
        ],
        nargs = '?',
        default = None
    )

    # Subparser for 'set'.
    parser_set = subparsers.add_parser('set', add_help=False)
    parser_set.add_argument(
        'command',
        choices = [
            'help',
            'closest',
            'highest',
            'exact'
        ],
        nargs = '?',
        default = 'closest'
    )

    # Subparser for 'show'.
    parser_show = subparsers.add_parser('show', add_help=False)
    parser_show.add_argument(
        'command',
        choices = [
            'help',
            'plist',
            'all',
            'closest',
            'highest',
            'exact',
            'displays'
        ],
        nargs = '?',
        default = 'all'
    )

    # Subparser for 'brightness'.
    parser_brightness = subparsers.add_parser('brightness', add_help=False)
    parser_brightness.add_argument('command', choices=['help', 'show', 'set'])
    parser_brightness.add_argument('brightness', type=float, nargs='?')

    # Subparser for 'underscan'.
    parser_underscan = subparsers.add_parser('underscan', add_help=False)
    parser_underscan.add_argument('command', choices=['help', 'show', 'set'])
    parser_underscan.add_argument('underscan', type=float, nargs='?')

    # Subparser for 'mirroring'.
    parser_mirroring = subparsers.add_parser('mirroring', add_help=False)
    parser_mirroring.add_argument('command', choices=['help', 'enable', 'disable'])
    parser_mirroring.add_argument('--mirror-of-display', type=int, default=Quartz.CGMainDisplayID())

    # All of the subcommands have some similar arguments.
    for subparser in [parser_set, parser_show, parser_brightness, parser_underscan, parser_mirroring]:
        subparser.add_argument('--help', action='store_true')
        subparser.add_argument('--display', type=int)
    # These two subparsers have similar arguments.
    for subparser in [parser_set, parser_show]:
        subparser.add_argument('-w', '--width', type=int)
        subparser.add_argument('-h', '--height', type=int)
        subparser.add_argument('-d', '--depth', type=int)
        subparser.add_argument('-r', '--refresh', type=int)
        subparser.add_argument('--no-hidpi', action='store_true')
        subparser.add_argument('--only-hidpi', action='store_true')
        subparser.add_argument('--plist', action='store_true')

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
#     try:
#         manual = [args.width, args.height, args.depth, args.refresh]
#         if any(manual):
#             if args.subcommand not in ['set', 'show']:
#                 usage()
#                 print("Error: Cannot supply manual specifications for subcommand '{}'.".format(subcommand))
#                 sys.exit(1)
#             for element in manual:
#                 if element is None:
#                     usage()
#                     sys.exit("Error: Must have either all or none of the manual specifications.")

    try:
        manual = [args.width, args.height, args.depth, args.refresh]
        if args.subcommand in ['set', 'show'] and not all(manual):
            usage()
            sys.exit("Error: Must have either all or none of the manual specifications.")
        elif args.subcommand not in ['set', 'show'] and any(manual):
            usage()
            sys.exit("Error: Cannot supply manual specifications for subcommand '{}'.".format(subcommand))
    except AttributeError:
        # Evidently we're using a subparser without these attributes.
        # Not an issue.
        pass

#     sys.exit("made it this far")
    # Check if we have specified both not to use HiDPI and only to use HiDPI.
    try:
        hidpi = get_hidpi_value(args.no_hidpi, args.only_hidpi)
    except AttributeError:
        # Probably using a subparser that doesn't check HiDPI settings.
        # And that's okay.
        pass

    if args.subcommand == 'set':
        sub_set(args.command, args.width, args.height, args.depth, args.refresh, args.display, hidpi)
    elif args.subcommand == 'show':
        sub_show(args.command, args.width, args.height, args.depth, args.refresh, args.display, hidpi, args.plist)
    elif args.subcommand == 'brightness':
        sub_brightness(args.command, args.brightness, args.display)
    elif args.subcommand == 'underscan':
        sub_underscan(args.command, args.underscan, args.display)
    elif args.subcommand == 'mirroring':
        sub_mirroring(args.command, args.display, args.mirror_of_display)
