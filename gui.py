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
# Graphical User Interface

import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as tkFileDialog
from display_manager import *


class App(object):
    """
    The GUI for the user to interact with.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Display Manager")

        self.mainFrame = ttk.Frame(self.root)

        # Set up the window
        self.mainFrame.grid(column=0, row=0)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.geometry("+400+200")

        # Raw GIF encoding
        self.logoPic = tk.PhotoImage(
            data="""
        R0lGODlhvAE8APcAAAAAAP///28HFZwAAp0ABfHX2J8AC96gpOKuseW1uLaXmezIyu/P0e/Q0vPe
        39nJysJXYcVfaIVCSMhmb895gJBWW9eMk9aLkdiPldeOlNiQltePldeQltqUmuOboZppbeGmq6R5
        feKrr+Sus+OtsuOusq2Ii7+kpsixs6EAEaAAD7AnN7MxP7Y4RnopMbk/TL9OWcRcZtODi9iPlteP
        ltC9v6IAE6IAFaIAFqEAFKEAE6wWK6sYLKsaLqwbLqwcL6MAGqMAGKkNJakQJ6kRKKsTKaoUKqoW
        K6sXLKwYLa0ZLvns7qUAHaQAG6cII6kOKPDq66gDIqcDIvz09hsZGnd1dv37/Onn6Hl4eXh3eP/+
        //j6+uzu7urs7Ojq6uPl5c3Pz/f4+PP09OXm5t3e3s/Q0HKBgN/h4JoAAJcAAAUDAwMCAgYFBQgH
        BwwLCw4NDSIgIBAPD+HV1RMSEhQTExYVFRkYGOjg4B4dHUVDQygnJyUkJFdVVTMyMi8uLisqKjw7
        Ozc2Nvj19YB+flNSUlJRUVBPT01MTEpJSUhHR0A/P/37+/Xz8+/t7efl5ePh4dTS0s3Ly8fFxaup
        qX9+fn18fHd2dnZ1dXV0dHRzc2xra2hnZ2ZlZWJhYV9eXlxbW1lYWP79/fn4+Pj39+jn5+fm5uXk
        5OTj497d3drZ2djX19bV1dDPz87Nzc3MzMnIyMjHx8fGxsPCwry7u7q5ubm4uLi3t7e2tra1tbW0
        tLSzs7Cvr6yrq6inp6OioqGgoJ+enp2cnJuampWUlJSTk4yLi4mIiIeGhoWEhISDg/7+/v39/fv7
        +/f39/b29vX19fT09PPz8/Dw8O/v7+7u7uzs7Ovr6+np6ePj4+Hh4d/f397e3t3d3dvb29ra2tnZ
        2dbW1tXV1dLS0tDQ0M7OzsvLy8TExMPDw8HBwb+/v76+vrKysq6urqysrKurq6ioqKWlpZmZmZeX
        l5GRkY6OjoqKioGBgXt7e3JycnBwcG5ubmpqamNjYwkJCQEBAf///yH5BAEAAP8ALAAAAAC8ATwA
        AAj/AAMIHEiwoMGDCBMqXMiwocOHECNKnEixosWLGDNq3Mixo8ePIEOKHEmypMmTKFOqXMmypcuX
        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
        """
        )
        self.imageLabel = ttk.Label(self.mainFrame, image=self.logoPic)
        self.imageLabel.grid(column=0, row=0, columnspan=8)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=9, columnspan=8, sticky=tk.EW)

        # Display selection
        ttk.Label(self.mainFrame, text="Display:").grid(column=0, row=10, sticky=tk.E)
        self.displayDict = {}
        self.displayDropdown = ttk.Combobox(self.mainFrame, width=32, state="readonly")
        self.displayDropdown.grid(column=1, row=10, columnspan=6, sticky=tk.EW)
        ttk.Button(self.mainFrame, text="Refresh", command=self.__reloadDisplay).grid(column=7, row=10, sticky=tk.E)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=19, columnspan=8, sticky=tk.EW)

        # Mode selection
        ttk.Label(self.mainFrame, text="Resolution:").grid(column=0, row=20, sticky=tk.E)
        self.modeDict = {}
        self.modeDropdown = ttk.Combobox(self.mainFrame, width=64, state="readonly")
        self.modeDropdown.grid(column=1, row=20, columnspan=7, sticky=tk.EW)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=29, columnspan=8, sticky=tk.EW)

        # Rotate menu
        ttk.Label(self.mainFrame, text="Rotate:").grid(column=0, row=30, sticky=tk.E)
        self.rotateSlider = tk.Scale(self.mainFrame, orient=tk.HORIZONTAL, width=32, from_=0, to=270, resolution=90)
        self.rotateSlider.grid(column=1, row=30, columnspan=7, sticky=tk.EW)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=39, columnspan=8, sticky=tk.EW)

        # Brightness menu
        ttk.Label(self.mainFrame, text="Brightness:").grid(column=0, row=40, sticky=tk.E)
        self.brightnessSlider = tk.Scale(self.mainFrame, orient=tk.HORIZONTAL, width=32, from_=0, to=100)
        self.brightnessSlider.grid(column=1, row=40, columnspan=7, sticky=tk.EW)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=49, columnspan=8, sticky=tk.EW)

        # Underscan menu
        ttk.Label(self.mainFrame, text="Underscan:").grid(column=0, row=50, sticky=tk.E)
        self.underscanSlider = tk.Scale(self.mainFrame, orient=tk.HORIZONTAL, width=32, from_=0, to=100)
        self.underscanSlider.grid(column=1, row=50, columnspan=7, sticky=tk.EW)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=59, columnspan=8, sticky=tk.EW)

        # Mirroring menu
        ttk.Label(self.mainFrame, text="Mirror Display:").grid(column=0, row=60, sticky=tk.E)
        self.mirrorEnabled = tk.BooleanVar()
        self.mirrorEnabled.set(False)
        self.mirrorDropdown = ttk.Combobox(self.mainFrame, width=32, state="readonly")
        self.mirrorDropdown.grid(column=1, row=60, columnspan=6, sticky=tk.EW)
        self.mirrorCheckbox = ttk.Checkbutton(self.mainFrame, text="Enable", variable=self.mirrorEnabled)
        self.mirrorCheckbox.grid(column=7, row=60, sticky=tk.E)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=69, columnspan=8, sticky=tk.EW)

        # Set/build script menu
        ttk.Button(self.mainFrame, text="Set Display", command=self.setDisplay).grid(column=0, row=70, sticky=tk.E)
        ttk.Button(self.mainFrame, text="Build Script", command=self.buildScript).grid(column=7, row=70, sticky=tk.E)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=79, columnspan=8, sticky=tk.EW)

    def __displaySelectionInit(self):
        """
        Add all connected displays to self.displayDropdown.
        """
        displayStrings = []
        for display in getAllDisplays():
            displayID = str(display.displayID)
            self.displayDict[displayID] = display
            displayStrings.append(displayID + " (Main Display)" if display.isMain else displayID)

        self.displayDropdown["values"] = displayStrings
        self.displayDropdown.current(0)
        self.displayDropdown.bind("<<ComboboxSelected>>", lambda event: self.__reloadDisplay())

    def __modeSelectionInit(self):
        """
        Add all the DisplayModes of the currently selected display to self.modeDropdown.
        """
        # Add self.display's DisplayModes to self.modeDropdown in reverse sorted order
        sortedModeStrings = []
        for mode in sorted(self.display.allModes, reverse=True):
            modeString = mode.__str__()
            self.modeDict[modeString] = mode
            sortedModeStrings.append(modeString)
        self.modeDropdown["values"] = sortedModeStrings

        # Set the default mode to the current mode, if possible
        currentModeString = self.display.currentMode.__str__()
        if currentModeString in self.modeDropdown["values"]:
            self.modeDropdown.current(self.modeDropdown["values"].index(currentModeString))
        else:
            self.modeDropdown.current(0)

    def __rotateSelectionInit(self):
        """
        Set self.rotateSlider's value to that of the currently selected display, and
        deactivates said slider if the rotation of this display can't be set.
        """
        if self.display.rotation is not None:
            rotation = self.display.rotation
            self.rotateSlider.set(rotation)
            self.rotateSlider.configure(state=tk.NORMAL)
        else:
            self.rotateSlider.set(0)
            self.rotateSlider.configure(state=tk.DISABLED)

    def __brightnessSelectionInit(self):
        """
        Set self.brightnessSlider's value to that of the currently selected display, and
        deactivates said slider if the brightness of this display can't be set.
        """
        if self.display.brightness is not None:
            brightness = self.display.brightness * 100
            self.brightnessSlider.set(brightness)
            self.brightnessSlider.configure(state=tk.NORMAL)
        else:
            self.brightnessSlider.set(0.0)
            self.brightnessSlider.configure(state=tk.DISABLED)

    def __underscanSelectionInit(self):
        """
        Sets self.underscanSlider's value to that of the currently selected display, and
        deactivates said slider if the underscan of this display can't be set.
        """
        if self.display.underscan is not None:
            underscan = abs(self.display.underscan - 1) * 100
            self.underscanSlider.set(underscan)
            self.underscanSlider.configure(state=tk.NORMAL)
        else:
            self.underscanSlider.set(0.0)
            self.underscanSlider.configure(state=tk.DISABLED)

    def __mirrorSelectionInit(self):
        """
        Show the other available displays to mirror.
        """
        otherDisplayIDs = []
        for display in self.displayDict.values():
            displayID = str(display.displayID)
            if displayID != str(self.display.displayID):
                otherDisplayIDs.append(displayID + " (Main Display)" if display.isMain else displayID)

        if otherDisplayIDs:  # if there are other displays to mirror
            self.mirrorDropdown["values"] = otherDisplayIDs
            self.mirrorDropdown.current(0)
        else:  # there is only one display
            self.mirrorDropdown["values"] = ["None"]
            self.mirrorDropdown.current(0)
            self.mirrorEnabled.set(False)
            self.mirrorDropdown.configure(state=tk.DISABLED)
            self.mirrorCheckbox.configure(state=tk.DISABLED)

    @property
    def display(self):
        """
        :return: The currently selected Display.
        """
        displayID = re.search(r"^[0-9]*", self.displayDropdown.get()).group()
        return self.displayDict[displayID]

    @property
    def mode(self):
        """
        :return: The currently selected DisplayMode.
        """
        modeString = self.modeDropdown.get()
        return self.modeDict[modeString]

    @property
    def rotation(self):
        """
        :return: The currently selected brightness.
        """
        if self.rotateSlider.get():
            return int(self.rotateSlider.get())
        else:
            return 0

    @property
    def brightness(self):
        """
        :return: The currently selected brightness.
        """
        if self.brightnessSlider.get():
            return float(self.brightnessSlider.get()) / 100
        else:
            return 0

    @property
    def underscan(self):
        """
        :return: The currently selected underscan.
        """
        if self.underscanSlider.get():
            return float(self.underscanSlider.get() / 100)
        else:
            return 0

    @property
    def mirror(self):
        """
        :return: The currently selected display to mirror.
        """
        if "None" not in self.mirrorDropdown["values"]:
            mirrorID = re.search(r"^[0-9]*", self.mirrorDropdown.get()).group()
            return self.displayDict[mirrorID]
        else:
            return None

    def setDisplay(self):
        """
        Set the Display to the currently selected settings.
        """
        self.__generateCommands().run()
        self.__reloadDisplay()

    def buildScript(self):
        """
        Build a script with the currently selected settings and save it where
        the user specifies.
        """
        # Ask the user where to store the file
        f = tkFileDialog.asksaveasfile(
            mode='w',
            initialdir=os.getcwd(),
            defaultextension='.sh',
            initialfile="set",
        )
        if f is not None:  # if the user didn't cancel
            f.write("#!/bin/sh\n\ndisplay_manager.py")
            for command in self.__generateCommands().commands:
                f.write(" " + command.__str__())
            f.close()

    def __generateCommands(self):
        """
        :return: A CommandList with all the currently selected commands
        """
        # These commands are always available
        commands = [
            Command(
                verb="res",
                width=self.mode.width,
                height=self.mode.height,
                refresh=self.mode.refresh,
                scope=self.display,
            ),
            Command(
                verb="mirror",
                subcommand="enable" if self.mirrorEnabled.get() else "disable",
                source=self.mirror if self.mirrorEnabled.get() else None,
                scope=self.display,
            ),
        ]

        # Add these commands if and only if they're available to this Display
        rotate = Command(
            verb="rotate",
            angle=self.rotation,
            scope=self.display,
        )
        brightness = Command(
            verb="brightness",
            brightness=self.brightness,
            scope=self.display,
        )
        underscan = Command(
            verb="underscan",
            underscan=self.underscan,
            scope=self.display,
        )
        if self.display.rotation is not None:
            commands.append(rotate)
        if self.display.brightness is not None:
            commands.append(brightness)
        if self.display.underscan is not None:
            commands.append(underscan)

        return CommandList(commands)

    def __reloadDisplay(self):
        """
        Reloads data-containing elements.
        """
        self.__modeSelectionInit()
        self.__rotateSelectionInit()
        self.__brightnessSelectionInit()
        self.__mirrorSelectionInit()
        self.__underscanSelectionInit()

        self.mirrorEnabled.set(False)  # resets every time the display is switched

    def start(self):
        """
        Open the GUI.
        """
        self.__displaySelectionInit()
        self.__reloadDisplay()

        self.root.mainloop()


def main():
    view = App()
    view.start()


if __name__ == "__main__":
    main()
