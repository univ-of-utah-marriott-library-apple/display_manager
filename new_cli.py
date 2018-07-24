#!/usr/bin/python

# This script allows users to access Display Manager through the command line.

import collections
import re
from display_manager_lib import *


class CommandSyntaxError(Exception):
    """
    Raised if commands have improper syntax (e.g.
    """
    pass


class CommandValueError(Exception):
    """
    Raised if commands have improper values
    """
    pass


class Command(object):
    """
    Represents a user-requested command to Display Manager.
    """

    # todo: remove deprecated
    # def __init__(self, verb, secondary=None, displayTags=None, width=None, height=None, refresh=None, hidpi=None,
    #              brightness=None, angle=None, underscan=None, mirrorTargetTags=None):
    #     getIOKit()
    #
    #     if verb in ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]:
    #         self.primary = verb
    #     else:
    #         print("Unrecognized command {}".format(verb))
    #         sys.exit(1)
    #     self.secondary = secondary
    #
    #     if displayTags is not None:
    #         self.displays = []
    #         for displayTag in displayTags:
    #             self.displays.append(self.__getDisplayFromTag(displayTag))
    #     else:
    #         self.displays = None
    #
    #     if mirrorTargetTags is not None:
    #         self.mirrors = []
    #         for displayTag in mirrorTargetTags:
    #             self.mirrors.append(self.__getDisplayFromTag(displayTag))
    #     else:
    #         self.mirrors = None
    #
    #     self.width = int(width) if width is not None else None
    #     self.height = int(height) if height is not None else None
    #     self.refresh = float(refresh) if refresh is not None else None
    #     self.hidpi = int(hidpi) if hidpi is not None else None
    #     self.brightness = float(brightness) if brightness is not None else None
    #     self.angle = int(angle) if angle is not None else None
    #     self.underscan = float(underscan) if underscan is not None else None

    def __init__(self, verb, scope, **kwargs):
        # Determine verb
        if verb in ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]:
            self.verb = verb
        else:
            print("Unrecognized command \"{}\".".format(verb))
            sys.exit(1)

        # Determine type, scope
        self.type = kwargs["type"] if "type" in kwargs else None
        self.scope = scope

        # Determine values, options
        self.width = int(kwargs["width"]) if "width" in kwargs else None
        self.height = int(kwargs["height"]) if "height" in kwargs else None
        self.refresh = float(kwargs["refresh"]) if "refresh" in kwargs else None
        self.hidpi = int(kwargs["hidpi"]) if "hidpi" in kwargs else None
        self.brightness = float(kwargs["brightness"]) if "brightness" in kwargs else None
        self.angle = int(kwargs["angle"]) if "angle" in kwargs else None
        self.underscan = float(kwargs["underscan"]) if "underscan" in kwargs else None
        self.source = kwargs["mirror"] if "mirror" in kwargs else None

        # Make sure IOKit is ready for use in any/all commands
        getIOKit()

    def __str__(self):
        """
        :return: A string which would result in this command via the command line
        """
        # A list to contain strings of all the arguments in the command
        stringList = [self.verb]

        if self.type:
            stringList.append(self.type)

        # Determine value

        if self.verb == "res":
            if self.width and self.height:  # can also be set by type=highest
                stringList.append(self.width)
                stringList.append(self.height)

        elif self.verb == "brightness":
            stringList.append(self.brightness)
        elif self.verb == "rotate":
            stringList.append(self.angle)
        elif self.verb == "underscan":
            stringList.append(self.underscan)
        elif self.verb == "mirror":
            stringList.append(self.source)

        # Determine options

        if self.verb == "show" or self.verb == "res":
            if self.hidpi == 1:
                stringList.append("no-hidpi")
            elif self.hidpi == 2:
                stringList.append("only-hidpi")

        if self.verb == "res":
            if self.refresh:
                stringList.append("refresh {}".format(self.refresh))

        # Determine scope

        if self.scope:
            for display in self.scope:
                stringList.append(display.tag)
        # Default scope
        else:
            if (
                self.verb == "res" or
                self.verb == "rotate" or
                self.verb == "brightness" or
                self.verb == "underscan"
            ):
                stringList.append("main")

            elif (
                self.verb == "show" or
                (self.verb == "mirror" and self.type == "disable")
            ):
                stringList.append("all")

        return " ".join(stringList)

    # Helper methods

    # todo: move this somewhere for the parser to access?
    # def __getDisplayFromTag(displayTag):
    #     """
    #     Returns a Display for "displayTag"
    #     :param displayTag: The display tag to find the Display of
    #     :return: The Display which displayTag refers to
    #     """
    #     if displayTag == "main":
    #         return getMainDisplay()
    #     elif displayTag == "all":
    #         return getAllDisplays()
    #     elif re.match(r"^ext[0-9]+$", displayTag):
    #         # Get all the external displays (in order)
    #         externals = sorted(getAllDisplays())
    #         for display in externals:
    #             if display.isMain:
    #                 externals.remove(display)
    #                 break
    #
    #         # Get the number in displayTag
    #         externalNum = int(displayTag[3:])
    #         # invalid displayTag
    #         if (
    #                 externalNum < 1 or
    #                 externalNum > len(externals) - 1
    #         ):
    #             print("Invalid display tag {}".format(displayTag))
    #             sys.exit(1)
    #         else:
    #             return externals[externalNum]
    #     else:
    #         print("Invalid display tag {}".format(displayTag))
    #         sys.exit(1)

    def __printNotFound(self):
        print("No matching display mode was found. {}".format(
            "Try removing HiDPI flags to find a mode." if self.hidpi != 0 else ""))

    # Run (and its handlers)

    def run(self):
        """
        Runs the command this Command has stored
        """
        if self.verb == "help":
            self.__handleHelp()
        elif self.verb == "show":
            self.__handleShow()
        elif self.verb == "res":
            self.__handleRes()
        elif self.verb == "brightness":
            self.__handleBrightness()
        elif self.verb == "rotate":
            self.__handleRotate()
        elif self.verb == "underscan":
            self.__handleUnderscan()
        elif self.verb == "mirror":
            self.__handleMirror()

    def __handleHelp(self):
        """
        Shows the user usage information (either for a specific verb, or general help)
        """
        usage = {
            "help": "\n".join([
                "usage: display_manager.py {{ help | show | res | brightness | rotate | underscan | mirror }}",
                "",
                "Type any of the commands after \"help\" to get command-specific usage information:",
                "   help        Show this help information.",
                "   res         Set the display resolution.",
                "   show        Show current/available display configurations.",
                "   brightness  Control display brightness.",
                "   rotate      Control display rotation.",
                "   underscan   Show or set the current display underscan.",
                "   mirror      Enable or disable screen mirroring.",
            ]), "show": "\n".join([
                "usage: display_manager.py show [command] [options] [scope]",
                "",
                "COMMANDS",
                "   current (default)   Show current display settings.",
                "   highest             Show the highest available resolution.",
                "   all                 Show all available resolutions.",
                "",
                "OPTIONS",
                "   only-hidpi  Only show HiDPI resolutions.",
                "   no-hidpi    Don\'t show HiDPI resolutions.",
                "",
                "SCOPE",
                "   main            Perform this command on the main display.",
                "   ext<N>          Perform this command on external display number <N>.",
                "   all (default)   Perform this command on all connected displays.",
            ]), "res": "\n".join([
                "usage: display_manager.py res [resolution] [options] [scope]",
                "",
                "RESOLUTION",
                "   To set to highest available resolution, enter \"highest\".",
                "   For a custom resolution, enter the width (in pixels) and the height (in pixels), "
                "separated by a space.",
                "",
                "OPTIONS",
                "   refresh [value]     Refresh rate (default: 0).",
                "   only-hidpi          Only choose HiDPI resolutions.",
                "   no-hidpi            Don\'t choose HiDPI resolutions.",
                "",
                "SCOPE",
                "   main (default)  Perform this command on the main display.",
                "   ext<N>          Perform this command on external display number <N>.",
                "   all             Perform this command on all connected displays.",
            ]), "brightness": "\n".join([
                "usage: display_manager.py brightness [brightness] [scope]",
                "",
                "BRIGHTNESS",
                "   A number between 0 and 1, where 0 is minimum brightness, and 1 is maximum brightness.",
                "",
                "SCOPE",
                "   main (default)  Perform this command on the main display.",
                "   ext<N>          Perform this command on external display number <N>.",
                "   all             Perform this command on all connected displays.",
            ]), "rotate": "\n".join([
                "usage: display_manager.py rotate [angle] [scope]",
                "",
                "ANGLE",
                "   The number of degrees to rotate the display. Must be a multiple of 90.",
                "",
                "SCOPE",
                "   main (default)  Perform this command on the main display.",
                "   ext<N>          Perform this command on external display number <N>.",
                "   all             Perform this command on all connected displays.",
            ]), "underscan": "\n".join([
                "usage: display_manager.py underscan [underscan] [scope]",
                "",
                "UNDERSCAN",
                "   A number between 0 and 1, where 0 is minimum underscan, and 1 is maximum underscan.",
                "",
                "SCOPE",
                "   main (default)  Perform this command on the main display.",
                "   ext<N>          Perform this command on external display number <N>.",
                "   all             Perform this command on all connected displays.",
            ]), "mirror": "\n".join([
                "usage: display_manager.py mirror [command] [source] [target(s)]",
                "",
                "COMMANDS",
                "   enable          Set <target> to mirror <source>.",
                "   disable         Disable mirroring from <source> to <target>.",
                "",
                "SOURCE/TARGET(S)",
                "   source (required for <enable>)",
                "       The display which will be mirrored by the target(s). "
                "Must be an element of <SCOPE> (see below). Cannot be \"all\".",
                "   target(s) (required for both <enable> and <disable>)",
                "       The display(s) which will mirror the source. Must be an element of <SCOPE> (see below).",
                "",
                "SCOPE",
                "   main    The main display.",
                "   ext<N>  External display number <N>.",
                "   all (default target for <disable>)",
                "       For <enable>: all connected displays besides [source]. Only available to [target].",
                "       For <disable>: all connected displays.",
            ])}

        print(usage[self.type])

    def __handleShow(self):
        """
        Shows the user information about connected displays
        """
        for display in self.scope:
            # Always print display identifier
            print("{0}".format(display.tag))

            if self.type == "current":
                current = display.currentMode
                if current:
                    print("{}".format(current))
                else:
                    self.__printNotFound()

                if display.brightness:
                    print("Brightness: {}".format(display.brightness))
                if display.rotation:
                    print("Rotation: {}".format(display.rotation))
                if display.underscan:
                    print("Underscan: {}".format(display.underscan))
                if display.mirrorOf:
                    print("Mirror of: {}".format(display.mirrorOf))

            elif self.type == "highest":
                current = display.highestMode
                if current:
                    print("{}".format(current))
                else:
                    self.__printNotFound()

            elif self.type == "all":
                foundMatching = False  # whether we ended up printing a matching mode or not
                for mode in sorted(display.allModes, reverse=True):
                    print("    {}".format(mode))
                    foundMatching = True

                if not foundMatching:
                    self.__printNotFound()

    def __handleRes(self):
        """
        Sets the display to the correct DisplayMode.
        """
        for display in self.scope:
            if self.type == "highest":
                highest = display.highestMode(self.hidpi)
                if highest:
                    display.setMode(highest)
                else:
                    self.__printNotFound()
                    sys.exit(1)

            else:
                closest = display.closestMode(self.width, self.height, 32, self.refresh)
                if closest:
                    display.setMode(closest)
                else:
                    self.__printNotFound()
                    sys.exit(1)

    def __handleBrightness(self):
        """
        Sets display brightness
        """
        for display in self.scope:
            display.setBrightness(self.brightness)

    def __handleRotate(self):
        """
        Sets display rotation.
        """
        for display in self.scope:
            display.setRotate(self.angle)

    def __handleUnderscan(self):
        """
        Sets or shows a display's underscan settings.
        """
        for display in self.scope:
            display.setUnderscan(self.underscan)

    def __handleMirror(self):
        """
        Enables or disables mirroring between two displays.
        """
        if self.type == "enable":
            source = self.source
            for target in self.scope:
                target.setMirrorOf(source)

        elif self.type == "disable":
            for target in self.scope:
                # If display is a mirror of another display, disable mirroring between them
                if target.mirrorOf is not None:
                    target.setMirrorOf(None)


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
                    print("Unexpected command.verb \"{}\"".format(command.primary))
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


# todo: this. see display_manager.py
def getCommand(commandString):
    return commandString


def parseCommands(string):
    """
    :param string: The string to get Commands from
    :return: Commands contained within the string
    """
    # The types of commands that can be issued
    verbs = ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]

    # The first command does not start with a valid verb
    if sys.argv[1] not in verbs:
        # todo: add "showHelp" or analogous function here
        sys.exit(1)

    # Find all of the indices in string that are verbs
    verbIndices = []
    for i in range(1, len(string)):
        if string[i] in verbs:
            verbIndices.append(i)

    # User entered only one command
    if len(verbIndices) == 0:
        return getCommand(" ".join(string))
    # User entered multiple commands
    else:
        # Split string along between verbs
        commandStrings = [" ".join(string[0:verbIndices[0]])]
        for j in range(1, len(verbIndices)):
            commandStrings.append(" ".join(string[verbIndices[j - 1]:verbIndices[j]]))
        commandStrings.append(" ".join(string[verbIndices[-1]:]))

        commands = CommandList()
        for commandString in commandStrings:
            command = getCommand(commandString)
            if command:
                commands.addCommand(command)
        return commands


def main():
    # Attempt to parse the commands
    try:
        commands = parseCommands(sys.argv[1:])
        commands.run()
    except CommandSyntaxError:
        command = Command("help")
        command.run()
        sys.exit(1)


if __name__ == "__main__":
    main()
