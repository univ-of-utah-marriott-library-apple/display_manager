#!/usr/bin/python

# Tests display_manager.py by manually running commands through it and prompting the user as to whether
# the right changes are occurring on-screen


import subprocess


def setCommand(width, height, depth, refresh, display):
    subprocess.call([
        "/usr/bin/python",
        "display_manager.py",
        "set",
        "-w",
        str(width),
        "-h",
        str(height),
        "-d",
        str(depth),
        "-r",
        str(refresh),
        "--display",
        str(display)
    ])


def setDefault():
    width = 1920
    height = 1080
    depth = 32
    refresh = 0
    display = 69731456

    setCommand(width, height, depth, refresh, display)


def setTiny():
    width = 640
    height = 480
    depth = 32
    refresh = 60
    display = 69731456

    setCommand(width, height, depth, refresh, display)


def main():
    setTiny()
    raw_input("Should have gone to 640x480...")
    setDefault()


if __name__ == "__main__":
    main()
