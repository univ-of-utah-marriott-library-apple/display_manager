#!/usr/bin/python

# This script allows users to access Display Manager through the command line.

import collections
from display_manager_lib import *


class CommandSyntaxError(Exception):
    """
    Raised if commands have improper syntax
        (e.g. wrong number of arguments, arguments in wrong place, invalid (sub)command(s), etc.)
    """
    pass


class CommandValueError(Exception):
    """
    Raised if commands have unexpected values
        (e.g. values are incorrect type, values are outside expected range, etc.)
    """
    pass


class CommandExecutionError(Exception):
    """
    Raised if commands could not be executed (usually due to a DisplayError)
    """

    def __init__(self, command, message):
        """
        :param command: Command which raised this exception
        :param message: Description of what went wrong
        """
        self.command = command
        self.message = message


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

    def __init__(self, verb, **kwargs):
        # Determine verb
        if verb in ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]:
            self.verb = verb
        else:
            raise CommandSyntaxError("Unrecognized command \"{}\".".format(verb))

        # Determine type, scope
        self.type = kwargs["type"] if "type" in kwargs else None
        self.scope = kwargs["scope"] if "scope" in kwargs else None

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

    # Run (and its handlers)

    def run(self):
        """
        Runs the command this Command has stored
        """
        try:
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
        except DisplayError as e:
            raise CommandExecutionError(self, e.message)

    def __handleHelp(self):
        """
        Shows the user usage information (either for a specific verb, or general help)
        """
        helpTypes = {
            "usage": "\n".join([
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
            ]), "help": "\n".join([
                "usage: display_manager.py help [command]",
                "",
                "COMMAND",
                "   The command to get more detailed information about. Must be one of the following:",
                "       {{ help | show | res | brightness | rotate | underscan | mirror }}",
            ]), "show": "\n".join([
                "usage: display_manager.py show [subcommand] [options] [scope]",
                "",
                "SUBCOMMANDS",
                "   current (default)   Show current display settings.",
                "   highest             Show the highest available resolution.",
                "   available           Show all available resolutions.",
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
                "   A number between 0 and 1 (inclusive), where 0 is minimum brightness, and 1 is maximum brightness.",
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
                "   A number between 0 and 1 (inclusive), where 0 is minimum underscan, and 1 is maximum underscan.",
                "",
                "SCOPE",
                "   main (default)  Perform this command on the main display.",
                "   ext<N>          Perform this command on external display number <N>.",
                "   all             Perform this command on all connected displays.",
            ]), "mirror": "\n".join([
                "usage: display_manager.py mirror [subcommand] [source] [target(s)]",
                "",
                "SUBCOMMANDS",
                "   enable      Set <target> to mirror <source>.",
                "   disable     Disable mirroring from <source> to <target>.",
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

        if self.type in helpTypes:
            print(helpTypes[self.type])
        else:
            print(helpTypes["usage"])

    def __handleShow(self):
        """
        Shows the user information about connected displays
        """
        for display in self.scope:
            # Always print display identifier
            print("{0}".format(display.tag))

            if self.type == "current":
                current = display.currentMode
                print("{}".format(current))

                if display.brightness:
                    print("Brightness: {}".format(display.brightness))
                if display.rotation:
                    print("Rotation: {}".format(display.rotation))
                if display.underscan:
                    print("Underscan: {}".format(display.underscan))
                if display.mirrorOf:
                    print("Mirror of: {}".format(display.mirrorOf))

            elif self.type == "highest":
                current = display.highestMode(self.hidpi)
                if current:
                    print("{}".format(current))

            elif self.type == "all":
                for mode in sorted(display.allModes, reverse=True):
                    print("    {}".format(mode))

    def __handleRes(self):
        """
        Sets the display to the correct DisplayMode.
        """
        for display in self.scope:
            if self.type == "highest":
                highest = display.highestMode(self.hidpi)
                display.setMode(highest)

            else:
                closest = display.closestMode(self.width, self.height, 32, self.refresh)
                display.setMode(closest)

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
        for display in command.scope:
            if display.displayID in self.__commandDict:
                self.__commandDict[display.displayID].append(command)
            else:
                self.__commandDict[display.displayID] = [command]

    def run(self):
        """
        Runs all stored Commands in a non-interfering fashion
        """
        for displayID in self.__commandDict:
            # Commands for this particular display
            displayCommands = self.__commandDict[displayID]

            # Group commands by type. Must preserve ordering to avoid interfering commands
            commandGroups = collections.OrderedDict([
                ("res", []),
                ("mirror", []),
                ("rotate", []),
                ("underscan", []),
                ("brightness", []),
                ("show", []),
            ])
            for command in displayCommands:
                if command.verb in commandGroups:
                    commandGroups[command.verb].append(command)
                else:
                    raise CommandSyntaxError("\"{}\" is not a valid command".format(command.verb))

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
                        try:
                            commands[-1].run()
                        except DisplayError as e:
                            raise CommandExecutionError(commands[-1], e.message)

                    # "show" commands don't interfere with each other, so run all of them
                    elif commandType == "show":
                        for command in commands:
                            try:
                                command.run()
                            except DisplayError as e:
                                raise CommandExecutionError(command, e.message)

                    # "mirror" commands are the most complicated to deal with
                    elif commandType == "mirror":
                        command = commands[-1]

                        if command.type == "enable":
                            display = Display(displayID)
                            # The current Display that the above "display" is mirroring
                            currentMirror = display.mirrorOf
                            # Become a mirror of most recently requested display
                            mirrorDisplay = Display(command.mirrorDisplayID)

                            # If display is not a mirror of any other display
                            if currentMirror is None:
                                try:
                                    display.setMirrorOf(mirrorDisplay)
                                except DisplayError as e:
                                    raise CommandExecutionError(command, e.message)

                            # The user requested that this display mirror itself, or that it mirror a display
                            # which it is already mirroring. In either case, nothing should be done
                            elif display == currentMirror or currentMirror == mirrorDisplay:
                                pass

                            # display is already a mirror, but not of the requested display
                            else:
                                # First disable mirroring, then enable it for new mirror
                                display.setMirrorOf(None)
                                display.setMirrorOf(mirrorDisplay)
                                try:
                                    display.setMirrorOf(None)
                                    display.setMirrorOf(mirrorDisplay)
                                except DisplayError as e:
                                    raise CommandExecutionError(command, e.message)

                        elif command.type == "disable":
                            try:
                                command.run()
                            except DisplayError as e:
                                raise CommandExecutionError(command, e.message)


def getCommand(commandString):
    if not commandString:
        return None

    # Individual words/values in the command
    words = commandString.split()

    # Determine verb, and remove it from words
    verb = words.pop(0)

    # Determine scope, and remove it from words
    scopePattern = r"^(main|ext[0-9]+|all)$"
    scopeTags = []
    # Iterate backwards through the indices of "words"
    for i in range(len(words) - 1, -1, -1):
        if re.match(scopePattern, words[i]):
            # If this scope tag is at the end of the list
            if words[i] == words[-1]:
                scopeTags.append(words.pop(i))
            # This scope tag is in the wrong place
            else:
                raise CommandSyntaxError("Invalid placement of {}".format(words[i]))

    def getDisplayFromTag(displayTag):
        """
        Returns a Display for "displayTag"
        :param displayTag: The display tag to find the Display of
        :return: The Display which displayTag refers to
        """
        if displayTag == "main":
            return getMainDisplay()
        elif displayTag == "all":
            return getAllDisplays()
        elif re.match(r"^ext[0-9]+$", displayTag):
            # Get all the external displays (in order)
            externals = sorted(getAllDisplays())
            for display in externals:
                if display.isMain:
                    externals.remove(display)
                    break

            # Get the number in displayTag
            externalNum = int(displayTag[3:])
            # invalid displayTag
            if (
                    externalNum < 0 or
                    externalNum > len(externals) - 1
            ):
                raise CommandValueError("There is no display \"{}\"".format(displayTag))
            else:
                return externals[externalNum]
        else:
            raise CommandSyntaxError("Invalid display tag \"{}\"".format(displayTag))

    # Get actual Displays for scope
    scope = []
    for scopeTag in scopeTags:
        scope.append(getDisplayFromTag(scopeTag))

    # Determine positionals (all remaining words)
    positionals = words

    # Create new command with verb and scope
    command = Command(verb, scope=scope)

    if verb == "help":
        if len(positionals) == 0:
            # Default type
            command.type = "help"
        elif len(positionals) == 1:
            if positionals[0] in ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]:
                command.type = positionals[0]
            # Invalid type
            else:
                raise CommandValueError("{} is not a valid command".format(positionals[0]))
        # Too many arguments
        else:
            raise CommandSyntaxError("\"help\" commands can only have one argument")

    elif verb == "show":
        if len(positionals) == 0:
            # Default type
            command.type = "current"
        if len(positionals) == 1:
            if positionals[0] in ["current", "highest", "available"]:
                command.type = positionals[0]
            # Invalid type
            else:
                raise CommandValueError("{} is not a valid subcommand".format(positionals[0]))
        # Too many arguments
        else:
            raise CommandSyntaxError("\"show\" commands can only have one subcommand")

    # TODO: THIS
    elif verb == "res":
        pass

    elif verb == "brightness":
        if len(positionals) == 1:
            try:
                brightness = float(positionals[0])
                # Brightness must be between 0 and 1
                if brightness < 0 or brightness > 1:
                    raise CommandValueError("{} is not a number between 0 and 1 (inclusive)".format(positionals[0]))
            # Couldn't convert to float
            except ValueError:
                raise CommandValueError("{} is not a number between 0 and 1 (inclusive)".format(positionals[0]))
        # Too many arguments
        else:
            raise CommandSyntaxError("\"brightness\" commands can only have one argument")

        command.brightness = brightness

    elif verb == "rotate":
        if len(positionals) == 1:
            try:
                angle = int(positionals[0])
                # Rotation must be multiple of 90
                if angle % 90 != 0:
                    raise CommandValueError("{} is not a multiple of 90".format(positionals[0]))
            # Couldn't convert to int
            except ValueError:
                raise CommandValueError("{} is not a multiple of 90".format(positionals[0]))
        # Too many arguments
        else:
            raise CommandSyntaxError("\"rotate\" commands can only have one argument")

        command.angle = angle

    elif verb == "underscan":
        if len(positionals) == 1:
            try:
                underscan = float(positionals[0])
                # Underscan must be between 0 and 1
                if underscan < 0 or underscan > 1:
                    raise CommandValueError("{} is not a number between 0 and 1 (inclusive)".format(positionals[0]))
            # Couldn't convert to float
            except ValueError:
                raise CommandValueError("{} is not a number between 0 and 1 (inclusive)".format(positionals[0]))
        # Too many arguments
        else:
            raise CommandSyntaxError("\"underscan\" commands can only have one argument")

        command.underscan = underscan

    elif verb == "mirror":
        if len(positionals) == 0:
            raise CommandSyntaxError("\"mirror\" commands must have a subcommand")
        if len(positionals) == 1:
            # Determine type
            if positionals[0] in ["enable", "disable"]:
                command.type = positionals[0]
            # Invalid type
            else:
                raise CommandValueError("{} is not a valid subcommand".format(positionals[0]))
            # For "enable" type, first element in scope is source
            if command.type == "enable":
                command.source = command.scope.pop(-1)
        # Too many arguments
        else:
            raise CommandSyntaxError("\"mirror\" commands can only have one subcommand")

    return command


def parseCommands(string):
    """
    :param string: The string to get Commands from
    :return: Commands contained within the string
    """
    # The types of commands that can be issued
    verbPattern = r"help|show|res|brightness|rotate|underscan|mirror"
    # Pattern for finding multiple commands
    commandPattern = r"((?:{0}).*?)(?:(?: (?={0}))|\Z)".format(verbPattern)

    # Make sure the command starts with a valid verb
    try:
        firstWord = re.match("^(" + verbPattern + ")$", string.split()[0]).group(0)
    # If the first word wasn't a valid verb, re.match returned a None, which has no ".group"
    except AttributeError:
        raise CommandSyntaxError("\"{}\" is not a valid type of command".format(string.split()[0]))

    # Get all the individual commands
    if "help" not in string:
        commandStrings = re.findall(commandPattern, string)
    # Cannot run more than one command if one of them is a "help" command
    else:
        # The whole command is a help command
        if firstWord == "help":
            commandStrings = [string]
        # The help command is only one of multiple commands
        else:
            raise CommandSyntaxError("Cannot run multiple commands if one is \"help\"")

    # Make the CommandList from the given command strings
    commands = CommandList()
    for commandString in commandStrings:
        command = getCommand(commandString)
        if command:
            commands.addCommand(command)

    return commands


def main():
    # Attempt to parse the commands
    try:
        commands = parseCommands(" ".join(sys.argv[1:]))
    except CommandSyntaxError:
        # Show usage information
        Command("help").run()
    except (CommandSyntaxError, CommandValueError) as e:
        print("ERROR: {}".format(e))
        raise SystemExit()
    # Command successfully parsed
    else:
        try:
            commands.run()
        except CommandExecutionError as e:
            print("Could not execute \"{}\"".format(e.command.__str__()))
            print("ERROR: {}".format(e.message))
            raise SystemExit()


if __name__ == "__main__":
    main()
