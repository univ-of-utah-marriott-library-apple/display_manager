#!/usr/bin/python

from __future__ import print_function
 
import os
import sys
import re
import subprocess
import plistlib
from pprint import pprint
import Quartz
import CoreFoundation as CF


def get_display_info(id):
    bounds = Quartz.CGDisplayBounds(id)
    p_height = Quartz.CGDisplayPixelsHigh(id)
    p_width = Quartz.CGDisplayPixelsWide(id)
    
    print("bounds: {}".format(bounds))
    print("height: {}".format(p_height))
    print("width: {}".format(p_width))
    ratio = float(p_width)/float(p_height)

    print("ratio: {}".format(ratio))

def analyze_modes(modes):
    pass

def main_display_id():
    '''
    Returns CGDirectDisplayID of Main Display

    CGDirectDisplayID - type(int) - used in many other CGDisplay functions
    '''
    main_display_id = Quartz.CGMainDisplayID()
    # print("Main Display ID: {}".format(main_display_id))
    # print("type: {}".format(type(main_display_id)))
    return main_display_id

def display_bounds(id):
    '''
    Returns CGRect with bounds from display id
    '''
    # Quartz.CGDisplayBounds(CGDirectDisplayID)
    displayBounds = Quartz.CGDisplayBounds(id)
    print("Raw: {}".format(display_bounds))

def current_mode(id):
    mode = Quartz.CGDisplayCopyDisplayMode(id)
    return mode

def screen_size(id):
    '''
    Returns NSSize object with width and height in millimeters
    '''
    return Quartz.CGDisplayScreenSize(id)





class Resolution(object):

    def __init__(self, width, height, mode=None):
        self.width = int(width)
        self.height = int(height)
        self.mode = mode
        self.area = int(width) * int(height)
    
    def __gt__(self, x):
        '''
        x.width > y.width and x.height > y.height
        '''
        return (self.width > x.width and self.height > x.height)

    def __div__(self, x):
        '''
        x.area / y.area
        '''
        return float(self.area) / float(x.area)

    def __ge__(self, x):
        '''
        x.width >= y.width and x.height >= y.height
        '''
        return (self.width >= x.width and self.h >= x.height)

    def __eq__(self, y):
        '''
        x.width == y.width and x.height == y.height
        '''
        return (self.w == x.width and self.height == x.height)
    
    def __str__(self):
        '''
        x.__str__() <==> "{}x{}".format(x.width, x.height)
        '''
        return "{}x{}".format(self.width, self.height)

    def __repr__(self):
        '''
        x.__repr__(...) -> x.__str__()
        '''
        return self.__str__()


class Display(object):

    def __init__(self, id):
        self.id = id
        self.builtin = Quartz.CGDisplayIsBuiltin(id)
        self.main = True if self.id == Quartz.CGMainDisplayID() else False
        size = Quartz.CGDisplayScreenSize(id)
        self.ratio = float(size.width) / float(size.height)
        self.width = size.width
        self.height = size.height

        self.modes = self.allDisplayModes()
        current_mode = Quartz.CGDisplayCopyDisplayMode(id)

        for mode in self.modes:
            if mode.id == Quartz.CGDisplayModeGetIODisplayModeID(current_mode):
                self.current_mode = mode.id
        

        
    def modesMatchingRatio(self):
        pass

    def allDisplayModes(self):
        key = Quartz.kCGDisplayShowDuplicateLowResolutionModes
        options = { key: Quartz.kCFBooleanTrue }
        modes = []
        for mode in Quartz.CGDisplayCopyAllDisplayModes(self.id, options):
            modes.append(DisplayMode(mode))
        return modes

    def __str__(self):
        return "{}: {} ({}) scale: {}".format(self.id, self.resolution, 
                                              self.pixels, self.scale)


class DisplayMode(object):
    def __init__(self, mode):
        self._mode = mode

        self.id = Quartz.CGDisplayModeGetIODisplayModeID(mode)
        self.width = Quartz.CGDisplayModeGetWidth(mode)
        self.height = Quartz.CGDisplayModeGetHeight(mode)
        self.pWidth = Quartz.CGDisplayModeGetPixelWidth(mode)
        self.pHeight = Quartz.CGDisplayModeGetPixelHeight(mode)

        self.resolution = Resolution(self.width, self.height)
        self.pixels = Resolution(self.pWidth, self.pHeight)
        self.scale = self.pixels / self.resolution
        self.refresh = Quartz.CGDisplayModeGetRefreshRate(mode)
        self.encoding = Quartz.CGDisplayModeCopyPixelEncoding(mode)
        self.usable = Quartz.CGDisplayModeIsUsableForDesktopGUI(mode)

#     def __str__(self):
#         return "{}: {} ({}) scale: {}".format(self.id, self.resolution, 
#                                               self.pixels, self.scale)

    def __str__(self):
        s = "ID: {}\n"
        return "{}: {} ({}) scale: {}".format(self.id, self.resolution, 
                                              self.pixels, self.scale)

        
def all_display_modes_test(id):
    '''
    Returns array of display modes with some information and a reference to
    the actual CGDisplayMode object for use with CGDisplaySetDisplayMode.
    '''
    # Note: this function seems limited

    display_modes = []
    # We can't use the mode directly, so we have to access the values in each
    # DisplayMode
    options = {
        Quartz.kCGDisplayShowDuplicateLowResolutionModes: Quartz.kCFBooleanTrue,
    }
#     for mode in Quartz.CGDisplayCopyAllDisplayModes(id, None):
    for mode in Quartz.CGDisplayCopyAllDisplayModes(id, options):
        # You can see there is a lot more in the DisplayMode than is available
        # if you uncomment the print below:
        # print(mode)

        # These are all the supported functions to get the information out of
        # a DisplayMode
        display_modes.append({
            'width': Quartz.CGDisplayModeGetWidth(mode),
            'height': Quartz.CGDisplayModeGetHeight(mode),
            'p_width': Quartz.CGDisplayModeGetPixelWidth(mode),
            'p_height': Quartz.CGDisplayModeGetPixelHeight(mode),

            'refresh': Quartz.CGDisplayModeGetRefreshRate(mode),
            'UsableForDesktopGUI': Quartz.CGDisplayModeIsUsableForDesktopGUI(mode),
            'pixels': Quartz.CGDisplayModeCopyPixelEncoding(mode),
            '_mode': mode,

            'IODisplayModeID': Quartz.CGDisplayModeGetIODisplayModeID(mode),
            'IOFlags': Quartz.CGDisplayModeGetIOFlags(mode),
            # Not sure how this is useful when it doesn't accept the mode as 
            # an argument
            'TypeID': Quartz.CGDisplayModeGetTypeID(),
        })
        
    return display_modes

# def debug(mode):
#     s = "   width: {}\n".format(mode['width']) \
#         + "  height: {}\n".format(mode['height']) \
#         + "     bpp: {}\n".format(mode['bpp']) \
#         + " refresh: {}\n".format(mode['refresh']) \
#         + "   HiDPI: {}\n".format(mode['dpi_scalar']) \
#         + "  pixels: {}\n".format(mode['pixels']) \
#         + "     r_w: {}\n".format(mode['raw_width']) \
#         + "     r_h: {}\n".format(mode['raw_height']) \
#         + "   ratio: {}\n".format(mode['ratio']) \
#         + "   mode: {}\n".format(mode['raw_mode']) \
#         + "-" * 80 
#     return s

## Helper Functions
def get_hidpi_scalar(raw_width, raw_height, res_width, res_height):
    """
    Uses extra methods to find the HiDPI scalar for a display.

    :param mode: The raw mode from the Quartz library for the display.
    :return: Either None if there is no scaling, or else the value of the
        scaling scalar.
    """
#     raw_width  = Quartz.CGDisplayModeGetPixelWidth(mode)
#     raw_height = Quartz.CGDisplayModeGetPixelHeight(mode)
#     res_width  = Quartz.CGDisplayModeGetWidth(mode)
#     res_height = Quartz.CGDisplayModeGetHeight(mode)
    if raw_width == res_width and raw_height == res_height:
        return None
    else:
        if raw_width / res_width != raw_height / res_height:
            raise RuntimeError("Vertical and horizontal dimensions aren't scaled properly... mode: {}".format(mode))
        return raw_width / res_width



# useful function
def set_display(id, mode):
    (err, config) = Quartz.CGBeginDisplayConfiguration(None)
    if err:
        print("Could not begin configuration: {}".format(err))
        sys.exit(8)

    err = Quartz.CGConfigureDisplayWithDisplayMode(config, id, mode, None)
    if err:
        print("Failed to configure: {}".format(err))
        # Yeah, there were errors. Let's cancel the configuration.
        err = Quartz.CGCancelDisplayConfiguration(config)
        if err:
            # Apparently this can fail too? Huh.
            print("Failed to cancel configuration: {}".format(err))
        sys.exit(9)

    Quartz.CGCompleteDisplayConfiguration(config, Quartz.kCGConfigurePermanently)





def main():

#     displaycnt = None
#     (err, display_id, x) = Quartz.CGGetOnlineDisplayList(32, None, None)
#     displays = []
#     for id in display_id:
#         displays.append(Display(id))
# 
#     for display in displays:
#         print(display)
        
    id = main_display_id()
#     display = Display(id)
#     for m in display.modes:
#         print(m)
#     get_display_info(id)

#     print(current_mode(id))

    modes = all_display_modes_test(id)
    m = []
    for mode in modes:
        m.append(Resolution(mode['width'], mode['height'], mode['_mode']))
    analyze_modes(modes)
    m.sort(reverse=True)
    
#     
    set_display(id, m[0].mode)

#     pprint(all_display_modes(id))
#     size = screen_size(id)
#     print(size)
#     print(size.height)
#     print(size.width)
#     print(float(size.width/size.height))

if __name__ == '__main__':
    main()

