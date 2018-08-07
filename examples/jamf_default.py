#!/usr/bin/python


from display_manager import *


for display in getAllDisplays():
    if not display.isHidpi:
        display.setMode(display.highestMode())
    else:
        hidpiModes = sorted(display.allModes(2))  # retrieves all of display's HiDPI modes, sorted low to high
        modeIndex = (len(hidpiModes) // 2) + 1
        display.setMode(hidpiModes[modeIndex])
