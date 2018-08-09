#!/usr/bin/python


from display_manager_lib import *


d = getMainDisplay()
allModes = d.allModes()
duplicates = []

for mode1 in allModes:
    for mode2 in allModes:
        if mode1 == mode2:
            duplicates.append((mode1, mode2))

for pair in duplicates:
    fs = []
    ids = []
    for mode in pair:
        width = Quartz.CGDisplayModeGetWidth(mode.raw)
        height = Quartz.CGDisplayModeGetHeight(mode.raw)
        refresh = Quartz.CGDisplayModeGetRefreshRate(mode.raw)
        flags = Quartz.CGDisplayModeGetIOFlags(mode.raw)
        modeID = Quartz.CGDisplayModeGetIODisplayModeID(mode.raw)
        # print(width, height, refresh, flags)
        fs.append(flags)
        # print()
        ids.append(modeID)
    # print(fs[0] == fs[1])
    print(ids[0] == ids[1])
