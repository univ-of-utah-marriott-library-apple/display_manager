#!/usr/bin/python

from __future__ import print_function
 
import os
import sys
import re
import subprocess
import plistlib
from pprint import pprint

import Quartz

import fractions

import time

class Resolution(object):
    '''Simple class to represent a resolution
    '''

    def __init__(self, width, height):
        self.width = int(width)
        self.height = int(height)
        self._ratio = None
    
    def __eq__(self, x):
        '''x.__eq__(y) <==> (x.width, x.height) == (y.width, y.height)
        '''
        return (self.width, self.height) == (x.width, x.height)

    def __ne__(self, x):
        '''x.__ne__(y) <==> (x.width, x.height) != (y.width, y.height)
        '''
        return (self.width, self.height) != (x.width, x.height)

    def __gt__(self, x):
        '''x.__gt__(y) <==> (x.width, x.height) > (y.width, y.height)
        '''
        return (self.width, self.height) > (x.width, x.height)

    def __lt__(self, x):
        '''x.__lt__(y) <==> (x.width, x.height) < (y.width, y.height)
        '''
        return (self.width, self.height) < (x.width, x.height)

    def __ge__(self, x):
        '''x.__ge__(y) <==> (x.width, x.height) >= (y.width, y.height)
        '''
        return (self.width, self.height) >= (x.width, x.height)

    def __le__(self, x):
        '''x.__le__(y) <==> (x.width, x.height) <= (y.width, y.height)
        '''
        return (self.width, self.height) <= (x.width, x.height)

    def __float__(self):
        '''x.__float__() <==> round(float(x.width)/x.height, 2)
        '''
        f = float(self.width)/self.height
        return round(f, 2)

    def __str__(self):
        '''x.__str__() <==> "{0}x{1}".format(x.width, x.height)
        '''
        return "{0}x{1}".format(self.width, self.height)

    @property
    def ratio(self):
        if not self._ratio:
            f = fractions.Fraction(self.width, self.height)
            self._ratio = "{0}:{1}".format(f.numerator, f.denominator)
        return self._ratio


def resolutionFromString(r):
    '''Returns a resolution object from string (e.g. '1440x900')
    '''
    w, h = r.split('x')
    return Resolution(w, h)

# https://developer.apple.com/documentation/coregraphics/quartz_display_services
# Useful functions from Quartz
#   CGMainDisplayID()
#   CGGetOnlineDisplayList() 
#   - Provides a list of displays that are online (active, mirrored, or sleeping).
#   CGGetActiveDisplayList()
#   - Provides a list of displays that are active (or drawable).
#   CGDisplayPixesHigh
#   - Returns the display height in pixel units.
#   CGDisplayPixelsWide
#   - Returns the display width in pixel units.
#   CGDisplayBitsPerPixel
#   - Returns the number of bits used to represent a pixel in the framebuffer.
#   CGDisplayScreenSize
#   - Returns the width and height of a display in millimeters.

class DisplayError(Exception):
    pass


class Display(object):
    '''Convienence class wrapping useful functions from Apple's Quartz 
    using CGDDirectDisplayID (i.e. display id)
    
    Also calculates physical display measurements
    '''
        
    def __init__(self, id):
        self.id = id
        # what happens if invalid displayID?
        w, h = Quartz.CGDisplayScreenSize(id)
        self.width = round(w, 2)
        self.height = round(h, 2)
        self._ratio = None
    
    def __float__(self):
        '''x.__float__() <==> round(float(x.width)/x.height, 2)

        Returns float value of Width/Height rounded to 2 decimal places
        '''
        f = float(self.width)/self.height
        return round(f, 2)
        
    @property
    def ratio(self):
        '''Reduced form of display in ratio notation (e.g. '16:9')
        '''
        if not self._ratio:
            f = fractions.Fraction(float(self))
            self._ratio = "{0}:{1}".format(f.numerator, f.denominator)
        return self._ratio
        
    def isMain(self):
        '''x.isMain() <==> Quartz.CGDisplayIsMain(x.id)

        Returns Boolean value indicating whether display is the main 
        display.
        '''
        return Quartz.CGDisplayIsMain(self.id)
    
    def isBuiltin(self):
        '''x.isBuiltIn() <==> Quartz.CGDisplayIsBuiltIn(x.id)

        Returns Boolean value indicating whether display is built-in.
        '''
        return Quartz.CGDisplayIsBuiltin(self.id)
    
    def rotation(self):
        '''x.rotation() <==> Quartz.CGDisplayRotation(x.id)

        Returns the rotation angle of a display in degrees.
        '''
        # Not sure what this will return
        return Quartz.CGDisplayRotation(self.id)
    
    def vendorNumber(self):
        '''x.vendorNumber() <==> Quartz.CGDisplayVendorNumber(x.id)

        Returns the vendor number of the specified display's monitor.
        '''
        return Quartz.CGDisplayVendorNumber(self.id)

    def modelNumber(self):
        '''x.modelNumber() <==> Quartz.CGDisplayModelNumber(x.id)

        Returns the model number of a display monitor.
        '''
        return Quartz.CGDisplayModelNumber(self.id)

    def serialNumber(self):
        '''x.serialNumber() <==> Quartz.CGDisplaySerialNumber(x.id)

        Returns the serial number of a display monitor.
        '''
        return Quartz.CGDisplaySerialNumber(self.id)

    def isAsleep(self):
        '''x.isAsleep() <==> Quartz.CGDisplayIsAsleep(x.id)

        Returns Boolean indicating whether display is sleeping.
        '''
        return Quartz.CGDisplayIsAsleep(self.id)

    def isActive(self):
        '''x.isActive() <==> Quartz.CGDisplayIsActive(x.id)

        Returns Boolean indicating whether a display is active.
        '''
        return Quartz.CGDisplayIsActive(self.id)

    def isOnline(self):
        '''x.isOnline() <==> Quartz.CGDisplayIsOnline(x.id)

        Returns Boolean indicating whether display is connected or online
        '''
        return Quartz.CGDisplayIsOnline(self.id)
    
    def isInMirrorSet(self):
        '''x.isInMirrorSet() <==> Quartz.CGDisplayIsInMirrorSet(x.id)
        
        Returns Boolean indicating whether display is in a mirroring set.
        '''
        return Quartz.CGDisplayIsInMirrorSet(self.id)

    def mirrorsDisplay(self):
        '''x.mirrorsDisplay() <==> Quartz.CGDisplayMirrorsDisplay(x.id)
        
        For secondary display in a mirroring set, returns the primary 
        display.
        
        Display is additionally returned as a Display object, if display
        is not in a mirroring set, returns None
        '''
        # TO-DO: make sure this has no errors when display is not in
        #        mirroring set
        primary_id = Quartz.CGDisplayMirrorsDisplay(self.id)
        return Display(primary_id)
        

## Struct-like thing for easy display.
class DisplayMode(object):
    '''Class with some convienence functions
    '''
    def __init__(self, mode):
        if not isinstance(mode, Quartz.CGDisplayModeRef):
            err = 'Invalid CGDisplayModeRef: {0!r}'.format(mode)
            raise DisplayError(err)

        # save original mode for use when setting displays 
        self.mode = mode

        # Effective Resolution
        self.width = Quartz.CGDisplayModeGetWidth(mode)
        self.height = Quartz.CGDisplayModeGetHeight(mode)
        r = Resolution(self.width, self.height)
        self.resolution = r

        # Real Pixel Resolution
        self.pixelWidth = Quartz.CGDisplayModeGetPixelWidth(mode)
        self.pixelHeight = Quartz.CGDisplayModeGetPixelHeight(mode)
        pR = Resolution(self.pixelWidth, self.pixelHeight)
        self.pixelResolution = pR

        # HiDPI is if pixelResolution is greater than effect resolution
        self.HiDPI = True if pR > r else False
        self.refreshRate = Quartz.CGDisplayModeGetRefreshRate(mode)
        self.usable = Quartz.CGDisplayModeIsUsableForDesktopGUI(mode)
        
    def __str__(self):
        res = self.resolution
        rate = self.refreshRate
        ratio = self.ratio
        hidpi = ']'
        if self.HiDPI:        
            hidpi = ", HiDPI: {0}]".format(self.pixelResolution)
        
        return "{0:9} [refresh: {1}, ratio: {2}{3}".format(
                 res, rate, ratio, hidpi)
    
     
    @property
    def ratio(self):
        '''ratio from the resolution
        '''
        return self.resolution.ratio

#     @property
#     def HiDPI(self):
#         '''Calculate HiDPI (if its needed)
#         '''
#         return self.resolution.ratio

    # Use rich comparison from Resolution() class to most of 
    # the heavy lifting for comparing DisplayModes, adding HiDPI as the
    # tie-breaker
    def __eq__(self, x):
        '''x.__eq__(y) <==> (x.resolution, x.HiDPI) == (y.resolution, y.HiDPI)
        '''
        # Take HiDPI into consideration
        return (self.resolution, self.HiDPI) == (x.resolution, x.HiDPI)

    def __ne__(self, x):
        '''x.__ne__(y) <==> (x.resolution, x.HiDPI) != (y.resolution, y.HiDPI)
        '''
        return (self.resolution, self.HiDPI) != (x.resolution, x.HiDPI)

    def __gt__(self, x):
        '''x.__gt__(y) <==> (x.resolution, x.HiDPI) > (y.resolution, y.HiDPI)
        '''
        # HiDPI resolution is greater than normal resolution
        return (self.resolution, self.HiDPI) > (x.resolution, x.HiDPI)

    def __lt__(self, x):
        '''x.__lt__(y) <==> (x.resolution, x.HiDPI) < (y.resolution, y.HiDPI)
        '''
        # normal resolution is less than HiDPI resolution
        return (self.resolution, self.HiDPI) < (x.resolution, x.HiDPI)

    def __ge__(self, x):
        '''x.__ge__(y) <==> (x.resolution, x.HiDPI) >= (y.resolution, y.HiDPI)
        '''
        # HiDPI resolution is greater than normal resolution
        return (self.resolution, self.HiDPI) >= (x.resolution, x.HiDPI)

    def __le__(self, x):
        '''x.__le__(y) <==> (x.resolution, x.HiDPI) <= (y.resolution, y.HiDPI)
        '''
        # HiDPI resolution is greater than normal resolution
        return (self.resolution, self.HiDPI) <= (x.resolution, x.HiDPI)



def allDisplayModes(id, dupLowRes=True, usable=True):
    '''Return list of all DisplayModes for displayID
    '''
    # Include duplicate Low Resolution Modes
    #   Setting to True will give us all DisplayModes including 
    #   non-HiDPI modes

    options = None
    if dupLowRes:
        k = Quartz.kCGDisplayShowDuplicateLowResolutionModes
        v = Quartz.kCFBooleanTrue
        options = {k: v}

    modes = []
    for m in Quartz.CGDisplayCopyAllDisplayModes(id, options):
        modes.append(DisplayMode(m))

    # filter out unusable modes unless usable=False
    usable_modes = []
    if usable:
        usable_modes = [m for m in modes if m.usable]

    return usable_modes

def mainDisplayID():
    '''return display id of main display
    '''
    return Quartz.CGMainDisplayID()

def onlineDisplayIDs():
    '''Return list of "Online" displayIDs
    Online <==> displays that are active, mirrored, or sleeping
    '''
    
    # TESTS:
    #   - what happens when there are no connected displays?
    #   - what happens before login?
    
    # returncode, tuple of displayIDs, and count (ignored)
    retcode, ids, _ = Quartz.CGGetOnlineDisplayList(32, None, None)
    
    # Not sure how this can fail, but feel like we should check
    if retcode != 0:
        # This may have to be adjusted as return values are discovered
        e = ("CGGetOnlineDisplayList returned non-zero value: "
             "{0}".format(retcode))
        raise DisplayError(e)

    # list of displayIDs (integers)
    return [i for i in ids]

def cancelDisplayChange(conf):
    
    err = Quartz.CGCancelDisplayConfiguration(conf)
    if err:
        e = "CGCancelDisplayConfiguration failed: {0}".format(err)
        raise DisplayError(e)

def setDisplayMode(id, mode):
    # Start the configuration, get CGDisplayConfigRef
    err, conf = Quartz.CGBeginDisplayConfiguration(None)
    if err:
        e = "CGBeginDisplayConfiguration failed: {0}".format(err)
        raise DisplayError(e)

    # original CGDisplayModeRef from our DisplayMode
    CGm = mode.mode

    # populate CGDisplayConfigRef with settings from the mode we provided  
    err = Quartz.CGConfigureDisplayWithDisplayMode(conf, id, CGm, None)
    if err:
        e = "CGConfigureDisplayWithDisplayMode failed: {0}".format(err)
        cancelDisplayChange(conf)
        raise DisplayError(e)
    
    # TO-DO: Set mirroring options

    # Complete the configuration, permanently adjust the settings
    options = Quartz.kCGConfigurePermanently
    Quartz.CGCompleteDisplayConfiguration(conf, options)

def setDisplayMode2(id, mode):
    '''NOT VIABLE
    Only able to change the DisplayMode for the duration of the script
    '''
    opt = None
    m = mode.mode
    err = Quartz.CGDisplaySetDisplayMode(id, m, opt)
    if err:
        e = "CGDisplaySetDisplayMode failed: {0}".format(err)
        raise DisplayError(e)
        
def main():
    id = Quartz.CGMainDisplayID()
    modes = allDisplayModes(id, dupLowRes=True, usable=False)
#     modes = allDisplayModes(id)

    r = resolutionFromString('2560x1600')
#     r = resolutionFromString('1680x1050')
#     r = resolutionFromString('1440x900')
#     r = resolutionFromString('1280x800')
#     r = resolutionFromString('1024x640')
#     r = resolutionFromString('825x525')
#     r = resolutionFromString('720x450')

#     for x in sorted([m for m in modes if m.HiDPI], reverse=True):
#         print(x)
    biggest = sorted([m for m in modes if m.HiDPI], reverse=True)[0]
    print(biggest)
    
    raise SystemExit()
#     
#     res = [m for m in modes if m == r]
    
    
    
    
#     for m in sorted(modes, reverse=True):
#         print(m)
#     raise SystemExit()

    for m in sorted(modes, reverse=True):
#         print(m)
        if m.resolution == r:
            print("setting resolution as: {0}".format(m))
            setDisplayMode(id, m)
            break
        else:
            print("skipping: {0}".format(m))

#     time.sleep(30)

if __name__ == '__main__':
    main()

