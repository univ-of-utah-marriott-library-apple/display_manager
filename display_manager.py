#!/usr/bin/env python3

########################################################################
# Copyright (c) 2018 University of Utah Student Computing Labs.        #
# All Rights Reserved.                                                 #
#                                                                      #
# Permission to use, copy, modify, and distribute this software and    #
# its documentation for any purpose and without fee is hereby granted, #
# provided that the above copyright notice appears in all copies and   #
# that both that copyright notice and this permission notice appear    #
# in supporting documentation, and that the name of The University     #
# of Utah not be used in advertising or publicity pertaining to        #
# distribution of the software without specific, written prior         #
# permission. This software is supplied as is without expressed or     #
# implied warranties of any kind.                                      #
########################################################################

# Display Manager, version 1.0.1
# Command-Line Interface

# Programmatically manages Mac displays.
# Can set screen resolution, refresh rate, rotation, brightness, underscan, and screen mirroring.

import sys                          # Collect command-line arguments
import re                           # Parse command-line input
import collections                  # Special collections are required for CommandList
from display_manager_lib import *   # The Display Manager Library


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

        Exception.__init__(self, self.message)


class CommandValueError(Exception):
    """
    Raised if a command's arguments have unexpected values
        (e.g. values are incorrect type, values are outside expected range, etc.)
    """

    def __init__(self, message, verb=None):
        """
        :param verb: The type of command that raised this exception
        :param message: Description of what went wrong
        """
        self.message = message
        self.verb = verb

        Exception.__init__(self, self.message)


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

        Exception.__init__(self, self.message)


class Command(object):
    """
    Represents a user-requested command to Display Manager
    """

    def __init__(self, **kwargs):
        """
        :param kwargs: Includes verb ("command type"), subcommand, scope, and misc. Command values
            verb: string in ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]
            subcommand: string
            scope: Display(s)
            width: int
            height: int
            refresh: int
            hidpi: int (0 -> all; 1 -> no HiDPI; 2 -> only HiDPI)
            angle: int
            brightness: float
            underscan: float
            source: Display
        """
        # Determine verb
        if "verb" in kwargs:
            if kwargs["verb"] in ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]:
                self.verb = kwargs["verb"]
            else:
                raise CommandSyntaxError("\"{}\" is not a valid command".format(kwargs["verb"]))
        else:
            self.verb = None

        # Determine subcommand, scope
        self.subcommand = kwargs["subcommand"] if "subcommand" in kwargs else None
        if "scope" in kwargs:
            if isinstance(kwargs["scope"], list):
                self.scope = kwargs["scope"]
            elif isinstance(kwargs["scope"], AbstractDisplay):
                self.scope = [kwargs["scope"]]
            else:
                self.scope = None
        else:
            self.scope = None

        # Determine values
        self.width = int(kwargs["width"]) if "width" in kwargs else None
        self.height = int(kwargs["height"]) if "height" in kwargs else None
        self.refresh = int(kwargs["refresh"]) if "refresh" in kwargs else None
        # For HiDPI:
        #   0: fits HiDPI or non-HiDPI
        #   1: fits only non-HiDPI
        #   2: fits only HiDPI
        self.hidpi = int(kwargs["hidpi"]) if "hidpi" in kwargs else None
        self.angle = int(kwargs["angle"]) if "angle" in kwargs else None
        self.brightness = float(kwargs["brightness"]) if "brightness" in kwargs else None
        self.underscan = float(kwargs["underscan"]) if "underscan" in kwargs else None
        self.source = kwargs["source"] if "source" in kwargs else None

        # Make sure IOKit is ready for use in any/all commands
        getIOKit()

    # "Magic" methods

    def __str__(self):
        # A list to contain strings of all the arguments in the command
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
        elif self.verb == "mirror" and self.subcommand == "enable":
            stringList.append(self.source.tag)

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
            if len(self.scope) == len(getAllDisplays()):
                stringList.append("all")
            else:
                for display in sorted(self.scope):
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

        # Convert everything to a string so it can be joined
        for i in range(len(stringList)):
            stringList[i] = str(stringList[i])

        return " ".join(stringList)

    def __eq__(self, other):
        def safeScopeCheckEquals(a, b):
            """
            Check whether two Commands' scopes are equal in a None-safe way
            :param a: The first Command
            :param b: The second Command
            :return: Whether the two scopes are equal
            """
            if a.scope and b.scope:
                return set(a.scope) == set(b.scope)
            else:
                return a.scope == b.scope

        if isinstance(other, self.__class__):
            return all([
                isinstance(other, self.__class__),

                self.verb == other.verb,
                self.subcommand == other.subcommand,
                safeScopeCheckEquals(self, other),

                self.width == other.width,
                self.height == other.height,
                self.refresh == other.refresh,
                self.hidpi == other.hidpi,
                self.angle == other.angle,
                self.brightness == other.brightness,
                self.underscan == other.underscan,
                self.source == other.source,
            ])
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        else:
            return NotImplemented

    def __lt__(self, other):
        if self.__eq__(other):
            return False
        else:
            return self.__str__().lower() < self.__str__().lower()

    def __gt__(self, other):
        if self.__eq__(other):
            return False
        else:
            return self.__str__().lower() > self.__str__().lower()

    def __hash__(self):
        return hash(self.__str__())

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
            raise CommandExecutionError(e.message, command=self)

    def __handleHelp(self):
        """
        Shows the user usage information (either for a specific verb, or general help)
        """
        helpTypes = {
            "usage": "\n".join([
                "usage:  display_manager.py <command>",
                "",
                "COMMANDS (required)",
                "    help        Show help information about a command",
                "    show        Show current/available display configurations",
                "    res         Manage display resolution",
                "    brightness  Manage display brightness",
                "    rotate      Manage display rotation",
                "    underscan   Manage display underscan",
                "    mirror      Manage screen mirroring",
            ]), "help": "\n".join([
                "usage:  display_manager.py help <command>",
                "",
                "COMMANDS (required)",
                "    help        Show help information about a command",
                "    show        Show current/available display configurations",
                "    res         Manage display resolution and refresh rate",
                "    brightness  Manage display brightness",
                "    rotate      Manage display rotation",
                "    underscan   Manage display underscan",
                "    mirror      Manage screen mirroring",
            ]), "show": "\n".join([
                "usage:  display_manager.py show [subcommand] [options] [scope...]",
                "",
                "SUBCOMMANDS (optional)",
                "    current (default)   Show the current display configuration",
                "    default             Apple's recommended default configuration",
                "    highest             Show the highest available configuration",
                "    available           Show all available configurations",
                "",
                "OPTIONS (optional; only applies to \"available\")",
                "    no-hidpi    Don\'t show HiDPI resolutions",
                "    only-hidpi  Only show HiDPI resolutions",
                "",
                "    (Note: by default, both HiDPI and non-HiDPI resolutions are shown)",
                "",
                "SCOPE (optional)",
                "    main            Perform this command on the main display",
                "    ext<N>          Perform this command on external display number <N>",
                "    all (default)   Perform this command on all connected displays",
            ]), "res": "\n".join([
                "usage:  display_manager.py res <resolution> [refresh] [options] [scope...]",
                "",
                "RESOLUTION (required)",
                "    default             Apple's recommended default configuration",
                "    highest             Set the display to the highest available configuration",
                "    <width> <height>    Width and height (in pixels)",
                "        (Note: width and height must be separated by at least one space)",
                "",
                "REFRESH (not used by \"default\" or \"highest\" resolution; optional otherwise)",
                "    <refresh>   Refresh rate (in Hz)",
                "        (Note: if refresh rate is not specified, it will default to a rate that is "
                "available at the desired resolution, if possible)",
                "",
                "OPTIONS (optional)",
                "    no-hidpi    Don\'t set to HiDPI resolutions",
                "    only-hidpi  Only set to HiDPI resolutions",
                "",
                "    (Note: by default, both HiDPI and non-HiDPI resolutions are shown)",
                "",
                "SCOPE (optional)",
                "    main (default)  Perform this command on the main display",
                "    ext<N>          Perform this command on external display number <N>",
                "    all             Perform this command on all connected displays",
            ]), "rotate": "\n".join([
                "usage:  display_manager.py rotate <angle> [scope...]",
                "",
                "ANGLE (required)",
                "    <angle>     Desired display rotation; must be a multiple of 90",
                "",
                "SCOPE (optional)",
                "    main (default)  Perform this command on the main display",
                "    ext<N>          Perform this command on external display number <N>",
                "    all             Perform this command on all connected displays",
            ]), "brightness": "\n".join([
                "usage:  display_manager.py brightness <brightness> [scope...]",
                "",
                "BRIGHTNESS (required)",
                "    <brightness>    A number between 0 and 1 (inclusive); "
                "0 is minimum brightness, and 1 is maximum brightness",
                "",
                "SCOPE (optional)",
                "    main (default)  Perform this command on the main display",
                "    ext<N>          Perform this command on external display number <N>",
                "    all             Perform this command on all connected displays",
            ]), "underscan": "\n".join([
                "usage:  display_manager.py underscan <underscan> [scope...]",
                "",
                "UNDERSCAN (required)",
                "    <underscan>     A number between 0 and 1 (inclusive); "
                "0 is minimum underscan, and 1 is maximum underscan",
                "",
                "SCOPE (optional)",
                "    main (default)  Perform this command on the main display",
                "    ext<N>          Perform this command on external display number <N>",
                "    all             Perform this command on all connected displays",
            ]), "mirror": "\n".join([
                "usage:  display_manager.py mirror enable <source> <target...>",
                "   or:  display_manager.py mirror disable [scope...]",
                "",
                "SUBCOMMANDS (required)",
                "    enable      Set <target> to mirror <source>",
                "    disable     Disable mirroring on <scope>",
                "",
                "SOURCE/TARGET(S) (not used by \"disable\"; required for \"enable\")",
                "    source      The display which will be mirrored by the target(s); "
                "must be a single element of <SCOPE> (see below); cannot be \"all\"",
                "    target(s)   The display(s) which will mirror the source; "
                "must be an element of <SCOPE> (see below)",
                "",
                "SCOPE",
                "    main    The main display",
                "    ext<N>  External display number <N>",
                "    all (default scope for \"disable\")",
                "        For <enable>: all connected displays besides <source>; only available to <target>",
                "        For <disable>: all connected displays",
            ])}

        if self.subcommand in helpTypes:
            print(helpTypes[self.subcommand])
        else:
            print(helpTypes["usage"])

    def __handleShow(self):
        """
        Shows the user information about connected displays
        """
        for i, display in enumerate(self.scope):
            # Always print display identifier
            print("display \"{0}\":".format(display.tag))

            if self.subcommand == "current":
                current = display.currentMode
                print(current.bigString)

                if display.rotation is not None:
                    print("rotation:       {}".format(display.rotation))
                if display.brightness is not None:
                    print("brightness:     {:.2f}".format(display.brightness))
                if display.underscan is not None:
                    print("underscan:      {:.2f}".format(display.underscan))
                if display.mirrorSource is not None:
                    print("mirror of:      {}".format(display.mirrorSource.tag))

            elif self.subcommand == "default":
                default = display.defaultMode
                if default:
                    print(default.bigString)

            elif self.subcommand == "highest":
                highest = display.highestMode(self.hidpi)
                if highest:
                    print(highest.bigString)

            elif self.subcommand == "available":
                # Categorize modes by type, in order
                current = None
                default = None
                hidpi = []
                lodpi = []
                for mode in sorted(display.allModes, reverse=True):
                    if mode == display.currentMode:
                        current = mode
                    # Note: intentionally left "if" instead of "elif"; mode can be both current and default
                    if mode.isDefault:
                        default = mode
                    if mode.hidpi:
                        hidpi.append(mode)
                    if not mode.hidpi:
                        lodpi.append(mode)

                if current:
                    print("\n".join([
                        "    current mode:",
                        "        {}".format(current.littleString),
                    ]))

                if default:
                    print("\n".join([
                        "    default mode:",
                        "        {}".format(default.littleString),
                    ]))

                if hidpi:
                    print(
                        "    HiDPI modes:"
                    )
                    for mode in hidpi:
                        print(
                            "        {}".format(mode.littleString)
                        )

                if lodpi:
                    print(
                        "    non-HiDPI modes:"
                    )
                    for mode in lodpi:
                        print(
                            "        {}".format(mode.littleString)
                        )

            # Leave an empty line between displays
            if i < len(self.scope) - 1:
                print("")

    def __handleRes(self):
        """
        Sets the display to the correct DisplayMode.
        """
        for display in self.scope:
            if self.subcommand == "default":
                default = display.defaultMode
                display.setMode(default)

            elif self.subcommand == "highest":
                highest = display.highestMode(self.hidpi)
                display.setMode(highest)

            else:
                closest = display.closestMode(self.width, self.height, self.refresh, self.hidpi)
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
                target.setMirrorSource(source)

        elif self.subcommand == "disable":
            for target in self.scope:
                # If display is a mirror of another display, disable mirroring between them
                if target.mirrorSource is not None:
                    target.setMirrorSource(None)


class CommandList(object):
    """
    Holds one or more "Command" instances, and allows smart simultaneous execution
    """

    def __init__(self, commands=None):
        """
        :param commands: A single Command, a list of Commands, or a CommandList
        """
        # self.commands is a list that contains all the raw commands passed in to self.addCommand
        self.commands = []
        # self.commandDict will consist of displayID keys corresponding to commands for that display
        self.commandDict = {}

        if commands:
            if isinstance(commands, Command):
                self.addCommand(commands)
            elif isinstance(commands, list):
                for command in commands:
                    self.addCommand(command)
            elif isinstance(commands, CommandList):
                for command in commands.commands:
                    self.addCommand(command)

    # "Magic" methods

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return set(self.commands) == set(other.commands)
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return set(self.commands) != set(other.commands)
        else:
            return NotImplemented

    def __hash__(self):
        h = 0
        for command in self.commands:
            h = h | command.__str__()

        return hash(h)

    # Command interfacing

    def addCommand(self, command):
        """
        :param command: The Command to add to this CommandList
        """
        # Break "command" into each individual action it will perform
        # on each individual display in its scope, and add those actions
        # to commandDict, according to their associated display
        if command.scope:
            if len(command.scope) == len(getAllDisplays()):
                if "all" in self.commandDict:
                    self.commandDict["all"].append(command)
                else:
                    self.commandDict["all"] = [command]
            else:
                for display in command.scope:
                    if display.tag in self.commandDict:
                        self.commandDict[display.tag].append(command)
                    else:
                        self.commandDict[display.tag] = [command]
        # If there is no scope, there will be only one action.
        # In this case, we simply add the command to key "None".
        #   Note: this should only be possible with verb="help", since every
        #   other verb has a default scope
        else:
            if None in self.commandDict:
                self.commandDict[None].append(command)
            else:
                self.commandDict[None] = [command]

        self.commands.append(command)

    def run(self):
        """
        Runs all stored Commands in a non-interfering fashion
        """
        for displayTag in self.commandDict:
            # Commands for this particular display
            displayCommands = self.commandDict[displayTag]

            # Group commands by subcommand. Must preserve ordering to avoid interfering commands
            verbGroups = collections.OrderedDict([
                ("help", []),
                ("mirror", []),
                ("rotate", []),
                ("res", []),
                ("underscan", []),
                ("brightness", []),
                ("show", []),
            ])
            for command in displayCommands:
                verbGroups[command.verb].append(command)

            # Run commands by subcommand
            for verb in verbGroups:
                # Commands for this display, of this subcommand
                commands = verbGroups[verb]

                if len(commands) > 0:
                    # Multiple commands of these types will undo each other.
                    # As such, just run the most recently added command (the last in the list)
                    if (
                            verb == "help" or
                            verb == "rotate" or
                            verb == "res" or
                            verb == "brightness" or
                            verb == "underscan"
                    ):
                        try:
                            commands[-1].run()
                        except DisplayError as e:
                            raise CommandExecutionError(e.message, commands[-1])

                    # "show" commands don't interfere with each other, so run all of them
                    elif verb == "show":
                        for command in commands:
                            try:
                                command.run()
                            except DisplayError as e:
                                raise CommandExecutionError(e.message, command)

                    # "mirror" commands are the most complicated to deal with
                    elif verb == "mirror":
                        command = commands[-1]

                        if command.subcommand == "enable":
                            display = getDisplayFromTag(displayTag)
                            # The current Display that the above "display" is mirroring
                            currentMirror = display.mirrorSource
                            # Become a mirror of most recently requested display
                            mirrorDisplay = command.source

                            # If display is not a mirror of any other display
                            if currentMirror is None:
                                try:
                                    display.setMirrorSource(mirrorDisplay)
                                except DisplayError as e:
                                    raise CommandExecutionError(e.message, command)

                            # The user requested that this display mirror itself, or that it mirror a display
                            # which it is already mirroring. In either case, nothing should be done
                            elif display == currentMirror or currentMirror == mirrorDisplay:
                                pass

                            # display is already a mirror, but not of the requested display
                            else:
                                # First disable mirroring, then enable it for new mirror
                                display.setMirrorSource(None)
                                display.setMirrorSource(mirrorDisplay)
                                try:
                                    display.setMirrorSource(None)
                                    display.setMirrorSource(mirrorDisplay)
                                except DisplayError as e:
                                    raise CommandExecutionError(e.message, command)

                        elif command.subcommand == "disable":
                            try:
                                command.run()
                            except DisplayError as e:
                                raise CommandExecutionError(e.message, command)


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
        if externalNum > len(externals) - 1:
            # There aren't enough displays for this externalNumber to be valid
            raise CommandValueError("There is no display \"{}\"".format(displayTag))
        else:
            # 0 < externalNum < len(externals) - 1 means valid tag
            # ("0 < externalNum" known from re.match(r"^ext[0-9]+$") above)
            return externals[externalNum]

    # Note: no need for final "else" here, because getDisplayFromTag will only
    # be passed regex matches for "main|all|ext[0-9]+", because these are the only
    # arguments added to "scopeTags"


def getCommand(commandString):
    """
    Converts the commandString into a Command
    :param commandString: the string to convert
    :return: The Command represented by "commandString"
    """
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

    # Determine positionals (all remaining words)
    positionals = words

    attributesDict = {
        "verb": verb,
        "subcommand": None,
        "scope": None,
        "width": None,
        "height": None,
        "refresh": None,
        "hidpi": None,
        "angle": None,
        "brightness": None,
        "underscan": None,
        "source": None,
    }

    if verb == "help":
        if len(positionals) == 0:
            # Default (sub)command
            subcommand = "usage"
        elif len(positionals) == 1:
            if positionals[0] in ["help", "show", "res", "brightness", "rotate", "underscan", "mirror"]:
                subcommand = positionals[0]
            # Invalid (sub)command
            else:
                raise CommandValueError("\"{}\" is not a valid command".format(positionals[0]), verb=verb)
        # Too many arguments
        else:
            raise CommandSyntaxError("Help commands can only have one argument", verb=verb)

        attributesDict["subcommand"] = subcommand

    elif verb == "show":
        # Determine HiDPI settings
        hidpi = 0
        for positional in positionals:
            if positional == "no-hidpi":
                # If HiDPI hasn't been set to the contrary setting
                if hidpi != 2:
                    hidpi = 1  # doesn't match HiDPI
                    positionals.remove(positional)
                else:
                    raise CommandValueError("Cannot specify both \"no-hidpi\" and \"only-hidpi\"", verb=verb)
            elif positional == "only-hidpi":
                # If HiDPI hasn't been set to the contrary setting
                if hidpi != 1:
                    hidpi = 2  # only matches HiDPI
                    positionals.remove(positional)
                else:
                    raise CommandValueError("Cannot specify both \"no-hidpi\" and \"only-hidpi\"", verb=verb)

        if len(positionals) == 0:
            # Default subcommand
            subcommand = "current"
        elif len(positionals) == 1:
            if positionals[0] in ["current", "default", "highest", "available"]:
                subcommand = positionals[0]
            # Invalid subcommand
            else:
                raise CommandValueError("\"{}\" is not a valid subcommand".format(positionals[0]), verb=verb)
        # Too many arguments
        else:
            raise CommandSyntaxError("Show commands can only have one subcommand", verb=verb)

        # Determine scope
        if len(scopeTags) > 0:
            if "all" in scopeTags:
                scope = getAllDisplays()
            else:
                scope = []
                for scopeTag in scopeTags:
                    scope.append(getDisplayFromTag(scopeTag))
        else:
            # Default scope
            scope = getAllDisplays()

        attributesDict["subcommand"] = subcommand
        attributesDict["hidpi"] = hidpi
        attributesDict["scope"] = scope

    elif verb == "res":
        # Determine HiDPI settings
        hidpi = 0
        for positional in positionals:
            if positional == "no-hidpi":
                # If HiDPI hasn't been set to the contrary setting
                if hidpi != 2:
                    hidpi = 1  # doesn't match HiDPI
                    positionals.remove(positional)
                else:
                    raise CommandValueError("Cannot specify both \"no-hidpi\" and \'only-hidpi\"", verb=verb)
            elif positional == "only-hidpi":
                # If HiDPI hasn't been set to the contrary setting
                if hidpi != 1:
                    hidpi = 2  # only matches HiDPI
                    positionals.remove(positional)
                else:
                    raise CommandValueError("Cannot specify both \"no-hidpi\" and \'only-hidpi\"", verb=verb)

        if len(positionals) == 0:
            raise CommandSyntaxError("Res commands must specify a resolution", verb=verb)

        # case: "default"/"highest"
        elif len(positionals) == 1:
            if positionals[0] in ["default", "highest"]:
                subcommand = positionals[0]
            else:
                raise CommandValueError(
                    "Res commands must either specify both width and height or use the \"highest\" keyword",
                    verb=verb
                )

            attributesDict["subcommand"] = subcommand
            attributesDict["hidpi"] = hidpi

        # cases: ("default"/"highest", refresh) or (width, height)
        elif len(positionals) == 2:
            # case: ("default"/"highest", refresh)
            if positionals[0] in ["default", "highest"]:
                subcommand = positionals[0]
                try:
                    refresh = int(positionals[1])
                except ValueError:
                    raise CommandValueError("\"{}\" is not a valid refresh rate", verb=verb)
                if refresh < 0:
                    raise CommandValueError("Refresh rate must be positive", verb=verb)

                attributesDict["subcommand"] = subcommand
                attributesDict["refresh"] = refresh
                attributesDict["hidpi"] = hidpi

            # case: (width, height)
            else:
                # Try to parse positionals as integers
                wh = []
                for i in range(len(positionals)):
                    try:
                        wh.append(int(positionals[i]))
                    except ValueError:
                        wh.append(None)
                width, height = wh
                # Neither width nor height were integers (and thus invalid pixel counts)
                if width is None and height is None:
                    raise CommandValueError(
                        "Neither \"{}\" nor \"{}\" are valid widths or heights".format(
                            positionals[0], positionals[1]),
                        verb=verb
                    )
                # width was invalid
                elif width is None:
                    raise CommandValueError(
                        "\"{}\" is not a valid width".format(positionals[0]),
                        verb=verb
                    )
                # height was invalid
                elif height is None:
                    raise CommandValueError(
                        "\"{}\" is not a valid height".format(positionals[1]),
                        verb=verb
                    )
                # no negative dimensions
                if width < 0 or height < 0:
                    raise CommandValueError(
                        "Width and height must be positive",
                        verb=verb
                    )

                attributesDict["width"] = width
                attributesDict["height"] = height
                attributesDict["hidpi"] = hidpi

        # case: (width, height, refresh)
        elif len(positionals) == 3:
            # Try to parse width, height, and refresh as integers
            whr = []
            for i in range(len(positionals)):
                try:
                    whr.append(int(positionals[i]))
                except ValueError:
                    whr.append(None)
            width, height, refresh = whr
            # Nothing was an integer
            if width is None and height is None and refresh is None:
                raise CommandValueError(
                    "\"{}\"x\"{}\" is not a valid resolution, and \"{}\" is not a valid refresh rate".format(
                        positionals[0], positionals[1], positionals[2]),
                    verb=verb
                )
            # Neither width nor height were integers
            elif width is None or height is None:
                raise CommandValueError(
                    "\"{}\"x\"{}\" is not a valid resolution".format(
                        positionals[0], positionals[1]),
                    verb=verb
                )
            # refresh was not an integer
            elif refresh is None:
                raise CommandValueError(
                    "\"{}\" is not a valid refresh rate".format(positionals[2]),
                    verb=verb
                )
            # no negative dimensions or rate
            if width < 0 or height < 0 or refresh < 0:
                raise CommandValueError(
                    "Width, height, and refresh rate must be positive",
                    verb=verb
                )

            attributesDict["width"] = width
            attributesDict["height"] = height
            attributesDict["refresh"] = refresh
            attributesDict["hidpi"] = hidpi

        else:
            raise CommandSyntaxError(
                "Too many arguments supplied for the res command",
                verb=verb
            )

        # Determine scope
        if len(scopeTags) > 0:
            if "all" in scopeTags:
                scope = getAllDisplays()
            else:
                scope = []
                for scopeTag in scopeTags:
                    scope.append(getDisplayFromTag(scopeTag))
        else:
            # Default scope
            scope = getMainDisplay()
        attributesDict["scope"] = scope

    elif verb == "rotate":
        if len(positionals) == 0:
            raise CommandSyntaxError("Rotate commands must specify an angle", verb=verb)
        elif len(positionals) == 1:
            try:
                angle = int(positionals[0])
                # Rotation must be multiple of 90
                if angle % 90 != 0:
                    raise CommandValueError("\"{}\" is not a multiple of 90".format(positionals[0]), verb=verb)
            # Couldn't convert to int
            except ValueError:
                raise CommandValueError("\"{}\" is not a multiple of 90".format(positionals[0]), verb=verb)
        # Too many arguments
        else:
            raise CommandSyntaxError("Rotate commands can only have one argument", verb=verb)

        # Determine scope
        if len(scopeTags) > 0:
            if "all" in scopeTags:
                scope = getAllDisplays()
            else:
                scope = []
                for scopeTag in scopeTags:
                    scope.append(getDisplayFromTag(scopeTag))
        else:
            # Default scope
            scope = getMainDisplay()

        attributesDict["angle"] = angle
        attributesDict["scope"] = scope

    elif verb == "brightness":
        if len(positionals) == 0:
            raise CommandSyntaxError("Brightness commands must specify a brightness value", verb=verb)
        elif len(positionals) == 1:
            try:
                brightness = float(positionals[0])
                # Brightness must be between 0 and 1
                if brightness < 0 or brightness > 1:
                    raise CommandValueError(
                        "\"{}\" is not a number between 0 and 1 (inclusive)".format(positionals[0]),
                        verb=verb
                    )
            # Couldn't convert to float
            except ValueError:
                raise CommandValueError(
                    "\"{}\" is not a number between 0 and 1 (inclusive)".format(positionals[0]),
                    verb=verb
                )
        # Too many arguments
        else:
            raise CommandSyntaxError("Brightness commands can only have one argument", verb=verb)

        # Determine scope
        if len(scopeTags) > 0:
            if "all" in scopeTags:
                scope = getAllDisplays()
            else:
                scope = []
                for scopeTag in scopeTags:
                    scope.append(getDisplayFromTag(scopeTag))
        else:
            # Default scope
            scope = getMainDisplay()

        attributesDict["brightness"] = brightness
        attributesDict["scope"] = scope

    elif verb == "underscan":
        if len(positionals) == 0:
            raise CommandSyntaxError("Underscan commands must specify an underscan value", verb=verb)
        elif len(positionals) == 1:
            try:
                underscan = float(positionals[0])
                # Underscan must be between 0 and 1
                if underscan < 0 or underscan > 1:
                    raise CommandValueError(
                        "\"{}\" is not a number between 0 and 1 (inclusive)".format(positionals[0]),
                        verb=verb
                    )
            # Couldn't convert to float
            except ValueError:
                raise CommandValueError(
                    "\"{}\" is not a number between 0 and 1 (inclusive)".format(positionals[0]),
                    verb=verb
                )
        # Too many arguments
        else:
            raise CommandSyntaxError("underscan commands can only have one argument", verb=verb)

        # Determine scope
        if len(scopeTags) > 0:
            if "all" in scopeTags:
                scope = getAllDisplays()
            else:
                scope = []
                for scopeTag in scopeTags:
                    scope.append(getDisplayFromTag(scopeTag))
        else:
            # Default scope
            scope = getMainDisplay()

        attributesDict["underscan"] = underscan
        attributesDict["scope"] = scope

    elif verb == "mirror":
        if len(positionals) == 0:
            raise CommandSyntaxError("Mirror commands must specify a subcommand", verb=verb)
        # elif len(positionals) == 1:
        subcommand = positionals.pop(0)
        if subcommand == "enable":
            if len(positionals) == 0:
                if len(scopeTags) < 2:
                    raise CommandSyntaxError(
                        "Mirror enable commands require at least one source and one target display",
                        verb=verb
                    )
                else:
                    # For "enable" subcommand, first element in scope is source, and the rest are targets
                    # Since we parsed "scope" in reverse order, source will be last
                    source = getDisplayFromTag(scopeTags.pop(-1))
                    # Cannot mirror from more than one display
                    if isinstance(source, list):
                        if len(source) > 1:
                            raise CommandValueError(
                                "The source for mirror enable cannot be \"all\"",
                                verb=verb
                            )
                    # Determine target(s)
                    if "all" in scopeTags:
                        targets = getAllDisplays()
                    else:
                        targets = []
                        for scopeTag in scopeTags:
                            targets.append(getDisplayFromTag(scopeTag))

                attributesDict["subcommand"] = subcommand
                attributesDict["source"] = source
                attributesDict["scope"] = targets
            else:
                raise CommandValueError(
                    "\"{}\" is not a valid source or target".format(positionals[0]),
                    verb=verb
                )

        elif subcommand == "disable":
            if len(positionals) == 0:
                # Determine scope
                if len(scopeTags) > 0:
                    if "all" in scopeTags:
                        scope = getAllDisplays()
                    else:
                        scope = []
                        for scopeTag in scopeTags:
                            scope.append(getDisplayFromTag(scopeTag))
                else:
                    # Default scope
                    scope = getAllDisplays()

                attributesDict["subcommand"] = subcommand
                attributesDict["scope"] = scope
            else:
                raise CommandValueError(
                    "\"{}\" is not a valid scope".format(positionals[0]),
                    verb=verb
                )

        else:
            raise CommandValueError("\"{}\" is not a valid subcommand".format(subcommand), verb=verb)

    emptyKeys = [key for key in attributesDict if attributesDict[key] is None]
    for emptyKey in emptyKeys:
        attributesDict.pop(emptyKey)

    return Command(**attributesDict)


def parseCommands(commandStrings):
    """
    :param commandStrings: The string to get Commands from
    :return: Commands contained within the string
    """
    # Empty string
    if not commandStrings:
        raise CommandSyntaxError("An empty string is not a valid command")
    # Make sure all of the commands are in ASCII
    if not all(ord(c) < 128 for c in commandStrings):
        raise CommandSyntaxError("Commands cannot include non-ASCII characters")

    # The types of commands that can be issued
    verbPattern = r"help|show|res|brightness|rotate|underscan|mirror"
    # Pattern for finding multiple commands
    commandPattern = r"((?:{0}).*?)(?:(?: (?={0}))|\Z)".format(verbPattern)

    # Make sure the command starts with a valid verb
    firstWord = commandStrings.split()[0]
    firstWordMatch = re.match("^(" + verbPattern + ")$", firstWord)
    if not firstWordMatch:
        raise CommandSyntaxError("\"{}\" is not a valid type of command".format(firstWord), verb=firstWord)

    # Get all the individual commands
    if "help" not in commandStrings:
        commandStrings = re.findall(commandPattern, commandStrings)
    # Cannot run more than one command if one of them is a "help" command
    else:
        # The whole command will be interpreted as a single help command
        if firstWord == "help":
            commandStrings = [commandStrings]
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
                Command(verb="help", subcommand=e.verb).run()
            print("")
            print("Error in {} command:".format(e.verb))
            print(e.message)
        else:
            print("Error: {}".format(e.message))
        raise SystemExit()
    # Command successfully parsed
    else:
        try:
            commands.run()
        except CommandExecutionError as e:
            print("Error: {}".format(e.message))
            raise SystemExit()


if __name__ == "__main__":
    main()
