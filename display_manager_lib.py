#!/usr/bin/python

# Display Manager, version 1.0.0

# Programmatically manages Mac displays.
# Can set screen resolution, color depth, refresh rate, screen mirroring, and brightness.

import sys              # exit script with the right codes
import collections      # for specialized containers
import objc             # access Objective-C functions and variables
import CoreFoundation   # work with Objective-C data types
import Quartz           # work with system graphics


# Configured for global usage; otherwise, must be re-instantiated each time it is called
iokit = None


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
            print("Display {} not found.".format(displayID))
            sys.exit(1)
        else:
            self.displayID = displayID

    def __eq__(self, display):
        return self.displayID == display.displayID

    @property
    def isMain(self):
        """
        :return: Boolean for whether this display is the main display
        """
        return Quartz.CGDisplayIsMain(self.displayID)

    @property
    def brightness(self):
        """
        :return: Brightness of this display, from 0 to 1.
        """
        service = self.servicePort
        (error, brightness) = iokit["IODisplayGetFloatParameter"](service, 0, iokit["kDisplayBrightness"], None)
        if error:
            return None
        else:
            return brightness

    @property
    def rotation(self):
        """
        :return: Rotation of this display, in degrees.
        """
        return int(Quartz.CGDisplayRotation(self.displayID))

    @property
    def underscan(self):
        """
        :return: Display's active underscan setting, from 1 (0%) to 0 (100%).
            (Yes, it doesn't really make sense to have 1 -> 0 and 0 -> 100, but it's how IOKit reports it.)
        """
        (error, underscan) = iokit["IODisplayGetFloatParameter"](self.servicePort, 0, iokit["kDisplayUnderscan"], None)
        if error:
            return None
        else:
            # IOKit handles underscan values as the opposite of what makes sense, so I switch it here.
            # e.g. 0 -> maximum (100%), 1 -> 0% (default)
            return float(abs(underscan - 1))

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

    @property
    def servicePort(self):
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

        return highest

    def exactMode(self, width, height, depth=32.0, refresh=0.0, hidpi=0):
        """
        :param width: Desired width
        :param height: Desired height
        :param depth: Desired pixel depth
        :param refresh: Desired refresh rate
        :param hidpi: HiDPI code. 0 returns everything, 1 returns only non-HiDPI, and 2 returns only HiDPI.
        :return: The Quartz "DisplayMode" interface matching the description, if it exists; otherwise, None.
        """
        for mode in self.allModes:
            if (
                    mode.width == width and mode.height == height and mode.depth == depth and
                    mode.refresh == refresh and self.__rightHidpi(mode, hidpi)
            ):
                return mode
        return None

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

    def setMode(self, mode):
        """
        :param mode: The Quartz "DisplayMode" interface to set this display to.
        """
        (error, configRef) = Quartz.CGBeginDisplayConfiguration(None)
        if error:
            print("Could not begin display configuration: error {}".format(error))
            sys.exit(1)

        error = Quartz.CGConfigureDisplayWithDisplayMode(configRef, self.displayID, mode.raw, None)
        if error:
            print("Failed to set display configuration: error {}".format(error))
            Quartz.CGCancelDisplayConfiguration(configRef)
            sys.exit(1)

        Quartz.CGCompleteDisplayConfiguration(configRef, Quartz.kCGConfigurePermanently)

    def setBrightness(self, brightness):
        """
        :param brightness: The desired brightness, from 0 to 1.
        """
        error = iokit["IODisplaySetFloatParameter"](self.servicePort, 0, iokit["kDisplayBrightness"], brightness)
        if error:
            print("Failed to set brightness of display {}; error {}".format(self.displayID, error))
            # External display brightness probably can't be managed this way
            print("External displays may not be compatible with Display Manager. \n"
                  "If this is an external display, try setting manually on device hardware.")

    def setRotate(self, angle):
        """
        :param angle: The angle of rotation.
        """
        angleCodes = {0: 0, 90: 48, 180: 96, 270: 80}
        rotateCode = 1024
        if angle % 90 != 0:  # user entered inappropriate angle, so we quit
            print("Can only rotate by multiples of 90 degrees.")
            sys.exit(1)
        # "or" the rotate code with the right angle code (which is being moved to the right part of the 32-bit word)
        options = rotateCode | (angleCodes[angle % 360] << 16)

        # Actually rotate the screen
        error = iokit["IOServiceRequestProbe"](self.servicePort, options)

        if error:
            print("Failed to rotate display {}; error {}".format(self.displayID, error))
            sys.exit(1)

    def setUnderscan(self, underscan):
        """
        :param underscan: Underscan value, from 0 (no underscan) to 1 (maximum underscan).
        """
        # IOKit handles underscan values as the opposite of what makes sense, so I switch it here.
        # e.g. 0 -> maximum (100%), 1 -> 0% (default)
        underscan = float(abs(underscan - 1))

        error = iokit["IODisplaySetFloatParameter"](self.servicePort, 0, iokit["kDisplayUnderscan"], underscan)
        if error:
            print("Failed to set underscan of display {}; error {}".format(self.displayID, error))

    def setMirrorOf(self, mirrorDisplay):
        """
        :param mirrorDisplay: The Display which this Display will mirror.
            Input a NoneType to stop mirroring.
        """
        (error, configRef) = Quartz.CGBeginDisplayConfiguration(None)
        if error:
            print("Could not begin display configuration: error {}".format(error))
            sys.exit(1)

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
        self.width = Quartz.CGDisplayModeGetWidth(mode)
        self.height = Quartz.CGDisplayModeGetHeight(mode)
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
        return "resolution: {width}x{height}, pixel depth: {depth}, refresh rate: {refresh}, HiDPI: {hidpi}".format(**{
            "width": self.width, "height": self.height, "depth": self.depth,
            "refresh": self.refresh, "hidpi": self.hidpi
        })

    def __lt__(self, otherDM):
        return self.width * self.height < otherDM.width * otherDM.height

    def __gt__(self, otherDM):
        return self.width * self.height > otherDM.width * otherDM.height

    def __eq__(self, otherDM):
        return self.width * self.height == otherDM.width * otherDM.height


class Command(object):
    """
    Represents a user-requested command to Display Manager.
    """

    def __init__(self, primary, secondary, width=None, height=None, depth=None, refresh=None,
                 displayID=None, hidpi=None, brightness=None, angle=None, underscan=None,
                 mirrorDisplayID=None):
        getIOKit()

        if primary in ["set", "show", "brightness", "rotate", "underscan", "mirror"]:
            self.primary = primary
        else:
            print("Unrecognized command {}".format(primary))
            sys.exit(1)
        self.secondary = secondary

        self.width = int(width) if width is not None else None
        self.height = int(height) if height is not None else None
        self.depth = float(depth) if depth is not None else None
        self.refresh = float(refresh) if refresh is not None else None
        self.displayID = int(displayID) if displayID is not None else None
        self.hidpi = int(hidpi) if hidpi is not None else None
        self.brightness = float(brightness) if brightness is not None else None
        self.angle = int(angle) if angle is not None else None
        self.underscan = float(underscan) if underscan is not None else None
        self.mirrorDisplayID = int(mirrorDisplayID) if mirrorDisplayID is not None else None

    def __str__(self):
        """
        :return: A string which would result in this command via the command line
        """
        stringList = []

        for positional in [self.primary, self.secondary, self.brightness, self.angle, self.underscan]:
            if positional is not None:
                stringList.append(str(positional))

        if self.width is not None:
            stringList.append("-w " + str(self.width))
        if self.height is not None:
            stringList.append("-h " + str(self.height))
        if self.depth is not None:
            stringList.append("-p " + str(self.depth))
        if self.refresh is not None:
            stringList.append("-r " + str(self.refresh))
        if self.displayID is not None:
            stringList.append("-d " + str(self.displayID))
        if self.mirrorDisplayID is not None:
            stringList.append("-m " + str(self.mirrorDisplayID))

        if self.hidpi == 1:  # do not show HiDPI modes
            stringList.append("--no-hidpi")
        elif self.hidpi == 2:  # only show HiDPI modes
            stringList.append("--only-hidpi")

        return " ".join(stringList)

    def run(self):
        """
        Runs the command this Command has stored.
        """
        if self.primary == "set":
            self.__handleSet()
        elif self.primary == "show":
            self.__handleShow()
        elif self.primary == "brightness":
            self.__handleBrightness()
        elif self.primary == "rotate":
            self.__handleRotate()
        elif self.primary == "underscan":
            self.__handleUnderscan()
        elif self.primary == "mirror":
            self.__handleMirror()

    def __printNotFound(self):
        print("No matching display mode was found. {}".format(
            "Try removing HiDPI flags to find a mode." if self.hidpi != 0 else ""))

    def __handleSet(self):
        """
        Sets the display to the correct DisplayMode.
        """
        display = Display(self.displayID)

        if self.secondary == "closest":
            if self.width is None or self.height is None:
                print("Must have both width and height for closest setting.")
                sys.exit(1)

            closest = display.closestMode(self.width, self.height, self.depth, self.refresh)
            if closest:
                display.setMode(closest)
            else:
                self.__printNotFound()
                sys.exit(1)

        elif self.secondary == "highest":
            highest = display.highestMode(self.hidpi)
            if highest:
                display.setMode(highest)
            else:
                self.__printNotFound()
                sys.exit(1)

        elif self.secondary == "exact":
            exact = display.exactMode(self.width, self.height, self.depth, self.refresh, self.hidpi)
            if exact:
                display.setMode(exact)
            else:
                self.__printNotFound()
                sys.exit(1)

    def __handleShow(self):
        """
        Shows the user information about connected displays.
        """
        if self.secondary == "all":
            for display in getAllDisplays():
                print("Display: {0} {1}".format(str(display.displayID), " (Main Display)" if display.isMain else ""))

                foundMatching = False  # whether we ended up printing a matching mode or not
                for mode in sorted(display.allModes, reverse=True):
                    print("    {}".format(mode))
                    foundMatching = True

                if not foundMatching:
                    self.__printNotFound()

        elif self.secondary == "closest":
            if self.width is None or self.height is None:
                print("Must have both width and height for closest matching.")
                sys.exit(1)

            display = Display(self.displayID)
            closest = display.closestMode(self.width, self.height, self.depth, self.refresh)
            if closest:
                print("{}".format(closest))
            else:
                self.__printNotFound()

        elif self.secondary == "highest":
            display = Display(self.displayID)
            highest = display.highestMode(self.hidpi)
            if highest:
                print("{}".format(highest))
            else:
                self.__printNotFound()

        elif self.secondary == "current":
            display = Display(self.displayID)
            print("Display: {0} {1}".format(str(display.displayID), " (Main Display)" if display.isMain else ""))

            current = display.currentMode
            if current:
                print("{}".format(current))
            else:
                self.__printNotFound()

        elif self.secondary == "displays":
            for display in getAllDisplays():
                print("Display: {0} {1}".format(str(display.displayID), " (Main Display)" if display.isMain else ""))

    def __handleBrightness(self):
        """
        Sets or shows a display's brightness.
        """
        if self.secondary == "show":
            for display in getAllDisplays():
                if display.brightness:
                    print("Display: {}{}".format(display.displayID, " (Main Display)" if display.isMain else ""))
                    print("    {:.2f}%".format(display.brightness * 100))
                else:
                    print("Failed to get brightness of display {}".format(display.displayID))

        elif self.secondary == "set":
            display = Display(self.displayID)
            display.setBrightness(self.brightness)

    def __handleRotate(self):
        """
        Sets or shows a display's rotation.
        """
        if self.secondary == "show":
            for display in getAllDisplays():
                print(
                    "Display: {0} {1}".format(str(display.displayID), " (Main Display)" if display.isMain else ""))
                print("    Rotation: {0} degrees".format(str(int(display.rotation))))

        elif self.secondary == "set":
            display = Display(self.displayID)
            display.setRotate(self.angle)

    def __handleUnderscan(self):
        """
        Sets or shows a display's underscan settings.
        """
        if self.secondary == "show":
            for display in getAllDisplays():
                if display.underscan is not None:
                    print("Display: {}{}".format(display.displayID, " (Main Display)" if display.isMain else ""))
                    print("    {:.2f}%".format(self.underscan * 100))
                else:
                    print("Failed to get underscan value of display {}".format(display.displayID))

        elif self.secondary == "set":
            display = Display(self.displayID)
            display.setUnderscan(self.underscan)

    def __handleMirror(self):
        """
        Enables or disables mirroring between two displays.
        """
        if self.secondary == "set":
            display = Display(self.displayID)
            mirrorDisplay = Display(self.mirrorDisplayID)

            display.setMirrorOf(mirrorDisplay)

        if self.secondary == "disable":
            for display in getAllDisplays():
                # If display is a mirror of another display, disable mirroring between them
                if display.mirrorOf is not None:
                    display.setMirrorOf(None)


class CommandList(object):
    """
    Holds one or more "Command" instances.
    """

    def __init__(self):
        # self.commandDict will consist of displayID keys corresponding to commands for that display
        self.__commandDict = {}

    @property
    def commands(self):
        """
        :return: All the Commands in this CommandList
        """
        commands = []
        for displayID in self.__commandDict:
            for command in self.__commandDict[displayID]:
                commands.append(command)

        return commands

    def addCommand(self, command):
        """
        :param command: The Command to add to this CommandList
        """
        displayID = command.displayID
        if displayID is None:
            displayID = getMainDisplay().displayID

        if displayID in self.__commandDict:
            self.__commandDict[displayID].append(command)
        else:
            self.__commandDict[displayID] = [command]

    def run(self):
        """
        Runs all stored Commands in a non-interfering fashion
        """
        for displayID in self.__commandDict:
            # Commands for this particular display
            displayCommands = self.__commandDict[displayID]

            # Group commands by type. Must preserve ordering to avoid interfering commands
            commandGroups = collections.OrderedDict([
                ("set", []),
                ("mirror", []),
                ("rotate", []),
                ("underscan", []),
                ("brightness", []),
                ("show", []),
            ])
            for command in displayCommands:
                if command.primary in commandGroups:
                    commandGroups[command.primary].append(command)
                else:
                    print("Unexpected command.primary \"{}\"".format(command.primary))
                    sys.exit(1)

            # Run commands by type
            for commandType in commandGroups:
                # Commands for this display, of this type
                commands = commandGroups[commandType]

                if len(commands) > 0:
                    # Multiple commands of these types will undo each other.
                    # As such, just run the most recently added command (the last in the list)
                    if (
                            commandType == "set" or
                            commandType == "brightness" or
                            commandType == "rotate" or
                            commandType == "underscan"
                    ):
                        commands[-1].run()

                    # "show" commands don't interfere with each other, so run all of them
                    elif commandType == "show":
                        for command in commands:
                            command.run()

                    # "mirror" commands are the most complicated to deal with
                    elif commandType == "mirror":
                        command = commands[-1]

                        if command.secondary == "set":
                            display = Display(displayID)
                            # The current Display that the above "display" is mirroring
                            currentMirror = display.mirrorOf
                            # Become a mirror of most recently requested display
                            mirrorDisplay = Display(command.mirrorDisplayID)

                            # If display is not a mirror of any other display
                            if currentMirror is None:
                                display.setMirrorOf(mirrorDisplay)

                            # The user requested that this display mirror itself, or that it mirror a display
                            # which it is already mirroring. In either case, nothing should be done
                            elif display == currentMirror or currentMirror == mirrorDisplay:
                                pass

                            # display is already a mirror, but not of the requested display
                            else:
                                # First disable mirroring, then enable it for new mirror
                                display.setMirrorOf(None)
                                display.setMirrorOf(mirrorDisplay)

                        elif command.secondary == "disable":
                            command.run()


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
        print("Unable to get displays list.")
        sys.exit(1)

    displays = []
    for displayID in displayIDs:
        displays.append(Display(displayID))
    return displays


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
            ("IOIteratorNext", b"II")
        ]

        # The IOKit variables to be retrieved
        variables = [
            ("kIODisplayNoProductName", b"I"),
            ("kIOMasterPortDefault", b"I"),
            ("kIODisplayBrightnessKey", b"*"),
            ("kIODisplayOverscanKey", b"*"),
            ("kDisplayVendorID", b"*"),
            ("kDisplayProductID", b"*"),
            ("kDisplaySerialNumber", b"*")
        ]

        # Load functions from IOKit into the global namespace
        objc.loadBundleFunctions(iokitBundle, iokit, functions)
        # Bridge won't put straight into iokit, so globals()
        objc.loadBundleVariables(iokitBundle, globals(), variables)
        # Move only the desired variables into iokit
        for var in variables:
            key = "{}".format(var[0])
            if key in globals():
                iokit[key] = globals()[key]

        iokit["kDisplayBrightness"] = CoreFoundation.CFSTR(iokit["kIODisplayBrightnessKey"])
        iokit["kDisplayUnderscan"] = CoreFoundation.CFSTR("pscn")

    return iokit
