#!/usr/bin/python

# A collection of unittests for Display Manager's command-line interface

import unittest
from display_manager import *


class ParseTests(unittest.TestCase):

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

            # Do the actual checking
            self.assertEqual(commands, parseCommands(string))

    # Success tests

    def test_parseHelp(self):
        self.assertParse([
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
        ])

    def test_parseShow(self):
        self.assertParse([
            # Subcommands
            (
                CommandList([
                    Command(verb="show", subcommand="current", hidpi=0, scope=getAllDisplays()),  # default
                    Command(verb="show", subcommand="current", hidpi=0, scope=getAllDisplays()),
                    Command(verb="show", subcommand="highest", hidpi=0, scope=getAllDisplays()),
                    Command(verb="show", subcommand="available", hidpi=0, scope=getAllDisplays()),
                ]),
                "show show current show highest show available"
            ),
            # Options (HiDPI)
            (
                CommandList([
                    # match all (default)
                    Command(verb="show", subcommand="current", hidpi=0, scope=getAllDisplays()),
                    # mach only non-HiDPI
                    Command(verb="show", subcommand="current", hidpi=1, scope=getAllDisplays()),
                    # match only HiDPI
                    Command(verb="show", subcommand="current", hidpi=2, scope=getAllDisplays()),
                ]),
                "show show no-hidpi show only-hidpi"
            ),
            # Scopes
            (
                CommandList([
                    Command(verb="show", subcommand="current", hidpi=0, scope=getAllDisplays()),  # default
                    Command(verb="show", subcommand="current", hidpi=0, scope=getAllDisplays()),
                    Command(verb="show", subcommand="current", hidpi=0, scope=getMainDisplay()),
                    # NOTE: THIS NEXT COMMAND WILL FAIL IF NO EXTERNAL DISPLAYS ARE CONNECTED
                    Command(verb="show", subcommand="current", hidpi=0, scope=getDisplayFromTag("ext0")),
                ]),
                "show show all show main show ext0"
            ),
        ])

    def test_parseRes(self):
        self.assertParse([
            # case "highest"
            (
                CommandList([
                    # Scopes
                    Command(verb="res", subcommand="highest", hidpi=0, scope=getMainDisplay()),
                    Command(verb="res", subcommand="highest", hidpi=0, scope=getMainDisplay()),
                    # NOTE: THIS NEXT COMMAND WILL FAIL IF NO EXTERNAL DISPLAYS ARE CONNECTED
                    Command(verb="res", subcommand="highest", hidpi=0, scope=getDisplayFromTag("ext0")),
                    Command(verb="res", subcommand="highest", hidpi=0, scope=getAllDisplays()),

                    # HiDPI options
                    Command(verb="res", subcommand="highest", hidpi=1, scope=getMainDisplay()),
                    Command(verb="res", subcommand="highest", hidpi=2, scope=getMainDisplay()),
                ]),
                "res highest res highest main res highest ext0 res highest all "    # scopes
                "res highest no-hidpi res highest only-hidpi"                       # HiDPI options
            ),
            # case ("highest", refresh)
            (
                CommandList([
                    # Scopes
                    Command(verb="res", subcommand="highest", refresh=1, hidpi=0, scope=getMainDisplay()),
                    Command(verb="res", subcommand="highest", refresh=2, hidpi=0, scope=getMainDisplay()),
                    # NOTE: THIS NEXT COMMAND WILL FAIL IF NO EXTERNAL DISPLAYS ARE CONNECTED
                    Command(verb="res", subcommand="highest", refresh=3, hidpi=0, scope=getDisplayFromTag("ext0")),
                    Command(verb="res", subcommand="highest", refresh=4, hidpi=0, scope=getAllDisplays()),

                    # HiDPI options
                    Command(verb="res", subcommand="highest", refresh=5, hidpi=1, scope=getMainDisplay()),
                    Command(verb="res", subcommand="highest", refresh=6, hidpi=2, scope=getMainDisplay()),
                ]),
                "res highest 1 res highest 2 main res highest 3 ext0 res highest 4 all "    # scopes
                "res highest 5 no-hidpi res highest 6 only-hidpi"                           # HiDPI options
            ),
            # case (width, height)
            (
                CommandList([
                    # Scopes
                    Command(verb="res", width=1, height=2, hidpi=0, scope=getMainDisplay()),
                    Command(verb="res", width=3, height=4, hidpi=0, scope=getMainDisplay()),
                    # NOTE: THIS NEXT COMMAND WILL FAIL IF NO EXTERNAL DISPLAYS ARE CONNECTED
                    Command(verb="res", width=5, height=6, hidpi=0, scope=getDisplayFromTag("ext0")),
                    Command(verb="res", width=7, height=8, hidpi=0, scope=getAllDisplays()),

                    # HiDPI options
                    Command(verb="res", width=10, height=11, hidpi=1, scope=getMainDisplay()),
                    Command(verb="res", width=12, height=13, hidpi=2, scope=getMainDisplay()),
                ]),
                "res 1 2 res 3 4 main res 5 6 ext0 res 7 8 all "    # scopes
                "res 10 11 no-hidpi res 12 13 only-hidpi"           # HiDPI options
            ),
            # case (width, height, refresh)
            (
                CommandList([
                    # Scopes
                    Command(verb="res", width=1, height=2, refresh=3, hidpi=0, scope=getMainDisplay()),
                    Command(verb="res", width=4, height=5, refresh=6, hidpi=0, scope=getMainDisplay()),
                    # NOTE: THIS NEXT COMMAND WILL FAIL IF NO EXTERNAL DISPLAYS ARE CONNECTED
                    Command(verb="res", width=7, height=8, refresh=9, hidpi=0, scope=getDisplayFromTag("ext0")),
                    Command(verb="res", width=10, height=11, refresh=12, hidpi=0, scope=getAllDisplays()),

                    # HiDPI options
                    Command(verb="res", width=13, height=14, refresh=15, hidpi=1, scope=getMainDisplay()),
                    Command(verb="res", width=16, height=17, refresh=18, hidpi=2, scope=getMainDisplay()),
                ]),
                "res 1 2 3 res 4 5 6 main res 7 8 9 ext0 res 10 11 12 all "     # scopes
                "res 13 14 15 no-hidpi res 16 17 18 only-hidpi"                 # HiDPI options
            ),
        ])

    def test_parseRotate(self):
        self.assertParse([
            # Scopes
            (
                CommandList([
                    Command(verb="rotate", angle=0, scope=getMainDisplay()),
                    Command(verb="rotate", angle=90, scope=getMainDisplay()),
                    # NOTE: THIS NEXT COMMAND WILL FAIL IF NO EXTERNAL DISPLAYS ARE CONNECTED
                    Command(verb="rotate", angle=180, scope=getDisplayFromTag("ext0")),
                    Command(verb="rotate", angle=270, scope=getAllDisplays())
                ]),
                "rotate 0 rotate 90 main rotate 180 ext0 rotate 270 all"
            ),
        ])

    def test_parseBrightness(self):
        self.assertParse([
            # Scopes
            (
                CommandList([
                    Command(verb="brightness", brightness=0, scope=getMainDisplay()),
                    Command(verb="brightness", brightness=.33, scope=getMainDisplay()),
                    # NOTE: THIS NEXT COMMAND WILL FAIL IF NO EXTERNAL DISPLAYS ARE CONNECTED
                    Command(verb="brightness", brightness=.67, scope=getDisplayFromTag("ext0")),
                    Command(verb="brightness", brightness=1, scope=getAllDisplays())
                ]),
                "brightness 0 brightness .33 main brightness .67 ext0 brightness 1 all"
            ),
        ])

    def test_parseUnderscan(self):
        self.assertParse([
            # Scopes
            (
                CommandList([
                    Command(verb="underscan", underscan=0, scope=getMainDisplay()),
                    Command(verb="underscan", underscan=.33, scope=getMainDisplay()),
                    # NOTE: THIS NEXT COMMAND WILL FAIL IF NO EXTERNAL DISPLAYS ARE CONNECTED
                    Command(verb="underscan", underscan=.67, scope=getDisplayFromTag("ext0")),
                    Command(verb="underscan", underscan=1, scope=getAllDisplays())
                ]),
                "underscan 0 underscan .33 main underscan .67 ext0 underscan 1 all"
            ),
        ])

    def test_parseMirror(self):
        # NOTE: THESE COMMANDS WILL FAIL IF NO EXTERNAL DISPLAYS ARE CONNECTED
        self.assertParse([
            # Enable
            (
                CommandList([
                    # Single target
                    Command(verb="mirror", subcommand="enable", source=getMainDisplay(),
                            scope=getDisplayFromTag("ext0")),
                    Command(verb="mirror", subcommand="enable", source=getDisplayFromTag("ext0"),
                            scope=getMainDisplay()),

                    # Multiple targets
                    Command(verb="mirror", subcommand="enable", source=getMainDisplay(),
                            scope=[getDisplayFromTag("ext0"), getDisplayFromTag("ext1")]),
                    Command(verb="mirror", subcommand="enable", source=getDisplayFromTag("ext0"),
                            scope=[getMainDisplay(), getDisplayFromTag("ext1")]),

                    # Target "all"
                    Command(verb="mirror", subcommand="enable", source=getMainDisplay(),
                            scope=getAllDisplays()),
                    Command(verb="mirror", subcommand="enable", source=getDisplayFromTag("ext0"),
                            scope=getAllDisplays()),
                ]),
                "mirror enable main ext0 mirror enable ext0 main "
                "mirror enable main ext0 ext1 mirror enable ext0 main ext1 "
                "mirror enable main all mirror enable ext0 all"
            ),
            # Disable
            (
                CommandList([
                    Command(verb="mirror", subcommand="disable", scope=getAllDisplays()),  # default
                    Command(verb="mirror", subcommand="disable", scope=getAllDisplays()),
                    Command(verb="mirror", subcommand="disable", scope=getMainDisplay()),
                    Command(verb="mirror", subcommand="disable", scope=getDisplayFromTag("ext0")),
                ]),
                "mirror disable mirror disable all mirror disable main mirror disable ext0"
            ),
        ])

    # todo: stress tests

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
            "mirror enable all main",

            "show current res 1 1 rotate 90 brightness .5 underscan 0 mirror bad",

            "show ext" + str(len(getAllDisplays()) + 6),
        ]

        for fail in makeFail:
            self.assertRaises(CommandValueError, parseCommands, fail)


class TestDisplay(Display):

    def __init__(self, displayID):
        self.displayID = displayID

        self.__currentMode = None
        self.__rotation = None
        self.__brightness = None
        self.__underscan = None
        self.__mirrorOf = None

    @property
    def isMain(self):
        return self.displayID == 0

    @property
    def tag(self):
        return "main"

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

    @property
    def currentMode(self):
        return self.__currentMode

    def allModes(self, hidpi=0):
        if self.currentMode:
            if self.__rightHidpi(self.currentMode, hidpi):
                return self.currentMode
            else:
                return None

    def highestMode(self, hidpi=0):
        if self.currentMode:
            if self.__rightHidpi(self.currentMode, hidpi):
                return self.currentMode
            else:
                return None

    def closestMode(self, width, height, refresh=0, hidpi=0):
        if (
            self.currentMode.width == width and
            self.currentMode.height == height and
            self.currentMode.refresh == refresh and
            self.__rightHidpi(self.currentMode, hidpi)
        ):
            return self.currentMode
        else:
            return None

    def setMode(self, mode):
        self.__currentMode = mode

    @property
    def rotation(self):
        return self.__rotation

    def setRotate(self, angle):
        self.__rotation = angle

    @property
    def brightness(self):
        return self.__brightness

    def setBrightness(self, brightness):
        self.__brightness = brightness

    @property
    def underscan(self):
        return self.__underscan

    def setUnderscan(self, underscan):
        self.__underscan = underscan

    @property
    def mirrorOf(self):
        return self.__mirrorOf

    def setMirrorOf(self, mirrorDisplay):
        self.__mirrorOf = mirrorDisplay


class TestDisplayMode(DisplayMode):

    def __init__(self, **kwargs):
        self.width = kwargs["width"] if kwargs["width"] else None
        self.height = kwargs["height"] if kwargs["height"] else None
        self.refresh = kwargs["refresh"] if kwargs["refresh"] else None
        self.hidpi = kwargs["hidpi"] if kwargs["hidpi"] else None


class CommandTests(unittest.TestCase):

    def test_res(self):
        d = []
        mode = TestDisplayMode(width=1, height=2, refresh=3, hidpi=False)
        for i in range(3):
            d.append(TestDisplay(0))
            self.assertIs(d[i].currentMode, None)
            mode.hidpi = i % 2 == 0  # even displays hidpi=True; odd opposite
            d[i].setMode(mode)
        Command(verb="res", subcommand="highest", hidpi=2, scope=d).run()
        self.assertEqual(d[0].currentMode, mode)
        self.assertEqual(d[1].currentMode, None)
        self.assertEqual(d[2].currentMode, mode)

    def test_brightness(self):
        d = []
        for i in range(3):
            d.append(TestDisplay(0))
            self.assertIs(d[i].brightness, None)
        CommandList([
            Command(verb="brightness", brightness=.35, scope=d[:2]),
            Command(verb="brightness", brightness=.2, scope=d[2]),
        ]).run()
        self.assertEqual(d[0].brightness, .35)
        self.assertEqual(d[1].brightness, .35)
        self.assertEqual(d[2].brightness, .2)


if __name__ == "__main__":
    # todo: uncomment or remove
    # unittest.main()

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CommandTests)
    unittest.TextTestRunner().run(suite)
