#!/usr/bin/python


import Quartz


for mode in Quartz.CGDisplayCopyAllDisplayModes(
    # Quartz.CGMainDisplayID(),
    # 69731456,
    478176721,
    {Quartz.kCGDisplayShowDuplicateLowResolutionModes: True}
):
    width = Quartz.CGDisplayModeGetWidth(mode)
    height = Quartz.CGDisplayModeGetHeight(mode)
    refresh = Quartz.CGDisplayModeGetRefreshRate(mode)
    flags = Quartz.CGDisplayModeGetIOFlags(mode)
    ioMode = Quartz.CGDisplayModeGetIODisplayModeID(mode)
    usable = Quartz.CGDisplayModeIsUsableForDesktopGUI(mode)
    # print(width, height, refresh, flags, ioMode, usable)
    print(width, height, hex(flags))
