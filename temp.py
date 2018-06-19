#!/usr/bin/python

# Temporary staging script to test out Python-Objective-C bridge commands


import objc  # the actual bridge
import Quartz  # Mac Display Services


def rotate(display, degrees):
    pass


def getRotation(display):
    return Quartz.CGDisplayRotation(display)


def main():
    # Get IOKit up and running
    iokit = objc.initFrameworkWrapper(
        "IOKit",
        frameworkIdentifier="com.apple.iokit",
        frameworkPath=objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"),
        globals=globals()
    )

    # todo: figure out wtf the bytestrings are actually supposed to be!!
    functions = [("", b"")]

    display = Quartz.CGMainDisplayID()

    print(getRotation(display))


if __name__ == "__main__":
    main()
