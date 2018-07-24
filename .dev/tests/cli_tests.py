#!/usr/bin/python

# A collection of unittests for Display Manager's command-line interface

import unittest
from new_cli import *


class ParseCommandsTests(unittest.TestCase):

    ########
    # Designed to fail

    ####
    # Raise CommandSyntaxError
    def test_emptyString(self):
        with self.assertRaises(CommandSyntaxError):
            parseCommands("")

    def test_noCommand(self):
        with self.assertRaises(CommandSyntaxError):
            parseCommands("there is no command here")

    def test_specialCharacters1(self):
        with self.assertRaises(CommandSyntaxError):
            parseCommands(u"¬")

    def test_specialCharacters2(self):
        with self.assertRaises(CommandSyntaxError):
            parseCommands(u"list ¬")

    def test_notEnoughArgs(self):
        with self.assertRaises(CommandSyntaxError):
            parseCommands("res 1920")

    def test_tooManyArgs(self):
        with self.assertRaises(CommandSyntaxError):
            parseCommands("rotate 90 0")

    def test_badFlags(self):
        with self.assertRaises(CommandSyntaxError):
            parseCommands("list -a")

    ####
    # Raise CommandValueError
    def test_invalidList1(self):
        with self.assertRaises(CommandValueError):
            parseCommands("list bad")

    def test_invalidResolution1(self):
        with self.assertRaises(CommandValueError):
            parseCommands("res bad")

    # todo: more invalid resolutions

    def test_invalidBrightness1(self):
        with self.assertRaises(CommandValueError):
            parseCommands("brightness bad")

    def test_invalidBrightness2(self):
        with self.assertRaises(CommandValueError):
            parseCommands("brightness -1")

    def test_invalidBrightness3(self):
        with self.assertRaises(CommandValueError):
            parseCommands("brightness 1.1")

    def test_invalidRotation1(self):
        with self.assertRaises(CommandValueError):
            parseCommands("rotate bad")

    def test_invalidRotation2(self):
        with self.assertRaises(CommandValueError):
            parseCommands("rotate 89")

    def test_invalidUnderscan1(self):
        with self.assertRaises(CommandValueError):
            parseCommands("underscan bad")

    def test_invalidUnderscan2(self):
        with self.assertRaises(CommandValueError):
            parseCommands("underscan -1")

    def test_invalidUnderscan3(self):
        with self.assertRaises(CommandValueError):
            parseCommands("underscan 1.1")

    def test_invalidMirror1(self):
        with self.assertRaises(CommandValueError):
            parseCommands("mirror bad main")

    def test_invalidMirror2(self):
        with self.assertRaises(CommandValueError):
            parseCommands("mirror main bad")

    def test_invalidBig(self):
        with self.assertRaises(CommandSyntaxError):
            parseCommands("list current res 1 1 rotate 90 brightness .5 underscan 0 mirror bad")

    ######
    # Designed to succeed

    # todo: these


if __name__ == "__main__":
    unittest.main()
