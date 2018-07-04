#!/usr/bin/python

# A GUI that allows users to interface with Display Manager


from __future__ import print_function
import Tkinter as tk
import ttk
import sys
import re
sys.path.append("..")  # to allow import from current directory
import DisplayManager as dm
import configWriter as cg


class App(object):
    """
    The GUI for the user to interact with.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Display Manager 1.0.0")

        self.mainFrame = ttk.Frame(self.root)

        # self.normalStyle = ttk.Style()
        # self.normalStyle.configure("Normal.TLabel", foreground="black")
        #
        # self.highlightStyle = ttk.Style()
        # self.highlightStyle.configure("Highlight.TLabel", foreground="blue")

        # todo: put something in column, row 0
        # Set up the window
        self.mainFrame.grid(column=0, row=0)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.geometry("+0+0")  # todo: figure this out

        # todo: put in some kind of "current" indicator for all selections?

        # Display selection
        ttk.Label(self.mainFrame, text="Display:").grid(column=0, row=1, sticky=tk.E)
        self.displayDict = {}
        self.displayDropdown = ttk.Combobox(self.mainFrame, width=32, state="readonly")
        self.displayDropdown.grid(column=1, row=1, sticky=tk.EW)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=2, columnspan=8, sticky=tk.EW)

        # Mode selection
        ttk.Label(self.mainFrame, text="Resolution:").grid(column=0, row=3, sticky=tk.E)
        self.modeDict = {}
        self.modeDropdown = ttk.Combobox(self.mainFrame, width=64, state="readonly")
        self.modeDropdown.grid(column=1, row=3, sticky=tk.EW)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=4, columnspan=8, sticky=tk.EW)

        # todo: make brightnessSlider display values as percentages
        # Brightness menu
        ttk.Label(self.mainFrame, text="Brightness:").grid(column=0, row=5, sticky=tk.E)
        self.brightnessSlider = tk.Scale(self.mainFrame, orient=tk.HORIZONTAL, width=32, from_=0, to=100)
        self.brightnessSlider.grid(column=1, row=5, sticky=tk.EW)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=6, columnspan=8, sticky=tk.EW)

        # todo: make rotateSlider display values in multiples of 90
        # Rotate menu
        ttk.Label(self.mainFrame, text="Rotate:").grid(column=0, row=7, sticky=tk.E)
        self.rotateSlider = tk.Scale(self.mainFrame, orient=tk.HORIZONTAL, width=32, from_=0, to=3)
        self.rotateSlider.grid(column=1, row=7, sticky=tk.EW)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=8, columnspan=8, sticky=tk.EW)

        # Mirroring menu
        ttk.Label(self.mainFrame, text="Mirroring:").grid(column=0, row=9, sticky=tk.E)
        # todo: some kind of mirroring input
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=10, columnspan=8, sticky=tk.EW)

        # Underscan menu
        ttk.Label(self.mainFrame, text="Underscan:").grid(column=0, row=11, sticky=tk.E)
        # todo: some kind of rotate input
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=12, columnspan=8, sticky=tk.EW)

        # Set/write to config menu
        ttk.Button(self.mainFrame, text="Set Display", command=self.setDisplay).grid(column=0, row=13, sticky=tk.E)
        ttk.Button(self.mainFrame, text="Build Config", command=self.buildConfig).grid(column=1, row=13, sticky=tk.E)
        ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=14, columnspan=8, sticky=tk.EW)

    def __displaySelectionInit(self):
        """
        Add all connected displays to self.displayDropdown.
        """
        displayStrings = []
        for display in dm.getAllDisplays():
            displayID = str(display.displayID)
            self.displayDict[displayID] = display
            displayStrings.append(displayID + " (Main Display)" if display.isMain else displayID)

        self.displayDropdown["values"] = displayStrings
        self.displayDropdown.current(0)
        self.displayDropdown.bind("<<ComboboxSelected>>", lambda event: self.__handleDisplaySelection())

    def __handleDisplaySelection(self):
        """
        Handles self.displayDropdown's "ComboboxSelected" callback.
        """
        # Switch all data-containing elements to give options for the current display.
        self.__modeSelectionInit()
        self.__brightnessSelectionInit()

    @property
    def display(self):
        """
        :return: The currently selected Display.
        """
        displayID = re.search(r"^[0-9]*", self.displayDropdown.get()).group()
        return self.displayDict[displayID]

    def __modeSelectionInit(self):
        """
        Add all the DisplayModes of the currently selected display to self.modeDropdown.
        """
        sortedModeStrings = []
        for mode in sorted(self.display.allModes, reverse=True):
            modeString = mode.__str__()
            self.modeDict[modeString] = mode
            sortedModeStrings.append(modeString)

        self.modeDropdown["values"] = sortedModeStrings
        self.modeDropdown.current(0)
        self.modeDropdown.bind("<<ComboboxSelected>>", lambda event: self.__handleModeSelection())

    # todo: find something for this to do, or delete it
    def __handleModeSelection(self):
        """
        Handles self.modeDropdown's "ComboboxSelected" callback.
        """
        pass

    @property
    def mode(self):
        """
        :return: The currently selected DisplayMode.
        """
        modeString = self.modeDropdown.get()
        return self.modeDict[modeString]

    def __brightnessSelectionInit(self):
        """
        Set self.brightnessSlider's value to that of the currently selected display
        """
        if self.display.brightness is not None:
            brightness = self.display.brightness * 100
            self.brightnessSlider.set(brightness)
        else:
            # todo: find a way to deactivate this slider altogether when the display's brightness can't be read/set
            pass

    # todo: find something for this to do, or delete it
    def __handleBrightnessSelection(self):
        pass

    @property
    def brightness(self):
        """
        :return: The currently selected brightness.
        """
        return int(self.brightnessSlider.get())

    @property
    def rotation(self):
        """
        :return: The currently selected brightness.
        """
        return int(self.rotateSlider.get() * 90)  # in multiples of 90 degrees

    # todo: this
    @property
    def mirror(self):
        """
        :return: The currently selected display to mirror.
        """
        return None

    # todo: this
    @property
    def underscan(self):
        """
        :return: The currently selected underscan.
        """
        return 0

    # todo: this
    @property
    def config(self):
        """
        :return: The currently entered config filename.
        """
        return "config"

    def generateCommandList(self):
        """
        :return: All currently selected commands, in the form of a DisplayManager.CommandList.
        """
        commands = [
            dm.Command(
                "set",
                "exact",
                width=self.mode.width,
                height=self.mode.height,
                depth=self.mode.depth,
                refresh=self.mode.refresh,
                displayID=self.display.displayID
            ),
            dm.Command(
                "brightness",
                "set",
                brightness=self.brightness,
                displayID=self.display.displayID
            ),
            dm.Command(
                "rotate",
                "set",
                angle=self.rotation,
                displayID=self.display.displayID
            ),
            # todo: uncomment, and set enable/disable mirroring correctly
            # dm.Command(
            #     "mirroring",
            #     "enable",
            #     mirrorDisplayID=self.mirror,
            #     displayID=self.display.displayID
            # ),
            # dm.Command(
            #     "underscan",
            #     "set",
            #     underscan=self.underscan,
            #     displayID=self.display.displayID
            # )
        ]

        commandList = dm.CommandList()
        for command in commands:
            commandList.addCommands(command)

        return commandList

    def setDisplay(self):
        """
        Set the Display to the currently selected settings.
        """
        commandList = self.generateCommandList()
        dm.run(commandList)

    def buildConfig(self):
        """
        Build a config file with the currently selected settings.
        """
        commandList = self.generateCommandList()
        cg.buildConfig(commandList, self.config)

    def start(self):
        """
        Open the GUI.
        """
        # Make sure Display Manager has IOKit ready for future requests
        dm.getIOKit()

        # Initialize all the data-containing elements
        self.__displaySelectionInit()
        self.__modeSelectionInit()
        self.__brightnessSelectionInit()

        self.root.mainloop()


def main():
    view = App()
    view.start()


if __name__ == "__main__":
    main()
