#!/usr/bin/python

## Gets the current brightness via Apple's libraries.

import sys
import objc

import CoreFoundation
import Quartz

def initialize_iokit_functions_and_variables():
    iokit = objc.initFrameworkWrapper(
        "IOKit",
        frameworkIdentifier="com.apple.iokit",
        frameworkPath=objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"),
        globals=globals()
        )
    functions = [
        ("IOServiceGetMatchingServices", b"iI@o^I"),
        ("IODisplayCreateInfoDictionary", b"@II"),
        ("IODisplayGetFloatParameter", b"iII@o^f"),
        ("IOObjectRelease", b"iI"),
        ("IOServiceMatching", b"@or*", "", dict(
            arguments=
            {
                0: dict(type=objc._C_PTR + objc._C_CHAR_AS_TEXT,
                        c_array_delimited_by_null=True,
                        type_modifier=objc._C_IN)
            }
        )),
        ("IOIteratorNext", "II"),
        ]
    variables = [
        ("kIODisplayNoProductName", b"I"),
        ("kIOMasterPortDefault", b"I"),
        ("kIODisplayBrightnessKey", b"*"),
        ("kDisplayVendorID", b"*"),
        ("kDisplayProductID", b"*"),
        ("kDisplaySerialNumber", b"*"),
        ]
    objc.loadBundleFunctions(iokit, globals(), functions)
    objc.loadBundleVariables(iokit, globals(), variables)
    # Other global variables.
    global kMaxDisplays
    kMaxDisplays = 32
    global kDisplayBrightness
    kDisplayBrightness = CoreFoundation.CFSTR(kIODisplayBrightnessKey)

def CFNumberEqualsUInt32(number, uint32):
    if number is None:
        return uint32 == 0
    return number == uint32

def CGDisplayGetIOServicePort(display):
    vendor = Quartz.CGDisplayVendorNumber(display)
    model  = Quartz.CGDisplayModelNumber(display)
    serial = Quartz.CGDisplaySerialNumber(display)

    matching = IOServiceMatching("IODisplayConnect")

    error, iterator = IOServiceGetMatchingServices(kIOMasterPortDefault, matching, None)
    if error:
        return 0

    service = IOIteratorNext(iterator)
    matching_service = 0

    while service != 0:
        info = IODisplayCreateInfoDictionary(service, kIODisplayNoProductName)

        vendorID = CoreFoundation.CFDictionaryGetValue(info, CoreFoundation.CFSTR(kDisplayVendorID))
        productID = CoreFoundation.CFDictionaryGetValue(info, CoreFoundation.CFSTR(kDisplayProductID))
        serialNumber = CoreFoundation.CFDictionaryGetValue(info, CoreFoundation.CFSTR(kDisplaySerialNumber))

        if (
            CFNumberEqualsUInt32(vendorID, vendor) and
            CFNumberEqualsUInt32(productID, model) and
            CFNumberEqualsUInt32(serialNumber, serial)
            ):
            matching_service = service
            break

        service = IOIteratorNext(iterator)

    return matching_service

if __name__ == '__main__':
    # Initialize the Objective-C methods needed.
    initialize_iokit_functions_and_variables()
    # Get the service port.
    service = CGDisplayGetIOServicePort(Quartz.CGMainDisplayID())
    # Get the brightness.
    (error, brightness) = IODisplayGetFloatParameter(service, 0, kDisplayBrightness, None)
    if error:
        print("Failed to get brightness of display: ({})".format(error))
        sys.exit(3)
    print("brightness: {}".format(brightness))
