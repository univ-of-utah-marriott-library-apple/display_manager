#!/usr/bin/python

# Display Manager, version 1.0.0

# Programmatically manages Mac displays.
# Can set screen resolution, color depth, refresh rate, screen mirroring, and brightness.


import argparse         # read in command-line execution
import objc             # access Objective-C functions and variables
import sys              # exit script with the right codes
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
        if displayID in getAllDisplayIDs():
            self.displayID = displayID
        else:
            print("Display {} not found.".format(displayID))
            sys.exit(1)

    @property
    def isMain(self):
        """
        :return: Boolean for whether this display is the run display
        """
        return Quartz.CGDisplayIsMain(self.displayID)

    @property
    def rotation(self):
        """
        :return: Rotation of this display, in degrees.
        """
        return int(Quartz.CGDisplayRotation(self.displayID))

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

    @staticmethod
    def rightHidpi(mode, hidpi):
        """
        Evaluates whether the mode fits the user's HiDPI specification.

        :param mode: The mode to be evaluated.
        :param hidpi: The desired HiDPI description.
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

    @property
    def currentMode(self):
        """
        :return: The current Quartz "DisplayMode" interface for this display.
        """
        return DisplayMode(Quartz.CGDisplayCopyDisplayMode(self.displayID))

    @property
    def allModes(self, hidpi=0):
        """
        :return: All possible Quartz "DisplayMode" interfaces for this display.
        """
        modes = []
        # options forces Quartz to show HiDPI modes
        options = {Quartz.kCGDisplayShowDuplicateLowResolutionModes: True}
        for mode in Quartz.CGDisplayCopyAllDisplayModes(self.displayID, options):
            if self.rightHidpi(mode, hidpi):
                modes.append(DisplayMode(mode))
        return modes

    def highestMode(self, hidpi=0):
        """
        :return: The Quartz "DisplayMode" interface with the highest display resolution for this display.
        """
        highest = None
        for mode in self.allModes:
            if highest:
                if mode > highest and self.rightHidpi(mode, hidpi):
                    highest = mode
            else:
                highest = mode

        return highest

    @property
    def servicePort(self):
        """
        :return: The integer representing this display's service port.
        """
        return Quartz.CGDisplayIOServicePort(self.displayID)

    def exactMode(self, width, height, depth=32, refresh=0, hidpi=0):
        """
        :param width: Desired width
        :param height: Desired height
        :param depth: Desired pixel depth
        :param refresh: Desired refresh rate
        :return: The Quartz "DisplayMode" interface matching the description, if it exists; otherwise, None.
        """
        for mode in self.allModes:
            if (
                    mode.width == width and mode.height == height and mode.depth == depth and
                    mode.refresh == refresh and self.rightHidpi(mode, hidpi)
            ):
                return mode
        return None

    def closestMode(self, width, height, depth=32, refresh=0, hidpi=0):
        """
        :param width: Desired width
        :param height: Desired height
        :param depth: Desired pixel depth
        :param refresh: Desired refresh rate
        :return: The closest Quartz "DisplayMode" interface possible for this display.
        """
        whdr = None
        whd = None
        wh = None

        for mode in self.allModes:
            widthMatch = mode.width == width
            heightMatch = mode.height == height
            depthMatch = mode.depth == depth
            refreshMatch = mode.refresh == refresh
            hidpiMatch = self.rightHidpi(mode, hidpi)

            # todo: look into more cases (e.g. right ratio, wrong width & height)
            if widthMatch and heightMatch and depthMatch and refreshMatch and hidpiMatch:
                return mode
            elif widthMatch and heightMatch and depthMatch and refreshMatch:
                whdr = mode
            elif widthMatch and heightMatch and depthMatch:
                whd = mode
            elif widthMatch and heightMatch:
                wh = mode

        for match in [whdr, whd, wh]:
            if match:
                return match

        # todo: remove deprecated
        # if whdr:
        #     return whdr
        # elif whd:
        #     return whd
        # elif wh:
        #     return wh
        # else:
        #     return None

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
            error = Quartz.CGCancelDisplayConfiguration(configRef)
            sys.exit(1)

        Quartz.CGCompleteDisplayConfiguration(configRef, Quartz.kCGConfigurePermanently)

    def setMirror(self, mirrorDisplay):
        """
        :param mirrorDisplay: The display which will mirror this display.
            Input a NoneType to stop mirroring.
        """
        (error, configRef) = Quartz.CGBeginDisplayConfiguration(None)
        if error:
            print("Could not begin display configuration: error {}".format(error))
            sys.exit(1)

        if mirrorDisplay is not None and mirrorDisplay.displayID != self.displayID:
            Quartz.CGConfigureDisplayMirrorOfDisplay(configRef, self.displayID, mirrorDisplay.displayID)
        else:
            Quartz.CGConfigureDisplayMirrorOfDisplay(configRef, self.displayID, Quartz.kCGNullDirectDisplay)

        Quartz.CGCompleteDisplayConfiguration(configRef, Quartz.kCGConfigurePermanently)


class DisplayMode(object):
    """
    Represents a DisplayMode as implemented in Quartz.
    """

    def __init__(self, mode):
        # Low-hanging fruit
        self.width = Quartz.CGDisplayModeGetWidth(mode)
        self.height = Quartz.CGDisplayModeGetHeight(mode)
        self.refresh = Quartz.CGDisplayModeGetRefreshRate(mode)
        self.raw = mode

        # Pixel depth
        temp = {"PPPPPPPP": 8, "-RRRRRGGGGGBBBBB": 16,
                "--------RRRRRRRRGGGGGGGGBBBBBBBB": 32, "--RRRRRRRRRRGGGGGGGGGGBBBBBBBBBB": 30}
        self.depth = temp[Quartz.CGDisplayModeCopyPixelEncoding(mode)]

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

    def __init__(self, primary, secondary, width=None, height=None, depth=32, refresh=0,
                 displayID=None, hidpi=0, brightness=1, angle=0, underscan=1,
                 mirrorDisplayID=None):
        # Required for all types of commands
        if primary in ["set", "show", "brightness", "rotate", "underscan", "mirroring"]:
            self.primary = primary
        else:
            print("Unrecognized command {}".format(primary))
            sys.exit(1)
        self.secondary = secondary

        # Command-specific data
        if width:
            self.width = int(width)
        else:
            self.width = None
        if height:
            self.height = int(height)
        else:
            self.height = None
        self.depth = int(depth)
        self.refresh = int(refresh)
        self.hidpi = int(hidpi)
        self.brightness = int(brightness)
        self.angle = int(angle)
        self.underscan = int(underscan)
        if mirrorDisplayID:
            self.mirrorDisplayID = int(mirrorDisplayID)
        else:
            self.mirrorDisplayID = None

        # Need this conditional block because Python doesn't recognize getMainDisplay() in __init__ declaration
        if displayID:
            self.displayID = int(displayID)
        else:
            self.displayID = getMainDisplayID()

    def run(self):
        """
        Runs whichever command this Command has stored.
        """
        if self.primary == "set":
            handleSet(self.secondary, self.width, self.height, self.depth, self.refresh,
                      self.displayID, self.hidpi)
        elif self.primary == "show":
            handleShow(self.secondary, self.width, self.height, self.depth, self.refresh,
                       self.displayID, self.hidpi)
        elif self.primary == "brightness":
            handleBrightness(self.secondary, self.brightness, self.displayID)
        elif self.primary == "rotate":
            handleRotate(self.secondary, self.angle, self.displayID)
        elif self.primary == "underscan":
            handleUnderscan(self.secondary, self.underscan, self.displayID)
        elif self.primary == "mirroring":
            handleBrightness(self.secondary, self.displayID, self.mirrorDisplayID)


class CommandList(object):
    """
    Holds one or more "Command" instances.
    """

    def __init__(self, commands=None):
        self.commandDict = {"set": [], "show": [], "brightness": [], "rotate": [], "underscan": [], "mirroring": []}
        if commands:
            self.addCommands(commands)

    def addCommands(self, commands):
        """
        Adds Command(s) to the list.
        :param commands: The Command(s) to add.
        """
        if type(commands) == Command:
            self.commandDict[commands.primary].append(commands)
        elif type(commands) == CommandList:
            for commandKey in commands.commandDict:
                self.commandDict[commandKey] = commands.commandDict[commandKey]

    def run(self):
        """
        Run all the Commands stored. Grouped by type for safety and efficiency.
        """
        for command in self.commandDict["set"]:
            command.run()
        for command in self.commandDict["show"]:
            command.run()
        for command in self.commandDict["brightness"]:
            command.run()
        for command in self.commandDict["rotate"]:
            command.run()
        for command in self.commandDict["underscan"]:
            command.run()
        for command in self.commandDict["mirroring"]:
            command.run()


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


def getAllDisplays():
    """
    :return: A list containing all currently-online displays.
    """
    displays = []
    for displayID in getAllDisplayIDs():
        displays.append(Display(displayID))
    return displays


def getMainDisplayID():
    """
    :return: DisplayID of the run display
    """
    return Quartz.CGMainDisplayID()


def getAllDisplayIDs():
    """
    :return: A tuple containing all currently-online displays.
        Each object in the tuple is a display identifier (as an integer).
    """
    (error, displays, count) = Quartz.CGGetOnlineDisplayList(32, None, None)  # max 32 displays
    if error:
        raise RuntimeError("Unable to get displays list.")
    return displays


def handleSet(command, width, height, depth, refresh, displayID, hidpi=0):
    """
    Handles all of the options for the "set" subcommand.

    :param command: The command passed in.
    :param width: Desired width.
    :param height: Desired height.
    :param depth: Desired pixel depth.
    :param refresh: Desired refresh rate.
    :param displayID: Specific display to configure.
    :param hidpi: HiDPI settings.
    """
    display = Display(displayID)

    def printNotFound():
        print("    No matching display mode was found. {}".format(
            "Try removing HiDPI flags to find a mode." if hidpi != 0 else ""))

    if command == "closest":
        if width is None or height is None:
            showHelp("set")
            print("Must have both width and height for closest setting.")
            sys.exit(1)

        closest = display.closestMode(width, height, depth, refresh)
        if closest:
            display.setMode(closest)
        else:
            printNotFound()
            sys.exit(1)

    elif command == "highest":
        highest = display.highestMode(hidpi)
        if highest:
            display.setMode(highest)
        else:
            printNotFound()
            sys.exit(1)

    elif command == "exact":
        exact = display.exactMode(width, height, depth, refresh, hidpi)
        if exact:
            display.setMode(exact)
        else:
            printNotFound()
            sys.exit(1)


def handleShow(command, width, height, depth, refresh, displayID, hidpi=0):
    """
    Handles all the options for the "show" subcommand.

    :param command: The command passed in.
    :param width: Desired width.
    :param height: Desired height.
    :param depth: Desired pixel depth.
    :param refresh: Desired refresh rate.
    :param displayID: Specific display to configure.
    :param hidpi: HiDPI settings.
    """
    display = Display(displayID)

    def printNotFound():
        print("    No matching display mode was found. {}".format(
            "Try removing HiDPI flags to find a mode." if hidpi != 0 else ""))

    if command == "all":
        for display in getAllDisplays():
            print("Display: {0} {1}".format(str(display.displayID), " (Main Display)" if display.isMain else ""))

            foundMatching = False  # whether we ended up printing a matching mode or not
            for mode in sorted(display.allModes, reverse=True):
                print("    {}".format(mode))
                foundMatching = True

            if not foundMatching:
                printNotFound()

    elif command == "closest":
        if width is None or height is None:
            showHelp("show")
            print("Must have both width and height for closest matching.")
            sys.exit(1)

        closest = display.closestMode(width, height, depth, refresh)
        if closest:
            print("    {}".format(closest))
        else:
            printNotFound()

    elif command == "highest":
        highest = display.highestMode(hidpi)
        if highest:
            print("    {}".format(highest))
        else:
            printNotFound()

    elif command == "current":
        for display in getAllDisplays():
            print("Display: {0} {1}".format(str(display.displayID), " (Main Display)" if display.isMain else ""))

            current = display.currentMode
            if current:
                print("    {}".format(current))
            else:
                printNotFound()

    elif command == "displays":
        for display in getAllDisplays():
            print("Display: {0} {1}".format(str(display.displayID), " (Main Display)" if display.isMain else ""))


def handleBrightness(command, brightness, displayID):
    """
    Handles all the options for the "brightness" subcommand.

    :param command: The command passed in.
    :param brightness: The level of brightness to change to.
    :param displayID: Specific display to configure.
    """
    display = Display(displayID)

    if command == "show":
        for display in getAllDisplays():
            if display.brightness:
                print("Display: {}{}".format(displayID, " (Main Display)" if display.isMain else ""))
                print("    {:.2f}%".format(display.brightness * 100))
            else:
                print("Failed to get brightness of display {}".format(display.displayID))

    elif command == "set":
        error = iokit["IODisplaySetFloatParameter"](display.servicePort, 0, iokit["kDisplayBrightness"], brightness)
        if error:
            print("Failed to set brightness of display {}; error {}".format(display.displayID, error))
            # External display brightness probably can't be managed this way
            print("External displays may not be compatible with Display Manager. \n"
                  "If this is an external display, try setting manually on device hardware.")


def handleRotate(command, angle, displayID):
    """
    Handles all the options for the "rotation" subcommand.

    :param command: The command passed in.
    :param angle: The display to configure rotation on.
    :param displayID: The display to configure rotation on.
    """
    display = Display(displayID)

    if command == "show":
        for display in getAllDisplays():
            print("Display: {0} {1}".format(str(display.displayID), " (Main Display)" if display.isMain else ""))
            print("    Rotation: {0} degrees".format(str(int(display.rotation))))

    elif command == "set":
        # Get rotation "options", per user input
        angleCodes = {0: 0, 90: 48, 180: 96, 270: 80}
        rotateCode = 1024
        if angle % 90 != 0:  # user entered inappropriate angle, so we quit
            print("Can only rotate by multiples of 90 degrees.")
            sys.exit(1)
        # "or" the rotate code with the right angle code (which is being moved to the right part of the 32-bit word)
        options = rotateCode | (angleCodes[angle % 360] << 16)

        # Actually rotate the screen
        iokit["IOServiceRequestProbe"](display.servicePort, options)


def handleUnderscan(command, underscan, displayID):
    """
    Handles all the options for the "underscan" subcommand.

    :param command: The command passed in.
    :param underscan: The value to set on the underscan slider.
    :param displayID: Specific display to configure.
    """
    display = Display(displayID)

    if command == "show":
        for display in getAllDisplays():
            (error, underscan) = iokit["IODisplayGetFloatParameter"](
                display.servicePort, 0, iokit["kDisplayUnderscan"], None)
            if error:
                print("Failed to get underscan value of display {}; error {}".format(display.displayID, error))
                continue
            print("Display: {}{}".format(display.displayID, " (Main Display)" if display.isMain else ""))
            print("    {:.2f}%".format(underscan * 100))

    elif command == "set":
        error = iokit["IODisplaySetFloatParameter"](display.servicePort, 0, iokit["kDisplayUnderscan"], underscan)
        if error:
            print("Failed to set underscan of display {}; error {}".format(display.displayID, error))
        print("Display: {}{}".format(displayID, " (Main Display)" if display.isMain else ""))
        print("    {:.2f}%".format(underscan * 100))


def handleMirroring(command, displayID, mirrorDisplayID):
    """
    Handles all the options for the "mirroring" subcommand.

    :param command: The command passed in.
    :param displayID: The display to configure mirroring on.
    :param mirrorDisplayID: The display to become a mirror of.
    """
    mirrorDisplay = Display(mirrorDisplayID)
    display = Display(displayID)

    if command == "enable":
        mirrorDisplay.setMirror(display)

    if command == "disable":
        for display in getAllDisplays():
            display.setMirror(None)


def showHelp(command=None):
    """
    Prints out the help information.

    :param command: The subcommand to print information for.
    """
    # Give the version information always.
    print("Display Manager, version 1.0.0")

    information = {}

    information['set'] = '\n'.join([
        "usage: display_manager.py set {{ help | closest | highest | exact }}",
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
        "    --display display   Specify a particular display (default: run display).",
        "    --no-hidpi          Don't show HiDPI settings.",
        "    --only-hidpi        Only show HiDPI settings.",
        "",
    ])

    information['show'] = '\n'.join([
        "usage: display_manager.py show {{ help | all | closest | highest | current }}",
        "    [-w width] [-h height] [-d depth] [-r refresh]",
        "    [--display display] [--nohidpi]",
        "",
        "SUBCOMMANDS",
        "    help        Print this help information.",
        "    all         Show all supported resolutions for the display.",
        "    closest     Show the closest matching supported resolution to the specified",
        "                values.",
        "    highest     Show the highest supported resolution.",
        "    current     Show the current display configuration.",
        "    displays    Just list the current displays and their IDs.",
        "",
        "OPTIONS",
        "    -w width            Resolution width.",
        "    -h height           Resolution height.",
        "    -d depth            Pixel color depth (default: 32).",
        "    -r refresh          Refresh rate (default: 32).",
        "    --display display   Specify a particular display (default: run display).",
        "    --no-hidpi          Don't show HiDPI settings.",
        "    --only-hidpi        Only show HiDPI settings.",
        "",
    ])

    information['brightness'] = '\n'.join([
        "usage: display_manager.py brightness {{ help | show | set [value] }}",
        "    [--display display]",
        "",
        "SUBCOMMANDS",
        "    help        Print this help information.",
        "    show        Show the current brightness setting(s).",
        "    set [value] Sets the brightness to the given value. Must be between 0 and 1.",
        "",
        "OPTIONS",
        "    --display display   Specify a particular display (default: run display).",
        "",
    ])

    information['rotate'] = '\n'.join([
        "usage: display_manager.py rotate {{ help | show | set }}"
        "    [--display display]",
        "SUBCOMMANDS",
        "    help        Print this help information.",
        "    show        Show the current display rotation.",
        "    set [value] Set the rotation to the given value (in degrees). Must be a multiple of 90.",
        "",
        "OPTIONS",
        "    --display display   Specify a particular display (default: run display).",
        ""
    ])

    information['underscan'] = '\n'.join([
        "usage: display_manager.py underscan {{ help | show | set [value] }}",
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
    ])

    information['mirroring'] = '\n'.join([
        "usage: display_manager.py brightness {{ help | enable | disable }}",
        "    [--diplay display] [--mirror display]",
        "",
        "SUBCOMMANDS",
        "    help        Print this help information.",
        "    enable      Activate mirroring.",
        "    disable     Deactivate all mirroring.",
        "",
        "OPTIONS",
        "    --display display               Change mirroring settings for 'display'.",
        "    --mirror display                Set the display to mirror 'display' (default: run display).",
        "",
    ])

    if command in information:
        print(information[command])
    else:
        print('\n'.join([
            "usage: display_manager.py {{ help | set | show | mirroring | brightness | rotate }}",
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
        ]))


def run(commands):
    """
    Called to execute commands.
    :param commands: What commands have been requested?
    """
    getIOKit()

    if commands:
        runCommands = CommandList(commands)
        runCommands.run()
