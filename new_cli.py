#!/usr/bin/python

# This script allows users to access Display Manager through the command line.

import collections
from display_manager_lib import *


class CommandSyntaxError(Exception):
    """
    Raised if commands have improper syntax
        (e.g. wrong number of arguments, arguments in wrong place, invalid (sub)command(s), etc.)
    """

    def __init__(self, message, verb=None):
        """
        :param verb: The type of command that raised this exception
        :param message: Description of what went wrong
        """
        self.message = message
        self.verb = verb


class CommandValueError(Exception):
    """
    Raised if commands have unexpected values
        (e.g. values are incorrect type, values are outside expected range, etc.)
    """

    def __init__(self, message, verb=None):
        """
        :param verb: The type of command that raised this exception
        :param message: Description of what went wrong
        """
        self.message = message
        self.verb = verb


class CommandExecutionError(Exception):
    """
    Raised if commands could not be executed (usually due to a DisplayError)
    """

    def __init__(self, message, command=None):
        """
        :param command: The Command which raised this exception
        :param message: Description of what went wrong
        """
        self.message = message
        self.command = command


class Command(object):
    """
    Represents a user-requested command to Display Manager.
    """

    def __init__(self, **kwargs):
        """
        :param kwargs: Includes verb ("command type"), subcommand, scope, values, options, and rawInput
        """
        # Determine verb
        if kwargs["verb"]:
            if kwargs["verb"] in ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]:
                self.verb = kwargs["verb"]
            else:
                raise CommandSyntaxError("\"{}\" is not a valid command".format(kwargs["verb"]))

        # Determine subcommand, scope
        self.subcommand = kwargs["subcommand"] if "subcommand" in kwargs else None
        self.scope = kwargs["scope"] if "scope" in kwargs else None

        # Determine values, options
        self.width = int(kwargs["width"]) if "width" in kwargs else None
        self.height = int(kwargs["height"]) if "height" in kwargs else None
        self.refresh = int(kwargs["refresh"]) if "refresh" in kwargs else None
        self.hidpi = int(kwargs["hidpi"]) if "hidpi" in kwargs else None
        self.angle = int(kwargs["angle"]) if "angle" in kwargs else None
        self.brightness = float(kwargs["brightness"]) if "brightness" in kwargs else None
        self.underscan = float(kwargs["underscan"]) if "underscan" in kwargs else None
        self.source = kwargs["source"] if "source" in kwargs else None

        # Keep raw command text (for use in error messages)
        self.rawInput = kwargs["rawInput"] if "rawInput" in kwargs else None

        # Make sure IOKit is ready for use in any/all commands
        getIOKit()

    def __str__(self):
        """
        :return: A string which would result in this command via the command line
        """
        # A list to contain strings of all the arguments in the command
        # Determine verb
        stringList = [self.verb]

        # Determine subcommand
        if self.subcommand:
            stringList.append(self.subcommand)

        # Determine value

        if self.verb == "res":
            if self.width and self.height:  # can also be set by subcommand=highest
                stringList.append(self.width)
                stringList.append(self.height)

        elif self.verb == "rotate":
            stringList.append(self.angle)
        elif self.verb == "brightness":
            stringList.append(self.brightness)
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
                (self.verb == "mirror" and self.subcommand == "disable")
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
            elif self.verb == "rotate":
                self.__handleRotate()
            elif self.verb == "brightness":
                self.__handleBrightness()
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
                "usage: display_manager.py [command]",
                "",
                "COMMANDS",
                "   help        Show this help information",
                "   res         Set the display resolution",
                "   show        Show current/available display configurations",
                "   brightness  Control display brightness",
                "   rotate      Control display rotation",
                "   underscan   Show or set the current display underscan",
                "   mirror      Enable or disable screen mirroring",
            ]), "help": "\n".join([
                "usage: display_manager.py help [command]",
                "",
                "COMMANDS",
                "   The command to get more detailed information about; must be one of the following:",
                "       help        Show this help information",
                "       res         Set the display resolution",
                "       show        Show current/available display configurations",
                "       brightness  Control display brightness",
                "       rotate      Control display rotation",
                "       underscan   Show or set the current display underscan",
                "       mirror      Enable or disable screen mirroring",
            ]), "show": "\n".join([
                "usage: display_manager.py show [subcommand] (parameters) (scope)",
                "",
                "SUBCOMMANDS",
                "   current (default)   Show current display settings",
                "   highest             Show the highest available resolution",
                "   available           Show all available resolutions",
                "",
                "PARAMETERS (never obligatory; not available to \"current\")",
                "   only-hidpi  Only show HiDPI resolutions",
                "   no-hidpi    Don\'t show HiDPI resolutions",
                "",
                "   (Note: by default, both HiDPI and non-HiDPI resolutions are shown)",
                "",
                "SCOPE (optional)",
                "   main            Perform this command on the main display",
                "   ext<N>          Perform this command on external display number <N>",
                "   all (default)   Perform this command on all connected displays",
            ]), "res": "\n".join([
                "usage: display_manager.py res [resolution] (refresh) (parameters) (scope)",
                "",
                "RESOLUTION",
                "   highest             Set the display to the highest available resolution",
                "   <width> <height>    Width and height (in pixels)",
                "       (Note: width and height must be separated by at least one space)",
                "",
                "REFRESH (optional)",
                "   <refresh>   Refresh rate (in Hz)",
                "       (Note: if refresh rate is not specified, it will default to whichever rate is "
                "available at the desired resolution; if 0 is one of the options, it will be selected)",
                "",
                "PARAMETERS (optional)",
                "   only-hidpi  Only show HiDPI resolutions",
                "   no-hidpi    Don\'t show HiDPI resolutions",
                "",
                "   (Note: by default, both HiDPI and non-HiDPI resolutions are shown)",
                "",
                "SCOPE (optional)",
                "   main (default)  Perform this command on the main display",
                "   ext<N>          Perform this command on external display number <N>",
                "   all             Perform this command on all connected displays",
            ]), "rotate": "\n".join([
                "usage: display_manager.py rotate [angle] (scope)",
                "",
                "ANGLE",
                "   <angle>     Desired display rotation; must be a multiple of 90",
                "",
                "SCOPE (optional)",
                "   main (default)  Perform this command on the main display",
                "   ext<N>          Perform this command on external display number <N>",
                "   all             Perform this command on all connected displays",
            ]), "brightness": "\n".join([
                "usage: display_manager.py brightness [brightness] (scope)",
                "",
                "BRIGHTNESS",
                "   <brightness>    Must be a number between 0 and 1 (inclusive); "
                "0 is minimum brightness, and 1 is maximum brightness",
                "",
                "SCOPE (optional)",
                "   main (default)  Perform this command on the main display",
                "   ext<N>          Perform this command on external display number <N>",
                "   all             Perform this command on all connected displays",
            ]), "underscan": "\n".join([
                "usage: display_manager.py underscan [underscan] (scope)",
                "",
                "UNDERSCAN",
                "   <underscan>     A number between 0 and 1 (inclusive); "
                "0 is minimum underscan, and 1 is maximum underscan",
                "",
                "SCOPE (optional)",
                "   main (default)  Perform this command on the main display",
                "   ext<N>          Perform this command on external display number <N>",
                "   all             Perform this command on all connected displays",
            ]), "mirror": "\n".join([
                "usage: display_manager.py mirror enable [source] [target(s)]",
                "   or: display_manager.py mirror disable [scope]"
                "",
                "SUBCOMMANDS",
                "   enable      Set <target> to mirror <source>",
                "   disable     Disable mirroring from <source> to <target>",
                "",
                "SOURCE/TARGET(S)",
                "   source (required for <enable>)",
                "       The display which will be mirrored by the target(s); "
                "must be a single element of <SCOPE> (see below); cannot be \"all\"",
                "   target(s) (required for both <enable> and <disable>)",
                "       The display(s) which will mirror the source; must be an element of <SCOPE> (see below)",
                "",
                "SCOPE",
                "   main    The main display",
                "   ext<N>  External display number <N>",
                "   all (default scope for <disable>)",
                "       For <enable>: all connected displays besides [source]; only available to [target(s)]",
                "       For <disable>: all connected displays",
            ])}

        if self.subcommand in helpTypes:
            print(helpTypes[self.subcommand])
        else:
            print(helpTypes["usage"])

    def __handleShow(self):
        """
        Shows the user information about connected displays
        """
        for display in self.scope:
            # Always print display identifier
            print("{0}".format(display.tag))

            if self.subcommand == "current":
                current = display.currentMode
                print("{}".format(current))

                if display.rotation is not None:
                    print("Rotation: {}".format(display.rotation))
                if display.brightness is not None:
                    print("Brightness: {}".format(display.brightness))
                if display.underscan is not None:
                    print("Underscan: {}".format(display.underscan))
                if display.mirrorOf is not None:
                    print("Mirror of: {}".format(display.mirrorOf))

            elif self.subcommand == "highest":
                current = display.highestMode(self.hidpi)
                if current:
                    print("{}".format(current))

            elif self.subcommand == "all":
                for mode in sorted(display.allModes, reverse=True):
                    print("    {}".format(mode))

    def __handleRes(self):
        """
        Sets the display to the correct DisplayMode.
        """
        for display in self.scope:
            if self.subcommand == "highest":
                highest = display.highestMode(self.hidpi)
                display.setMode(highest)

            else:
                closest = display.closestMode(self.width, self.height, 32, self.refresh)
                display.setMode(closest)

    def __handleRotate(self):
        """
        Sets display rotation.
        """
        for display in self.scope:
            display.setRotate(self.angle)

    def __handleBrightness(self):
        """
        Sets display brightness
        """
        for display in self.scope:
            display.setBrightness(self.brightness)

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
        if self.subcommand == "enable":
            source = self.source
            for target in self.scope:
                target.setMirrorOf(source)

        elif self.subcommand == "disable":
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

            # Group commands by subcommand. Must preserve ordering to avoid interfering commands
            commandGroups = collections.OrderedDict([
                ("res", []),
                ("rotate", []),
                ("mirror", []),
                ("underscan", []),
                ("brightness", []),
                ("show", []),
            ])
            for command in displayCommands:
                if command.verb in commandGroups:
                    commandGroups[command.verb].append(command)
                else:
                    raise CommandSyntaxError("\"{}\" is not a valid command".format(command.verb))

            # Run commands by subcommand
            for commandType in commandGroups:
                # Commands for this display, of this subcommand
                commands = commandGroups[commandType]

                if len(commands) > 0:
                    # Multiple commands of these types will undo each other.
                    # As such, just run the most recently added command (the last in the list)
                    if (
                            commandType == "set" or
                            commandType == "rotate" or
                            commandType == "brightness" or
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
                raise CommandSyntaxError("Invalid placement of {}".format(words[i]), verb=verb)

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
                raise CommandValueError("There is no display \"{}\"".format(displayTag), verb=verb)
            else:
                return externals[externalNum]
        else:
            raise CommandSyntaxError("Invalid display tag \"{}\"".format(displayTag), verb=verb)

    # Get actual Displays for scope
    scope = []
    for scopeTag in scopeTags:
        scope.append(getDisplayFromTag(scopeTag))

    # Determine positionals (all remaining words)
    positionals = words

    # todo: parse for only-hidpi and no-hidpi

    if verb == "help":
        if len(positionals) == 0:
            # Default (sub)command
            subcommand = "help"
        elif len(positionals) == 1:
            if positionals[0] in ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]:
                subcommand = positionals[0]
            # Invalid (sub)command
            else:
                raise CommandValueError("{} is not a valid command".format(positionals[0]), verb=verb)
        # Too many arguments
        else:
            raise CommandSyntaxError("\"help\" commands can only have one argument", verb=verb)

        return Command(
            verb=verb,
            subcommand=subcommand,
        )

    elif verb == "show":
        if len(positionals) == 0:
            # Default subcommand
            subcommand = "current"
        elif len(positionals) == 1:
            if positionals[0] in ["current", "highest", "available"]:
                subcommand = positionals[0]
            # Invalid subcommand
            else:
                raise CommandValueError("{} is not a valid subcommand".format(positionals[0]), verb=verb)
        # Too many arguments
        else:
            raise CommandSyntaxError("\"show\" commands can only have one subcommand", verb=verb)

        if len(scope) == 0:
            # Default scope
            scope = getAllDisplays()

        return Command(
            verb=verb,
            subcommand=subcommand,
            scope=scope,
        )

    elif verb == "res":
        if len(positionals) == 0:
            raise CommandSyntaxError("\"res\" commands must specify a resolution", verb=verb)
        # case: "highest" (or error)
        elif len(positionals) == 1:
            if positionals[0] == "highest":
                subcommand = positionals[0]
            else:
                raise CommandValueError(
                    "\"res\" commands must either specify both width and height or use the \"highest\" keyword",
                    verb=verb
                )

            if len(scope) == 0:
                # Default scope
                scope = getMainDisplay()

            return Command(
                verb=verb,
                subcommand=subcommand,
                scope=scope,
            )
        # cases: ("highest", refresh), (width, height)
        elif len(positionals) == 2:
            # case: "highest", refresh
            if positionals[0] == "highest":
                subcommand = positionals[0]
                try:
                    refresh = int(positionals[1])
                except ValueError:
                    raise CommandValueError("\"{}\" is not a valid refresh rate")

                return Command(
                    verb=verb,
                    subcommand=subcommand,
                    refresh=refresh,
                    scope=scope,
                )
            # case: width, height
            else:
                # Try to parse positionals as integers
                wh = []
                for i in range(len(positionals)):
                    try:
                        wh.append(int(positionals[i]))
                    except ValueError:
                        wh.append(-1)
                width, height = wh
                # Neither width nor height were integers (and thus invalid pixel counts)
                if width == -1 and height == -1:
                    raise CommandValueError(
                        "Neither \"{}\" nor \"{}\" are valid widths or heights".format(
                            positionals[0], positionals[1]),
                        verb=verb
                    )
                # width was invalid
                elif width == -1:
                    raise CommandValueError(
                        "\"{}\" is not a valid width".format(positionals[0]),
                        verb=verb
                    )
                # height was invalid
                elif height == -1:
                    raise CommandValueError(
                        "\"{}\" is not a valid height".format(positionals[1]),
                        verb=verb
                    )

                return Command(
                    verb=verb,
                    width=width,
                    height=height,
                    scope=scope,
                )
        # case: (width, height, refresh)
        elif len(positionals) == 3:
            # Try to parse width, height, and refresh as integers
            whr = []
            for i in range(len(positionals)):
                try:
                    whr.append(int(positionals[i]))
                except ValueError:
                    whr.append(-1)
            width, height, refresh = whr
            # Nothing was an integer
            if width == -1 and height == -1 and refresh == -1:
                raise CommandValueError(
                    "\"{}\"x\"{}\" at \"{}\"Hz is not a valid resolution".format(
                        positionals[0], positionals[1], positionals[2]),
                    verb=verb
                )
            # Neither width nor height were integers
            elif width == -1 or height == -1:
                raise CommandValueError(
                    "\"{}\"x\"{}\" is not a valid resolution".format(
                        positionals[0], positionals[1]),
                    verb=verb
                )
            # refresh was not an integer
            elif refresh == -1:
                raise CommandValueError(
                    "\"{}\" is not a valid refresh rate".format(positionals[2]),
                    verb=verb
                )

            return Command(
                verb=verb,
                width=width,
                height=height,
                refresh=refresh,
                scope=scope,
            )
        else:
            raise CommandSyntaxError("\"res\" commands cannot have more than three arguments", verb=verb)

    elif verb == "rotate":
        if len(positionals) == 0:
            raise CommandSyntaxError("\"rotate\" commands must specify an angle", verb=verb)
        elif len(positionals) == 1:
            try:
                angle = int(positionals[0])
                # Rotation must be multiple of 90
                if angle % 90 != 0:
                    raise CommandValueError("{} is not a multiple of 90".format(positionals[0]), verb=verb)
            # Couldn't convert to int
            except ValueError:
                raise CommandValueError("{} is not a multiple of 90".format(positionals[0]), verb=verb)
        # Too many arguments
        else:
            raise CommandSyntaxError("\"rotate\" commands can only have one argument", verb=verb)

        if len(scope) == 0:
            # Default scope
            scope = getMainDisplay()

        return Command(
            verb=verb,
            angle=angle,
            scope=scope,
        )

    elif verb == "brightness":
        if len(positionals) == 0:
            raise CommandSyntaxError("\"brightness\" commands must specify a brightness value", verb=verb)
        elif len(positionals) == 1:
            try:
                brightness = float(positionals[0])
                # Brightness must be between 0 and 1
                if brightness < 0 or brightness > 1:
                    raise CommandValueError(
                        "{} is not a number between 0 and 1 (inclusive)".format(positionals[0]),
                        verb=verb
                    )
            # Couldn't convert to float
            except ValueError:
                raise CommandValueError(
                    "{} is not a number between 0 and 1 (inclusive)".format(positionals[0]),
                    verb=verb
                )
        # Too many arguments
        else:
            raise CommandSyntaxError("\"brightness\" commands can only have one argument", verb=verb)

        if len(scope) == 0:
            # Default scope
            scope = getMainDisplay()

        return Command(
            verb=verb,
            brightness=brightness,
            scope=scope,
        )

    elif verb == "underscan":
        if len(positionals) == 0:
            raise CommandSyntaxError("\"underscan\" commands must specify an underscan value", verb=verb)
        elif len(positionals) == 1:
            try:
                underscan = float(positionals[0])
                # Underscan must be between 0 and 1
                if underscan < 0 or underscan > 1:
                    raise CommandValueError(
                        "{} is not a number between 0 and 1 (inclusive)".format(positionals[0]),
                        verb=verb
                    )
            # Couldn't convert to float
            except ValueError:
                raise CommandValueError(
                    "{} is not a number between 0 and 1 (inclusive)".format(positionals[0]),
                    verb=verb
                )
        # Too many arguments
        else:
            raise CommandSyntaxError("\"underscan\" commands can only have one argument", verb=verb)

        if len(scope) == 0:
            # Default scope
            scope = getMainDisplay()

        return Command(
            verb=verb,
            underscan=underscan,
            scope=scope,
        )

    elif verb == "mirror":
        if len(positionals) == 0:
            raise CommandSyntaxError("\"mirror\" commands must specify a subcommand", verb=verb)
        elif len(positionals) == 1:
            subcommand = positionals[0]
            if subcommand == "enable":
                if len(scope) < 2:
                    raise CommandSyntaxError(
                        "\"mirror enable\" commands require at least one source and one target display",
                        verb=verb
                    )
                else:
                    # For "enable" subcommand, first element in scope is source, and the rest are targets
                    # Since we parsed "scope" in reverse order, source will be last
                    source = scope.pop(-1)

                return Command(
                    verb=verb,
                    subcommand=subcommand,
                    source=source,
                    # "scope" == "target"
                    scope=scope,
                )
            elif subcommand == "disable":
                if len(scope) == 0:
                    # Default scope
                    scope = getAllDisplays()

                return Command(
                    verb=verb,
                    subcommand=subcommand,
                    scope=scope,
                )
            # Invalid subcommand
            else:
                raise CommandValueError("{} is not a valid subcommand".format(subcommand), verb=verb)
        # Too many arguments
        else:
            raise CommandSyntaxError("\"mirror\" commands can only have one subcommand", verb=verb)


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
    firstWordMatch = re.match("^(" + verbPattern + ")$", string.split()[0])
    if firstWordMatch:
        firstWord = firstWordMatch.group(0)
    else:
        raise CommandSyntaxError("\"{}\" is not a valid type of command".format(string.split()[0]))

    # Get all the individual commands
    if "help" not in string:
        commandStrings = re.findall(commandPattern, string)
    # Cannot run more than one command if one of them is a "help" command
    else:
        # The whole command will be interpreted as a single help command
        if firstWord == "help":
            commandStrings = [string]
        # The help command isn't even the first command
        else:
            raise CommandSyntaxError("Cannot run multiple commands if one of them is \"help\"", verb="help")

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
    except (CommandSyntaxError, CommandValueError) as e:
        if e.verb:
            if e.verb in ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]:
                # Show proper usage information for the attempted command
                Command(verb=e.verb).run()
            print("Error in \"{}\":".format(e.verb))
            print(e.message)
        else:
            print("Error: {}".format(e.message))
        raise SystemExit()
    # Command successfully parsed
    else:
        try:
            commands.run()
        except CommandExecutionError as e:
            if e.command.rawInput:
                print("Error in \"{}\":".format(e.command.rawInput))
                print("{}".format(e.message))
            else:
                print("Error: {}".format(e.message))
            raise SystemExit()


if __name__ == "__main__":
    main()
