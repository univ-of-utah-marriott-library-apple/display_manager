#!/usr/bin/python

# A collection of unittests for Display Manager's command-line interface

import unittest
from new_cli import *


class CommandTests(unittest.TestCase):

    # Helper methods

    def assertParse(self, tuples):
        """
        Asserts that the string in each tuple parses to the Command or CommandList
        :param tuples: A list of tuples of a single Command/CommandList and a string
            [(CommandList1, string1), (CommandList2, string2), ...]
        """
        for t in tuples:
            commands = t[0]
            string = t[1]

            # Make sure everything is the right type to begin with
            self.assertIsInstance(commands, CommandList)
            self.assertIsInstance(string, str)

            # todo: remove and uncomment next
            temp = parseCommands(string)
            self.assertEqual(commands, temp)

            # Do the actual checking
            # self.assertEqual(commands, parseCommands(string))

    # Success tests

    def test_parseHelp(self):
        self.assertParse(
            [
                (
                    CommandList([Command(verb="help", subcommand="usage")]),
                    "help"
                ),
                (
                    CommandList([Command(verb="help", subcommand="help")]),
                    "help help"
                ),
                (
                    CommandList([Command(verb="help", subcommand="show")]),
                    "help show"
                ),
                (
                    CommandList([Command(verb="help", subcommand="res")]),
                    "help res"
                ),
                (
                    CommandList([Command(verb="help", subcommand="rotate")]),
                    "help rotate"
                ),
                (
                    CommandList([Command(verb="help", subcommand="brightness")]),
                    "help brightness"
                ),
                (
                    CommandList([Command(verb="help", subcommand="underscan")]),
                    "help underscan"
                ),
                (
                    CommandList([Command(verb="help", subcommand="mirror")]),
                    "help mirror"
                ),
            ]
        )

    def test_parseShow(self):
        self.assertParse(
            [
                # Subcommands
                (
                    CommandList([
                        Command(verb="show", subcommand="current"),  # default
                        Command(verb="show", subcommand="current"),
                        Command(verb="show", subcommand="highest"),
                        Command(verb="show", subcommand="available"),
                    ]),
                    "show show current show highest show available"
                ),
                # Parameters (HiDPI)
                (
                    CommandList([
                        Command(verb="show", hidpi=0),  # match all (default)
                        Command(verb="show", hidpi=1),  # mach only non-HiDPI
                        Command(verb="show", hidpi=2),  # match only HiDPI
                    ]),
                    "show show no-hidpi show only-hidpi"
                ),
                # Scopes
                (
                    CommandList([
                        Command(verb="show", scope=getMainDisplay()),  # default
                        Command(verb="show", scope=getMainDisplay()),
                        # NOTE: THIS NEXT COMMAND WILL FAIL IF NO EXTERNAL DISPLAYS ARE CONNECTED
                        Command(verb="show", scope=getDisplayFromTag("ext0")),
                        Command(verb="show", scope=getAllDisplays()),
                    ]),
                    "show show main show ext0 show all"
                ),
            ]
        )

    # Error tests

    def test_raiseCommandSyntaxError(self):
        makeFail = [
            # Empty string
            "",

            # Invalid verbs
            "bad",
            "there is no command here",

            # Non-ASCII characters
            u"\u00a7",  # section symbol
            u"list \u00ac",  # negation symbol

            # Too few arguments
            "res",
            "rotate",
            "brightness",
            "underscan",
            "mirror",
            "mirror enable",
            "mirror enable main",

            # Too many arguments
            "help show res",
            "show current highest",
            "res 1920 1080 0 0",
            "rotate 0 0",
            "brightness .35 .35",
            "underscan .7 .7",

            # If help is a command, it must be the ONLY command
            # Justification: given "help show", one might want either:
            #   1: "help (usage)" and "show (current)"
            #   2: "help show"
            # There are many such scenarios, and all cannot be accounted for in a reasonable way.
            "show help",

            # Scope must be at end of command
            "show main current",
        ]

        for fail in makeFail:
            self.assertRaises(CommandSyntaxError, parseCommands, fail)

    def test_raiseCommandValueError(self):
        makeFail = [
            "show bad",

            # Can't have it both ways
            "show no-hidpi only-hidpi",
            "show only-hidpi no-hidpi",
            "res no-hidpi only-hidpi",
            "res only-hidpi no-hidpi",

            "res bad",
            "res highest bad",
            "res highest -1",
            "res bad bad",
            "res 1920 bad",
            "res bad 1080",
            "res -1 -1",
            "res 1920 -1",
            "res -1 1080",
            "res 1920 1080 bad",
            "res 1920 bad 0",
            "res bad 1080 0",
            "res 1920 1080 -1",
            "res 1920 -1 0",
            "res -1 1080 0",

            "rotate 89",
            "rotate bad",

            "brightness -1",
            "brightness 1.1",
            "brightness bad",

            "underscan -1",
            "underscan 1.1",
            "underscan bad",

            "mirror bad",
            "mirror enable bad",
            "mirror disable bad",
            "mirror enable bad main",

            "show current res 1 1 rotate 90 brightness .5 underscan 0 mirror bad",

            "show ext" + str(len(getAllDisplays()) + 6),
        ]

        for fail in makeFail:
            self.assertRaises(CommandValueError, parseCommands, fail)


if __name__ == "__main__":
    unittest.main()
