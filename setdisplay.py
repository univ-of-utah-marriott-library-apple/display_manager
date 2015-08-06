#!/usr/bin/env python

# We're going to use the magical future print function.
# Mostly this is for easy text output to stderr.
from __future__ import print_function

import sys
import CoreFoundation
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
    pass

def get_all_modes_for_display(display, verbose=False):
    pass

def get_mode_for_display(display, exact_scan, find_mode):
    d_width             = sys.maxint / 2
    d_height            = sys.maxint / 2
    d_bpp               = sys.maxint
    d_refresh           = sys.maxint
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
    pass

def usage():
    pass

if __name__ == '__main__':
    verbose             = True
    should_show_all     = False
    should_find_exact   = True
    should_find_highest = False
    should_find_closest = False
    enable_mirroring    = False
    should_set_display  = False
    
    # Get list of online displays.
    (error, online_displays, displays_count) = Quartz.CGGetOnlineDisplayList(MAX_DISPLAYS, None, None)
    
    if error:
        print("Cannot get displays ({})".format(error), file=sys.stderr)
        sys.exit(1)
    
    if verbose:
        print("{} online display(s) found".format(displays_count))
    
    mode = DisplayMode(1024, 768, 32, 75)
    
    for i in xrange(displays_count):
        identifier = online_displays[i]
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
                mode.width          = sys.maxint
                mode.height         = sys.maxint
                mode.bits_per_pixel = sys.maxint
                mode.refresh        = sys.maxint
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
