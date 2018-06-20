#!/usr/bin/python

# Temporary staging script to test out Python-Objective-C bridge commands


import objc  # the actual bridge
import Quartz  # Mac Display Services
import sys


def getIO():
    # Get IOKit up and running
    iokit = objc.initFrameworkWrapper(
        "IOKit",
        frameworkIdentifier="com.apple.iokit",
        frameworkPath=objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"),
        globals=globals()
    )

    # todo: figure out wtf the bytestrings are actually supposed to be!!
    functions = [
        ("IOServiceRequestProbe", b"iI@o^I")
    ]
    # variables = [
    #     # The keys per angle of rotation
    #     ("kIOScaleRotate0", b""),
    #     ("kIOScaleRotate90", b""),
    #     ("kIOScaleRotate180", b""),
    #     ("kIOScaleRotate270", b""),
    #     # We'll see what this does soon enough
    #     ("kIOFBSetTransform", b"*")
    # ]

    # todo: see if you can replace globals() with some other dict
    objc.loadBundleFunctions(iokit, globals(), functions)
    # objc.loadBundleVariables(iokit, globals(), variables)


def getAngleOptions(angle):
    rotateCodes = {0: 0, 90: 3, 180: 6, 270: 5}  # equivalent to kIOFBRotate{0, 90, 180, 270)
    setTransformCode = 1024  # equivalent to kIOFBSetTransform
    if angle % 90 == 0:
        # grab the right code, and move it to the right part of a 32-bit word
        rotateCode = rotateCodes[angle % 360] << 16
        # or the two together
        return setTransformCode | rotateCode
    else:  # inappropriate angle
        return None


def rotate(display, degrees):
    options = getAngleOptions(degrees)
    if options:  # the angle was an appropriate number of degrees
        service = Quartz.CGDisplayIOServicePort(display)

        # todo: delete these lines:
        # options = int(hex(1024 | options), 16)
        # options = 197632

        IOServiceRequestProbe(service, options, None)  # actually sets the rotation


def main():
    getIO()
    rotate(Quartz.CGMainDisplayID(), int(sys.argv[1]))

    # print(kIOScaleRotate0 == getAngleOptions(0))
    # print(kIOScaleRotate90 == getAngleOptions(90))
    # print(kIOScaleRotate180 == getAngleOptions(180))
    # print(kIOScaleRotate270 == getAngleOptions(270))


if __name__ == "__main__":
    main()
