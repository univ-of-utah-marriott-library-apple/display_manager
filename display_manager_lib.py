#!/usr/bin/python

# Display Manager, version 1.0.0

# Programmatically manages Mac displays.
# Can set screen resolution, color depth, refresh rate, screen mirroring, and brightness.

import objc             # access Objective-C functions and variables
import CoreFoundation   # work with Objective-C data types
import Quartz           # work with system graphics


# Configured for global usage; otherwise, must be re-instantiated each time it is called
iokit = None


class DisplayError(Exception):
    """
    Raised if a display cannot perform the requested operation (or access the requested property)
        (e.g. does not have a matching display mode, display cannot modify this setting, etc.)
    """
    pass


class Display(object):
    """
    Virtual representation of a physical display.

    Contains properties regarding display information for a given physical display, along with a few
    useful helper functions to configure the display.
    """

    def __init__(self, displayID):
        """
        :param displayID: The DisplayID of the display to manipulate
        """
        getIOKit()

        # Check whether displayID is actually a display
        (error, allDisplayIDs, count) = Quartz.CGGetOnlineDisplayList(32, None, None)  # max 32 displays
        if displayID not in allDisplayIDs or error:
            raise DisplayError("Display {} not found".format(displayID))
        else:
            self.displayID = displayID

    def __lt__(self, other):
        return self.displayID < other.displayID

    def __gt__(self, other):
        return self.displayID > other.displayID

    def __eq__(self, other):
        return self.displayID == other.displayID

    # General properties

    @property
    def isMain(self):
        """
        :return: Boolean for whether this Display is the main display
        """
        return Quartz.CGDisplayIsMain(self.displayID)

    @property
    def tag(self):
        """
        :return: The display tag for this Display
        """
        if self.isMain:
            return "main"
        # is external display
        else:
            # Get all the external displays (in order)
            externals = sorted(getAllDisplays())
            for display in externals:
                if display.isMain:
                    externals.remove(display)
                    break

            for i in range(len(externals)):
                if self == externals[i]:
                    return "ext" + str(i)

    @property
    def __servicePort(self):
        """
        :return: The integer representing this display's service port.
        """
        return Quartz.CGDisplayIOServicePort(self.displayID)

    @staticmethod
    def __rightHidpi(mode, hidpi):
        """
        Evaluates whether the mode fits the user's HiDPI specification.

        :param mode: The mode to be evaluated.
        :param hidpi: HiDPI code. 0 returns everything, 1 returns only non-HiDPI, and 2 returns only HiDPI.
        :return: Whether the mode fits the HiDPI description specified by the user.
        """
        if (
                (hidpi == 0)  # fits HiDPI or non-HiDPI (default)
                or (hidpi == 1 and not mode.hidpi)  # fits only non-HiDPI
                or (hidpi == 2 and mode.hidpi)  # fits only HiDPI
        ):
            return True
        else:
            return False

    # Mode properties and methods

    @property
    def currentMode(self):
        """
        :return: The current Quartz "DisplayMode" interface for this display.
        """
        return DisplayMode(Quartz.CGDisplayCopyDisplayMode(self.displayID))

    @property
    def allModes(self):
        """
        :return: All possible Quartz "DisplayMode" interfaces for this display.
        """
        modes = []
        # options forces Quartz to show HiDPI modes
        options = {Quartz.kCGDisplayShowDuplicateLowResolutionModes: True}
        for mode in Quartz.CGDisplayCopyAllDisplayModes(self.displayID, options):
            modes.append(DisplayMode(mode))
        return modes

    def highestMode(self, hidpi=0):
        """
        :param hidpi: HiDPI code. 0 returns everything, 1 returns only non-HiDPI, and 2 returns only HiDPI.
        :return: The Quartz "DisplayMode" interface with the highest display resolution for this display.
        """
        highest = None
        for mode in self.allModes:
            if highest:
                if mode > highest and self.__rightHidpi(mode, hidpi):
                    highest = mode
            else:  # highest hasn't been set yet, so anything is the highest
                highest = mode

        if highest:
            return highest
        else:
            if hidpi == 1:
                raise DisplayError(
                    "Display \"{}\" cannot be set to any non-HiDPI resolutions".format(self.tag))
            elif hidpi == 2:
                raise DisplayError(
                    "Display \"{}\" cannot be set to any HiDPI resolutions".format(self.tag))
            else:
                raise DisplayError(
                    "Display \"{}\"\'s resolution cannot be set".format(self.tag))

    def closestMode(self, width, height, depth=32.0, refresh=0.0, hidpi=0):
        """
        :param width: Desired width
        :param height: Desired height
        :param depth: Desired pixel depth
        :param refresh: Desired refresh rate
        :param hidpi: HiDPI code. 0 returns everything, 1 returns only non-HiDPI, and 2 returns only HiDPI
        :return: The closest Quartz "DisplayMode" interface possible for this display.
        """
        whdr = None  # matches width, height, depth, and refresh
        whd = None   # matches width, height, and depth
        wh = None    # matches width and height

        for mode in self.allModes:
            widthMatch = mode.width == width
            heightMatch = mode.height == height
            depthMatch = mode.depth == depth
            refreshMatch = mode.refresh == refresh
            hidpiMatch = self.__rightHidpi(mode, hidpi)

            if widthMatch and heightMatch and depthMatch and refreshMatch and hidpiMatch:
                return mode
            elif widthMatch and heightMatch and depthMatch and refreshMatch:
                whdr = mode
            elif widthMatch and heightMatch and depthMatch:
                whd = mode
            elif widthMatch and heightMatch:
                wh = mode

        for match in [whdr, whd, wh]:  # iterate through the "close" modes in order of closeness
            if match:
                return match

        raise DisplayError(
            "Display \"{}\" cannot be set to {}x{}".format(self.tag, width, height))

    def setMode(self, mode):
        """
        :param mode: The Quartz "DisplayMode" interface to set this display to.
        """
        (error, configRef) = Quartz.CGBeginDisplayConfiguration(None)
        if error:
            raise DisplayError(
                "Display \"{}\"\'s resolution cannot be set to {}x{} at {} Hz".format(
                    self.tag, mode.width, mode.height, mode.refresh))

        error = Quartz.CGConfigureDisplayWithDisplayMode(configRef, self.displayID, mode.raw, None)
        if error:
            Quartz.CGCancelDisplayConfiguration(configRef)
            raise DisplayError(
                "Display \"{}\"\'s resolution cannot be set to {}x{} at {} Hz".format(
                    self.tag, mode.width, mode.height, mode.refresh))

        Quartz.CGCompleteDisplayConfiguration(configRef, Quartz.kCGConfigurePermanently)

    # Rotation properties and methods

    @property
    def rotation(self):
        """
        :return: Rotation of this display, in degrees.
        """
        return int(Quartz.CGDisplayRotation(self.displayID))

    def setRotate(self, angle):
        """
        :param angle: The angle of rotation.
        """
        angleCodes = {0: 0, 90: 48, 180: 96, 270: 80}
        rotateCode = 1024
        if angle % 90 != 0:  # user entered inappropriate angle, so we quit
            raise ValueError("Can only rotate by multiples of 90 degrees.")
        # "or" the rotate code with the right angle code (which is being moved to the right part of the 32-bit word)
        options = rotateCode | (angleCodes[angle % 360] << 16)

        # Actually rotate the screen
        error = iokit["IOServiceRequestProbe"](self.__servicePort, options)

        if error:
            raise DisplayError(
                "Display \"{}\"\'s rotation cannot be set".format(self.tag))

    # Brightness properties and methods

    @property
    def brightness(self):
        """
        :return: Brightness of this display, from 0 to 1.
        """
        service = self.__servicePort
        (error, brightness) = iokit["IODisplayGetFloatParameter"](service, 0, iokit["kDisplayBrightness"], None)
        if error:
            raise DisplayError(
                "Display \"{}\"\'s brightness cannot be set".format(self.tag))
        else:
            return brightness

    def setBrightness(self, brightness):
        """
        :param brightness: The desired brightness, from 0 to 1.
        """
        error = iokit["IODisplaySetFloatParameter"](self.__servicePort, 0, iokit["kDisplayBrightness"], brightness)
        if error:
            if self.isMain:
                raise DisplayError(
                    "Display \"{}\"\'s brightness cannot be set".format(self.tag))
            else:
                raise DisplayError(
                    "Display \"{}\"\'s brightness cannot be set.\n"
                    "External displays may not be compatible with Display Manager."
                    "Try setting manually on device hardware.\n".format(self.tag))

    # Underscan properties and methods

    @property
    def underscan(self):
        """
        :return: Display's active underscan setting, from 1 (0%) to 0 (100%).
            (Yes, it doesn't really make sense to have 1 -> 0 and 0 -> 100, but it's how IOKit reports it.)
        """
        (error, underscan) = iokit["IODisplayGetFloatParameter"](
            self.__servicePort, 0, iokit["kDisplayUnderscan"], None)
        if error:
            raise DisplayError(
                "Display \"{}\"\'s underscan cannot be set".format(self.tag))
        else:
            # IOKit handles underscan values as the opposite of what makes sense, so I switch it here.
            # e.g. 0 -> maximum (100%), 1 -> 0% (default)
            return float(abs(underscan - 1))

    def setUnderscan(self, underscan):
        """
        :param underscan: Underscan value, from 0 (no underscan) to 1 (maximum underscan).
        """
        # IOKit handles underscan values as the opposite of what makes sense, so I switch it here.
        # e.g. 0 -> maximum (100%), 1 -> 0% (default)
        underscan = float(abs(underscan - 1))

        error = iokit["IODisplaySetFloatParameter"](self.__servicePort, 0, iokit["kDisplayUnderscan"], underscan)
        if error:
            raise DisplayError(
                "Display \"{}\"\'s underscan cannot be set".format(self.tag))

    # Mirroring properties and methods

    @property
    def mirrorOf(self):
        """
        Checks whether self is mirroring another display
        :return: The Display that self is mirroring; if self is not mirroring
            any display, returns None
        """
        # The display which self is mirroring
        masterDisplayID = Quartz.CGDisplayMirrorsDisplay(self.displayID)
        if masterDisplayID == Quartz.kCGNullDirectDisplay:
            # self is not mirroring any display
            return None
        else:
            return Display(masterDisplayID)

    def setMirrorOf(self, mirrorDisplay):
        """
        :param mirrorDisplay: The Display which this Display will mirror.
            Input a NoneType to stop mirroring.
        """
        (error, configRef) = Quartz.CGBeginDisplayConfiguration(None)
        if error:
            raise DisplayError(
                "Display \"{}\" cannot be set to mirror display \"{}\"".format(self.tag, mirrorDisplay.tag))

        # Will be passed a None mirrorDisplay to disable mirroring. Cannot mirror self.
        if mirrorDisplay is None or mirrorDisplay.displayID == self.displayID:
            Quartz.CGConfigureDisplayMirrorOfDisplay(configRef, self.displayID, Quartz.kCGNullDirectDisplay)
        else:
            Quartz.CGConfigureDisplayMirrorOfDisplay(configRef, self.displayID, mirrorDisplay.displayID)

        Quartz.CGCompleteDisplayConfiguration(configRef, Quartz.kCGConfigurePermanently)


class DisplayMode(object):
    """
    Represents a DisplayMode as implemented in Quartz.
    """

    def __init__(self, mode):
        # Low-hanging fruit
        self.width = int(Quartz.CGDisplayModeGetWidth(mode))
        self.height = int(Quartz.CGDisplayModeGetHeight(mode))
        self.refresh = float(Quartz.CGDisplayModeGetRefreshRate(mode))
        self.raw = mode

        # Pixel depth
        depthMap = {
            "PPPPPPPP": 8.0,
            "-RRRRRGGGGGBBBBB": 16.0,
            "--------RRRRRRRRGGGGGGGGBBBBBBBB": 32.0,
            "--RRRRRRRRRRGGGGGGGGGGBBBBBBBBBB": 30.0
        }
        self.depth = depthMap[Quartz.CGDisplayModeCopyPixelEncoding(mode)]

        # HiDPI status
        maxWidth = Quartz.CGDisplayModeGetPixelWidth(mode)  # the maximum display width for this display
        maxHeight = Quartz.CGDisplayModeGetPixelHeight(mode)  # the maximum display width for this display
        self.hidpi = (maxWidth != self.width and maxHeight != self.height)  # if they're the same, mode is not HiDPI

    def __str__(self):
        return "resolution: {width}x{height}, refresh rate: {refresh}, HiDPI: {hidpi}".format(**{
            "width": self.width, "height": self.height, "depth": self.depth,
            "refresh": self.refresh, "hidpi": self.hidpi
        })

    def __lt__(self, other):
        return self.width * self.height < other.width * other.height

    def __gt__(self, other):
        return self.width * self.height > other.width * other.height

    def __eq__(self, other):
        return self.width * self.height == other.width * other.height


def getMainDisplay():
    """
    :return: The main Display.
    """
    return Display(Quartz.CGMainDisplayID())


def getAllDisplays():
    """
    :return: A list containing all currently-online displays.
    """
    (error, displayIDs, count) = Quartz.CGGetOnlineDisplayList(32, None, None)  # max 32 displays
    if error:
        raise DisplayError("Could not retrieve displays list")

    displays = []
    for displayID in displayIDs:
        displays.append(Display(displayID))
    return sorted(displays)


def getIOKit():
    """
    This handles the importing of specific functions and variables from the
    IOKit framework. IOKit is not natively bridged in PyObjC, so the methods
    must be found and encoded manually to gain their functionality in Python.

    :return: A dictionary containing several IOKit functions and variables.
    """
    global iokit
    if not iokit:  # iokit may have already been instantiated, in which case, nothing needs to be done
        # The dictionary which will contain all of the necessary functions and variables from IOKit
        iokit = {}

        # Retrieve the IOKit framework
        iokitBundle = objc.initFrameworkWrapper(
            "IOKit",
            frameworkIdentifier="com.apple.iokit",
            frameworkPath=objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"),
            globals=globals()
        )

        # The IOKit functions to be retrieved
        functions = [
            ("IOServiceGetMatchingServices", b"iI@o^I"),
            ("IODisplayCreateInfoDictionary", b"@II"),
            ("IODisplayGetFloatParameter", b"iII@o^f"),
            ("IODisplaySetFloatParameter", b"iII@f"),
            ("IOServiceRequestProbe", b"iII"),
            ("IOIteratorNext", b"II"),
        ]

        # The IOKit variables to be retrieved
        variables = [
            ("kIODisplayNoProductName", b"I"),
            ("kIOMasterPortDefault", b"I"),
            ("kIODisplayOverscanKey", b"*"),
            ("kDisplayVendorID", b"*"),
            ("kDisplayProductID", b"*"),
            ("kDisplaySerialNumber", b"*"),
        ]

        # Load functions from IOKit.framework into our iokit
        objc.loadBundleFunctions(iokitBundle, iokit, functions)
        # Bridge won't put straight into iokit, so globals()
        objc.loadBundleVariables(iokitBundle, globals(), variables)
        # Move only the desired variables into iokit
        for var in variables:
            key = "{}".format(var[0])
            if key in globals():
                iokit[key] = globals()[key]

        iokit["kDisplayBrightness"] = CoreFoundation.CFSTR("brightness")
        iokit["kDisplayUnderscan"] = CoreFoundation.CFSTR("pscn")

    return iokit
