#!/usr/bin/python

# A collection of unittests for Display Manager's command-line interface

import unittest
from new_cli import *


class CommandTests(unittest.TestCase):

    # Helper methods

    # todo: this
    # def parsesTo(self, string, command):
    #     self.assertEqual(
    #         command,
    #         parseCommands(string).commands[0]
    #     )

    # todo: migrate both of these to "parsesTo"
    # Success tests

    def test_parseHelp(self):
        self.assertEqual(
            Command(verb="help", subcommand="usage"),
            parseCommands("help").commands[0]
        )
        self.assertEqual(
            Command(verb="help", subcommand="show"),
            parseCommands("help show").commands[0]
        )

    def test_parseShow(self):
        self.assertEqual(
            Command(verb="show", subcommand="current"),
            parseCommands("help").commands[0]
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
