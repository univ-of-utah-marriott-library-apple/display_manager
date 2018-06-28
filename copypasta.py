import ctypes
import ctypes.util
import Quartz

iokit = ctypes.cdll.LoadLibrary(ctypes.util.find_library("IOKit"))

iokit.IOServiceOpen(Quartz.CGDisplayIOServicePort(Quartz.CGMainDisplayID()),
                    iokit.mach_task_self(), 0, ctypes.byref(ctypes.c_void_p()))

#
#
#
#
#
#

mode = Quartz.CGDisplayCopyDisplayMode(Quartz.CGMainDisplayID())

raw_width = Quartz.CGDisplayModeGetPixelWidth(mode)
raw_height = Quartz.CGDisplayModeGetPixelHeight(mode)
res_width = Quartz.CGDisplayModeGetWidth(mode)
res_height = Quartz.CGDisplayModeGetHeight(mode)
