#!/usr/bin/python

# Display Manager, version 1.0.0
# Python Library

# Programmatically manages Mac displays.
# Can set screen resolution, refresh rate, rotation, brightness, underscan, and screen mirroring.

import abc              # Allows use of abstract classes
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


# todo: block/doc comments?
class AbstractDisplay(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, displayID):
        self.displayID = displayID

    # "Magic" methods

    def __lt__(self, other):
        return self.displayID < other.displayID

    def __gt__(self, other):
        return self.displayID > other.displayID

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.displayID == other.displayID
        else:
            return False

    def __hash__(self):
        # Actually just returns self.displayID, as self.displayID is int;
        # hash() is called for consistency and compatibility
        return hash(self.displayID)

    # General properties

    @abc.abstractproperty
    def isMain(self):
        pass

    @abc.abstractproperty
    def tag(self):
        pass

    # Mode properties and methods

    @abc.abstractproperty
    def currentMode(self):
        pass

    @abc.abstractmethod
    def allModes(self, hidpi):
        pass

    @abc.abstractmethod
    def highestMode(self, hidpi):
        pass

    @abc.abstractmethod
    def closestMode(self, width, height, refresh, hidpi):
        pass

    @abc.abstractmethod
    def setMode(self, mode):
        pass

    # Rotation properties and methods

    @abc.abstractproperty
    def rotation(self):
        pass

    @abc.abstractmethod
    def setRotate(self, angle):
        pass

    # Brightness

    @abc.abstractproperty
    def brightness(self):
        pass

    @abc.abstractmethod
    def setBrightness(self, brightness):
        pass

    # Underscan

    @abc.abstractproperty
    def underscan(self):
        pass

    @abc.abstractmethod
    def setUnderscan(self, underscan):
        pass

    # Mirroring

    @abc.abstractproperty
    def mirrorOf(self):
        pass

    @abc.abstractmethod
    def setMirrorOf(self, mirrorDisplay):
        pass


class Display(AbstractDisplay):
    """
    Virtual representation of a physical display.

    Contains properties regarding display information for a given physical display, along with a few
    useful helper functions to configure the display.
    """

    def __init__(self, displayID):
        """
        :param displayID: The DisplayID of the display to manipulate
        """
        # Sets self.displayID to displayID
        super(Display, self).__init__(displayID)

        # Make sure displayID is actually a display
        (error, allDisplayIDs, count) = Quartz.CGGetOnlineDisplayList(32, None, None)  # max 32 displays
        if displayID not in allDisplayIDs or error:
            raise DisplayError("Display {} not found".format(displayID))

        # iokit is required for several Display methods
        getIOKit()

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

    def allModes(self, hidpi=0):
        """
        :return: All possible Quartz "DisplayMode" interfaces for this display.
        """
        modes = []
        # options forces Quartz to show HiDPI modes
        options = {Quartz.kCGDisplayShowDuplicateLowResolutionModes: True}
        for modeRef in Quartz.CGDisplayCopyAllDisplayModes(self.displayID, options):
            mode = DisplayMode(modeRef)
            if self.__rightHidpi(mode, hidpi):
                modes.append(mode)
        return modes

    def highestMode(self, hidpi=0):
        """
        :param hidpi: HiDPI code. 0 returns everything, 1 returns only non-HiDPI, and 2 returns only HiDPI.
        :return: The Quartz "DisplayMode" interface with the highest display resolution for this display.
        """
        highest = None
        for mode in self.allModes():
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

    def closestMode(self, width, height, refresh=0, hidpi=0):
        """
        :param width: Desired width
        :param height: Desired height
        :param refresh: Desired refresh rate
        :param hidpi: HiDPI code. 0 returns everything, 1 returns only non-HiDPI, and 2 returns only HiDPI
        :return: The closest Quartz "DisplayMode" interface possible for this display.
        """
        # Which criteria does it match (in addition to width and height)?
        both = []           # matches HiDPI and refresh
        onlyHidpi = []      # matches HiDPI
        onlyRefresh = []    # matches refresh

        for mode in self.allModes():
            if mode.width == width and mode.height == height:
                if self.__rightHidpi(mode, hidpi) and mode.refresh == refresh:
                    both.append(mode)
                elif self.__rightHidpi(mode, hidpi):
                    onlyHidpi.append(mode)
                elif mode.refresh == refresh:
                    onlyRefresh.append(mode)

        # Return the nearest match, with HiDPI matches preferred over refresh matches
        for modes in [both, onlyHidpi, onlyRefresh]:
            if modes:
                return modes[0]

        raise DisplayError(
            "Display \"{}\" cannot be set to {}x{}".format(self.tag, width, height)
        )

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
            raise DisplayError("Cannot manage rotation on display \"{}\"".format(self.tag))

    # Brightness properties and methods

    @property
    def brightness(self):
        """
        :return: Brightness of this display, from 0 to 1.
        """
        service = self.__servicePort
        (error, brightness) = iokit["IODisplayGetFloatParameter"](service, 0, iokit["kDisplayBrightness"], None)
        if error:
            return None
        else:
            return brightness

    def setBrightness(self, brightness):
        """
        :param brightness: The desired brightness, from 0 to 1.
        """
        error = iokit["IODisplaySetFloatParameter"](self.__servicePort, 0, iokit["kDisplayBrightness"], brightness)
        if error:
            if self.isMain:
                raise DisplayError("Cannot manage brightness on display \"{}\"".format(self.tag))
            else:
                raise DisplayError(
                    "Display \"{}\"\'s brightness cannot be set.\n"
                    "External displays may not be compatible with Display Manager. "
                    "Try setting manually on device hardware.".format(self.tag))

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
            return None
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
            raise DisplayError("Cannot manage underscan on display \"{}\"".format(self.tag))

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


# todo: block/doc comments?
class AbstractDisplayMode(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, mode):
        self.raw = mode

    # "Magic" methods

    def __str__(self):
        return "resolution: {width}x{height}, refresh rate: {refresh}, HiDPI: {hidpi}".format(**{
            "width": self.width, "height": self.height, "refresh": self.refresh, "hidpi": self.hidpi
        })

    def __lt__(self, other):
        return self.width * self.height < other.width * other.height

    def __gt__(self, other):
        return self.width * self.height > other.width * other.height

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__str__() == other.__str__()
        else:
            return False

    def __hash__(self):
        return hash(self.__str__())

    # General properties

    @abc.abstractproperty
    def width(self):
        pass

    @abc.abstractproperty
    def height(self):
        pass

    @abc.abstractproperty
    def refresh(self):
        pass

    @abc.abstractproperty
    def hidpi(self):
        pass


class DisplayMode(AbstractDisplayMode):
    """
    Represents a DisplayMode as implemented in Quartz.
    """

    def __init__(self, mode):
        # sets self.raw to mode
        super(DisplayMode, self).__init__(mode)

        self.__width = int(Quartz.CGDisplayModeGetWidth(mode))
        self.__height = int(Quartz.CGDisplayModeGetHeight(mode))
        self.__refresh = int(Quartz.CGDisplayModeGetRefreshRate(mode))

        maxWidth = Quartz.CGDisplayModeGetPixelWidth(mode)  # the maximum display width for this display
        maxHeight = Quartz.CGDisplayModeGetPixelHeight(mode)  # the maximum display width for this display
        self.__hidpi = (maxWidth != self.width and maxHeight != self.height)  # if they're the same, mode is not HiDPI

    # General properties

    def width(self):
        return self.__width

    def height(self):
        return self.__height

    def refresh(self):
        return self.__refresh

    def hidpi(self):
        return self.__hidpi


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

        # A few IOKit variables that have been deprecated, but whose values
        # still work as intended in IOKit functions
        iokit["kDisplayBrightness"] = CoreFoundation.CFSTR("brightness")
        iokit["kDisplayUnderscan"] = CoreFoundation.CFSTR("pscn")

    return iokit
