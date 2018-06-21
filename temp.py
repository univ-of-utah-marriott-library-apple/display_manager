#!/usr/bin/python

# Temporary staging script to test out Python-Objective-C bridge commands


import objc  # the actual bridge
import Quartz  # Mac Display Services
import io  # for opening and reading .XML files


def getIO():
    # Get IOKit up and running
    iokit = objc.initFrameworkWrapper(
        "IOKit",
        frameworkIdentifier="com.apple.iokit",
        frameworkPath=objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"),
        globals=globals()
    )

    functions = [
        ("IOServiceRequestProbe", b"iI@o^I")
    ]
    # variables = [
    #     # The keys per angle of rotation
    #     ("kIOScaleRotate0", b""),
    #     ("kIOScaleRotate90", b"*"),
    #     ("kIOScaleRotate180", b""),
    #     ("kIOScaleRotate270", b""),
    #     # We'll see what this does soon enough
    #     ("kIOFBSetTransform", b"I")
    # ]

    # todo: see if you can replace globals() with some other dict
    objc.loadBundleFunctions(iokit, globals(), functions)
    # objc.loadBundleVariables(iokit, globals(), variables)


def getRotateKey(angle):
    rotateCodes = {0: 0, 90: 3, 180: 6, 270: 5}  # equivalent to kIOFBRotate{0, 90, 180, 270}
    setTransformCode = 1024  # equivalent to kIOFBSetTransform
    if angle % 90 == 0:
        # grab the right code, and move it to the right part of a 32-bit word
        rotateCode = rotateCodes[angle % 360] << 16
        # "or" the two together
        return int(setTransformCode | rotateCode)
    else:  # inappropriate angle
        return None


def rotate(display, degrees):
    options = getRotateKey(degrees)
    if options:  # the angle was an appropriate number of degrees
        service = Quartz.CGDisplayIOServicePort(display)
        IOServiceRequestProbe(service, options, None)  # actually sets the rotation


# todo: rename this
def tempRename(display):

    xmlString = """
    <?xml version='1.0'?>
    <!DOCTYPE signatures SYSTEM "file://localhost/System/Library/DTDs/BridgeSupport.dtd">
    <signatures version='1.0'>
    <function name='IOServiceRequestProbe'>
    <arg type='I'/>
    <arg type='I'/>
    <retval type='i'/>
    </function>
    </signatures>
    """

    # with io.open("../PyRotate/iokit.metadata", "r", encoding="utf-8") as cont:
    #     IOKIT_XML = cont.read()
    # objc.parseBridgeSupport(IOKIT_XML, globals(), objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"))
    objc.parseBridgeSupport(xmlString, globals(), objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"))

    # with io.open("../PyRotate/iodisp.metadata", "r", encoding="utf-8") as cont:
    #     IODISP_XML = cont.read()
    # objc.parseBridgeSupport(IODISP_XML, globals(), objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"))

    service = Quartz.CGDisplayIOServicePort(display)
    # options = (0x00000400 | (kIOScaleRotate90) << 16)
    options = (0x00000400 | (48) << 16)
    IOServiceRequestProbe(service, options)

    from time import sleep
    sleep(2)

    # options = (0x00000400 | (kIOScaleRotate0) << 16)
    # options = (0x00000400 | (0) << 16)
    options = 0x00000400
    IOServiceRequestProbe(service, options)

    # (0, 0), (90, 48), (180, 96), (80, 80)


def main():
    # getIO()
    # rotate(Quartz.CGMainDisplayID(), int(sys.argv[1]))
    tempRename(Quartz.CGMainDisplayID())


if __name__ == "__main__":
    main()
