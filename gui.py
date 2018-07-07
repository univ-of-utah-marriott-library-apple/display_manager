#!/usr/bin/python

# A GUI that allows users to interface with Display Manager


from __future__ import print_function
import Tkinter as tk
import ttk
import re
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

        # Set up the window
        self.mainFrame.grid(column=0, row=0)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.geometry("+400+200")

        # todo: get the real logo
        self.logoPic = tk.PhotoImage(
            data='''\
        R0lGODlhWAJRAPcAAAEAAAQECgYJCgwMDQgHCBMODQ4QDhERDg0OEQUHFREOEw4REgoTGhITFBQV
        GhUZGxsbHBkXGCcXFR0iHiwkHRwdIxYZJhAVLyIcIxwjJRcpNiUlJSQlKyUqLCwrLCknJzQqKCgr
        NjMtNSwyOTMzNTM0Ozs7PDk3ODYyK1ExFWo3Ekc3KUQ7OlY0LF8rKD9DPHdIGnBJGUpEO1ZJOVdJ
        LHZLJXBRMHdhNxknQicqRS01RTM1Qjs8Qzg6Ry86VRkvWEQ9REk+TGYzQD1DSDlFVTlTY0NCQ0RD
        S0xLTEtHR1NLSVhSS0hJVlJNU1ROWExTWFVSVFtUVFlZWVdVWkhTSGhXSGRaWXFQS2pkXXdoVEtV
        Z1dZZlFUa2VdZFVpbmxra2dlZ3Rpamdpdnx9fXd2d3FzcFJjWaE0MMQSMMcfO8chPMgjPtQyOPow
        OolXG4xRF5llHLBtGYhYJ5ZbJ4lVM5hmKYlmN5doN5NsMKhrJqd0KrZ4Kah4N7Z7NqxqN6VZKMh4
        L+BXLc46U8kqRPwxRoZnRpByT613TIt3bq51bpNYTtFGXtBFVch0TtRTaNJMY9lnevNvVXCNe1aP
        bj+EbriFObmEKsiIKNmZK8WIN8qUOdiYNtGPLOSZMNujOdymMOmmK/WqKPq1KueoN+2zOfW1NPS0
        O/u6PPm5N/OsN+CYG/7FOf/MMbKLTI+Idq+PbrCrcJSRYMeWRs6QT9mlRc+nVeeqRuyzRve5RO6y
        UcySbNOrbuyza+iTUv3FRfvOUPXKbv/rZHJ3hVZxkYF+hdtugN13iHiJh3ajmjOL5kiS342NjYeE
        hpycnJiVl5CQjrKUjJGpl7ColJadpqqqqqWnqLi4uLa2tbGwrpqjp9CYjuKKmeGFlOyXkc2wkPiq
        k8q3rPKxsOaap7XKne3Pj9TKtvLMruvZobu6w9m9xLjGyMXFxcfKydHR0d3d3dbV19LQz/DCyvnF
        w+zVzObk2vjt0Nrd5+np6eXm5fj16/T09Pzz9f////f3+uzu8d3h5yH5BAAAAAAALAAAAABYAlEA
        AAj+APkJHEiwoMGDCBMO1PdKRQoVgGzlojWLjgULCaj1E/KnHr93AufVoycNm8B+/PzhU8iypcuX
        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
        RXatYVEc4fS1X6tJYfhlV+YIAHbNrRlMDAJOjqk9GiNghmrgPyVGKH1QU5Uxgu3F4z9OGCb+U84K
        B3GIh0WIB24IBz/5h5hkmkK64W5jV6vJrdq9Xem01FJMY2sTJDiuGAImYAF4SSXoAlcogzGgQHcQ
        YkBGqHtYSiMmE1aW5dUR5LfkLH4Ih3iYB0EoZCr2E2eIrg0ARfmNuquJQdqtxWMWpEqu5GUeYWVr
        Zul04+RIjgJeANHUAiwQhmkYAzD44WuwhnZY5Vl+tdJohgf+AkQIDXJmZ5nxUzVQgzSQ53mm53q2
        53v+ToMYu2V+iAdjiId42AZjmIeEAQNlewAYZY7phObpnMFaTGOGliNPXuhqvgwCtgAk+AIywEp4
        cId8QOJ2BumQbud96AcP3IeTNmmSTmmVPumWbumU9sB82OC+EIdiiIdiWOSadQACQIEISNoz5lkj
        C1o5ouZqJlACnj1cxdwEiIANAAGG+AJmmAZwGGeRtuqrbmdBZZ2Z9hOKIQDuyduwbt9pRowCdtEG
        mAAeaIItKBhnqAZrYAd4eId1wAZsWAd88Id8wOq95uu+Zs1GmWhlkz3nkIA6I6tnwIZrQId2oIfo
        9evHhuzINlBsYIZniAxnaIZmqIZyaAd38FjJBu0V0BZt1tTq0Tbt00bt1Fbt1WbtBQ4IACH/C1hN
        UCBEYXRhWE1QPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtj
        OWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUg
        WE1QIENvcmUgNS42LWMxMzggNzkuMTU5ODI0LCAyMDE2LzA5LzE0LTAxOjA5OjAxICAgICAgICAi
        PgogPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1z
        eW50YXgtbnMjIj4KICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIi8+CiA8L3JkZjpSREY+
        CjwveDp4bXBtZXRhPgo8P3hwYWNrZXQgZW5kPSJyIj8+Af/+/fz7+vn49/b19PPy8fDv7u3s6+rp
        6Ofm5eTj4uHg397d3Nva2djX1tXU09LR0M/OzczLysnIx8bFxMPCwcC/vr28u7q5uLe2tbSzsrGw
        r66trKuqqainpqWko6KhoJ+enZybmpmYl5aVlJOSkZCPjo2Mi4qJiIeGhYSDgoGAf359fHt6eXh3
        dnV0c3JxcG9ubWxramloZ2ZlZGNiYWBfXl1cW1pZWFdWVVRTUlFQT05NTEtKSUhHRkVEQ0JBQD8+
        PTw7Ojk4NzY1NDMyMTAvLi0sKyopKCcmJSQjIiEgHx4dHBsaGRgXFhUUExIREA8ODQwLCgkIBwYF
        BAMCAQAAOw==
        '''
        )
        self.imageLabel = ttk.Label(self.mainFrame, image=self.logoPic).grid(column=1, row=0, sticky=tk.NSEW)
        # todo: this separator (increment more than you think you need to; might be other stuff that needs a new row too
        # ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=1, columnspan=8, sticky=tk.EW)

        # todo: put in some kind of "current" indicator for all selections and default to those values?

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
        ttk.Label(self.mainFrame, text="Mirror Display:").grid(column=0, row=9, sticky=tk.E)
        self.mirrorEnabled = False
        self.mirrorDropdown = ttk.Combobox(self.mainFrame, width=32, state="readonly")
        self.mirrorDropdown.grid(column=1, row=9, sticky=tk.EW)
        enable = ttk.Button(self.mainFrame, text="Enable", command=lambda: self.__toggleMirroring(True))
        enable.grid(column=1, row=10, sticky=tk.W)
        disable = ttk.Button(self.mainFrame, text="Disable", command=lambda: self.__toggleMirroring(False))
        disable.grid(column=1, row=10, sticky=tk.E)
        # todo: this separator (increment rows)
        # ttk.Separator(self.mainFrame, orient=tk.HORIZONTAL).grid(row=10, columnspan=8, sticky=tk.EW)

        # Underscan menu
        ttk.Label(self.mainFrame, text="Underscan:").grid(column=0, row=11, sticky=tk.E)
        self.underscanSlider = tk.Scale(self.mainFrame, orient=tk.HORIZONTAL, width=32, from_=0, to=100)
        self.underscanSlider.grid(column=1, row=11, sticky=tk.EW)
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
        self.displayDropdown.bind("<<ComboboxSelected>>", lambda event: self.__reloadDisplay())

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

    def __brightnessSelectionInit(self):
        """
        Set self.brightnessSlider's value to that of the currently selected display.
        """
        if self.display.brightness is not None:
            brightness = self.display.brightness * 100
            self.brightnessSlider.set(brightness)
        else:
            # todo: find a way to deactivate this slider altogether when the display's brightness can't be read/set
            pass

    def __mirrorSelectionInit(self):
        """
        Show the other available displays to mirror.
        """
        otherDisplayIDs = []
        for display in self.displayDict.values():
            displayID = str(display.displayID)
            if displayID != str(self.display.displayID):
                otherDisplayIDs.append(displayID + " (Main Display)" if display.isMain else displayID)

        self.mirrorDropdown["values"] = otherDisplayIDs
        self.mirrorDropdown.current(0)

    # todo: this -- deactivate slider if it can't be read/set; default to current value
    def __underscanSelectionInit(self):
        pass

    def __toggleMirroring(self, boolean):
        """
        Toggles whether mirroring is enabled.
        :param boolean: True if enabled, False if disabled.
        """
        self.mirrorEnabled = boolean

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
    def brightness(self):
        """
        :return: The currently selected brightness.
        """
        return float(self.brightnessSlider.get()) / 100

    @property
    def rotation(self):
        """
        :return: The currently selected brightness.
        """
        return int(self.rotateSlider.get() * 90)  # in multiples of 90 degrees

    @property
    def mirror(self):
        """
        :return: The currently selected display to mirror.
        """
        mirrorID = re.search(r"^[0-9]*", self.mirrorDropdown.get()).group()
        return self.displayDict[mirrorID]

    @property
    def underscan(self):
        """
        :return: The currently selected underscan.
        """
        return abs((float(self.underscanSlider.get()) / 100) - 1)

    def __generateCommandList(self):
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
                displayID=self.display.displayID,
                hidpi=0
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
            dm.Command(
                "mirror",
                "enable" if self.mirrorEnabled else "disable",
                mirrorDisplayID=self.mirror.displayID,
                displayID=self.display.displayID
            ),
            dm.Command(
                "underscan",
                "set",
                underscan=self.underscan,
                displayID=self.display.displayID
            )
        ]

        commandList = dm.CommandList()
        for command in commands:
            commandList.addCommands(command)

        return commandList

    def setDisplay(self):
        """
        Set the Display to the currently selected settings.
        """
        commandList = self.__generateCommandList()
        dm.run(commandList)

        self.__reloadDisplay()

    def buildConfig(self):
        """
        Build a config file with the currently selected settings.
        """
        commandList = self.__generateCommandList()
        cg.buildConfig(commandList, "config")

    def __reloadDisplay(self):
        """
        Reloads data-containing elements.
        """
        self.__modeSelectionInit()
        self.__brightnessSelectionInit()
        self.__mirrorSelectionInit()

        self.mirrorEnabled = False  # resets every time the display is switched

    def start(self):
        """
        Open the GUI.
        """
        # Make sure Display Manager has IOKit ready for future requests
        dm.getIOKit()

        self.__displaySelectionInit()
        self.__reloadDisplay()

        self.root.mainloop()


def main():
    view = App()
    view.start()


if __name__ == "__main__":
    main()
