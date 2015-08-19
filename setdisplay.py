#!/usr/bin/python

# We're going to use the magical future print function.
# Mostly this is for easy text output to stderr.
from __future__ import print_function

import argparse
import sys
import Quartz

# A strict rewrite of SetDisplay from C into PyObjC.

MAX_DISPLAYS = 32

class DisplayMode(object):
    def __init__(self, width=0, height=0, bits_per_pixel=0, refresh=0):
        self.width          = width
        self.height         = height
        self.bits_per_pixel = bits_per_pixel
        self.refresh        = refresh

def get_display_bits_per_pixel(mode):
    # Found this on https://code.google.com/r/evilphillip-cocoa-ctypes2/source/browse/pyglet/canvas/cocoa.py?r=fda9f5c0c8823889e0e3fa9d01dbdd63a93e1919
    # The values from /System/Library/Frameworks/IOKit.framework/Headers/graphics/IOGraphicsTypes.h
    IO8BitIndexedPixels = "PPPPPPPP"
    IO16BitDirectPixels = "-RRRRRGGGGGBBBBB"
    IO32BitDirectPixels = "--------RRRRRRRRGGGGGGGGBBBBBBBB"

    encoding = Quartz.CGDisplayModeCopyPixelEncoding(mode)

    if encoding == IO8BitIndexedPixels:
        return 8
    if encoding == IO16BitDirectPixels:
        return 16
    if encoding == IO32BitDirectPixels:
        return 32

def print_short_display_description(mode, show_only_aqua):
    aqua = False
    if Quartz.CGDisplayModeGetIODisplayModeID(mode):
        aqua = True
    width   = Quartz.CGDisplayModeGetWidth(mode)
    height  = Quartz.CGDisplayModeGetHeight(mode)
    bpp     = get_display_bits_per_pixel(mode)
    refresh = Quartz.CGDisplayModeGetRefreshRate(mode)
    if show_only_aqua:
        if aqua:
            print("{width} {height} {bpp} {refresh}".format(
                width   = width,
                height  = height,
                bpp     = bpp,
                refresh = refresh
            ))
    else:
        print("{width} {height} {bpp} {refresh} {usable}".format(
            width   = width,
            height  = height,
            bpp     = bpp,
            refresh = refresh,
            usable  = "Usable" if aqua else "Nonusable"
        ))

def get_all_modes_for_display(display, verbose=False):
    modes       = Quartz.CGDisplayCopyAllDisplayModes(display, None)
    mode_ref    = Quartz.CGDisplayModeRef.alloc().init()
    for mode in modes:
        mode_ref = mode
        print_short_display_description(mode, verbose)
    print("------------------------------------")

def get_mode_for_display(display, exact_scan, find_mode):
    d_width     = sys.maxint / 2
    d_height    = sys.maxint / 2
    d_bpp       = sys.maxint
    d_refresh   = sys.maxint
    modes           = Quartz.CGDisplayCopyAllDisplayModes(display, None)
    matching_mode   = DisplayMode()
    mode_ref        = Quartz.CGDisplayModeRef.alloc().init()
    for mode in modes:
        width           = Quartz.CGDisplayModeGetWidth(mode)
        height          = Quartz.CGDisplayModeGetHeight(mode)
        bits_per_pixel  = get_display_bits_per_pixel(mode)
        refresh         = Quartz.CGDisplayModeGetRefreshRate(mode)

        if exact_scan:
            # Exact matching.
            if width == find_mode.width and height == find_mode.height and bits_per_pixel == find_mode.bits_per_pixel:
                matching_mode.width             = width
                matching_mode.height            = height
                matching_mode.bits_per_pixel    = bits_per_pixel
                matching_mode.refresh           = refresh
                mode_ref = mode
                break
        else:
            dw = abs(width - find_mode.width)
            dh = abs(height - find_mode.height)
            db = abs(bits_per_pixel - find_mode.bits_per_pixel)
            dr = abs(refresh - find_mode.refresh)

            if dw == d_width and dh == d_height and db == d_bpp and dr == d_refresh:
                matching_mode.bits_per_pixel = bits_per_pixel
                matching_mode.refresh = refresh
                d_width     = dw
                d_height    = dh
                d_bpp       = db
                d_refresh   = dr
                mode_ref = mode
            elif dw + dh <= d_width + d_height:
                matching_mode.width             = width
                matching_mode.height            = height
                matching_mode.bits_per_pixel    = bits_per_pixel
                matching_mode.refresh           = refresh
                d_width     = dw
                d_height    = dh
                d_bpp       = db
                d_refresh   = dr
                mode_ref = mode
    print("{width} {height} {bpp} {refresh}".format(
        width   = matching_mode.width,
        height  = matching_mode.height,
        bpp     = matching_mode.bits_per_pixel,
        refresh = matching_mode.refresh
    ))
    return mode_ref

def set_display(display, mode, mirroring, verbose=False):
    print("Setting display {} to mode: ".format(display))
    # This call exists only to ensure the CGBeginDisplayConfiguration call will
    # pass successfully. I don't know why it's necessary, but it is.
    Quartz.CGDisplayBounds(display)
    # Now start the setup of the display.
    (error, config_ref) = Quartz.CGBeginDisplayConfiguration(None)
    if error:
        print("Cannot begin display configuration ({})".format(error), file=sys.stderr)
        sys.exit(1)

    error = Quartz.CGConfigureDisplayWithDisplayMode(config_ref, display, mode, None)
    if error:
        print("Cannot set display configuration ({})".format(error),
        file=sys.stderr)
        sys.exit(1)

    if mirroring:
        Quartz.CGConfigureDisplayMirrorOfDisplay(config_ref, display, Quartz.kCGNullDirectDisplay)
    else:
        main_display = Quartz.CGMainDisplayID()
        if (display != main_display):
            Quartz.CGConfigureDisplayMirrorOfDisplay(config_ref, display, main_display)

    Quartz.CGCompleteDisplayConfiguration(config_ref, Quartz.kCGConfigurePermanently)


def usage():
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--show-all', action='store_true', help="show all possible matches (resolution not changed)")
    parser.add_argument('-c', '--show-closest', action='store_true', help="show closest match (resolution not changed)")
    parser.add_argument('-M', '--mirroring-on', action='store_true', dest='mirroring', help="mirroring on")
    parser.add_argument('-m', '--mirroring-off', action='store_false', dest='mirroring', help="mirroring off")
    parser.add_argument('-n', '--no-change', action='store_true', help="do not change the resolution")
    parser.add_argument('-v', '--verbose', action='store_true', help="verbose")
    parser.add_argument('-x', '--show-exact', action='store_true', help="show exact match")
    parser.add_argument('-y', '--set-highest', action='store_true', help="show and set highest possible resolution")
    parser.add_argument('-z', '--show-highest', action='store_true', help="show highest possible resolution (resolution not changed)")
    parser.add_argument('width', nargs='?', help="manual width")
    parser.add_argument('height', nargs='?', help="manual height")
    parser.add_argument('bpp', nargs='?', help="manual bits per pixel")
    parser.add_argument('refresh', nargs='?', help="manual refresh rate")

    args = parser.parse_args()

    manual = [args.width, args.height, args.bpp, args.refresh]
    if any(manual) and not all(manual):
        raise ValueError("You must supply all of width, height, bpp, and refresh.")

    verbose             = args.verbose
    should_show_all     = args.show_all
    should_find_exact   = args.show_exact
    should_find_highest = args.show_highest or args.set_highest
    should_find_closest = args.show_closest
    enable_mirroring    = args.mirroring

    should_set_display  = True

    if args.no_change or should_show_all or should_find_closest or should_find_exact or (should_find_highest and not args.set_highest):
        should_set_display = False

    mode = DisplayMode(1024, 768, 32, 75)

    if verbose:
        print("Width: {width} Height: {height} BitsPerPixel: {bpp} Refresh rate: {refresh}".format(
            width   = mode.width,
            height  = mode.height,
            bpp     = mode.bits_per_pixel,
            refresh = mode.refresh
        ))

    # Get list of online displays.
    (error, online_displays, displays_count) = Quartz.CGGetOnlineDisplayList(MAX_DISPLAYS, None, None)

    if error:
        print("Cannot get displays ({})".format(error), file=sys.stderr)
        sys.exit(1)

    if verbose:
        print("{} online display(s) found".format(displays_count))

    for index in xrange(displays_count):
        identifier = online_displays[index]
        if verbose and not should_show_all:
            print("------------------------------------")
        original_mode = Quartz.CGDisplayCopyDisplayMode(identifier)
        if not original_mode:
            print("Display 0x{} is invalid".format(identifier), file=sys.stderr)
            sys.exit(1)
        if verbose:
            print("Display 0x{}".format(identifier))
        if should_show_all:
            get_all_modes_for_display(identifier, verbose)
        else:
            if should_find_exact:
                print("------ Exact mode for display -----")
                ref_mode = get_mode_for_display(identifier, True, mode)
                print("------------------------------------")
            elif should_find_highest:
                print("----- Highest mode for display ----")
                mode.width          = sys.maxint / 2
                mode.height         = sys.maxint / 2
                mode.bits_per_pixel = sys.maxint / 2
                mode.refresh        = sys.maxint / 2
                ref_mode = get_mode_for_display(identifier, False, mode)
                print("------------------------------------")
            elif should_find_closest:
                print("----- Closest mode for display ----")
                ref_mode = get_mode_for_display(identifier, False, mode)
                print("------------------------------------")
            else:
                ref_mode = Quartz.CGDisplayModeRef.alloc().init()

            if should_set_display:
                set_display(identifier, ref_mode, enable_mirroring, verbose)
