import ctypes
import ctypes.util
import Quartz

iokit = ctypes.cdll.LoadLibrary(ctypes.util.find_library("IOKit"))

iokit.IOServiceOpen(Quartz.CGDisplayIOServicePort(Quartz.CGMainDisplayID()),
                    iokit.mach_task_self(), 0, ctypes.byref(ctypes.c_void_p()))
