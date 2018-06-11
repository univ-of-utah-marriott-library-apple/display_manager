#!/usr/bin/python

# Tests display_manager.py by manually running commands through it and prompting the user as to whether
# the right changes are occurring on-screen


import subprocess
import time
import sys


## Set stuff
def setCommand(width, height, depth, refresh, display):
    subprocess.call([
        "./display_manager.py",
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


def setTiny(display):
    width = 640
    height = 480
    depth = 32
    refresh = 60

    setCommand(width, height, depth, refresh, display)


def setDefault(display):
    width = 1920
    height = 1080
    depth = 32
    refresh = 0

    setCommand(width, height, depth, refresh, display)


## Show stuff
def getDisplays():
    process = subprocess.Popen([
        "./display_manager.py",
        "show"
    ], stdout=subprocess.PIPE)

    displays = []
    while True:  # parse the output
        line = process.stdout.readline()
        nextIsTop = False
        if line == "":
            break

        elif line[0:7] == "Display":
            display = ""
            for char in line[9:]:
                try:
                    int(char)
                    display = display + char
                except ValueError:
                    break
            displays.append(display)
            nextIsTop = True

    return displays


## Brightness stuff
def brightnessCommand(display):
    def setBrightness(brightness):
        subprocess.call([
            "./display_manager.py",
            "brightness",
            "set",
            str(brightness),
            "--display",
            str(display)
        ])

    for i in range(9):
        setBrightness(i/10 + .1)


def main():
    # Show stuff
    displays = getDisplays()
    assert len(displays) == 3  # only for my own personal setup

    # # Set stuff
    # setTiny(displays[0])
    # print("Display resolution should be 640x480")
    # time.sleep(2)
    #
    # setDefault(displays[0])
    # print("Display resolution should have returned to normal")

    # Brightness stuff
    brightnessCommand(displays[0])

    sys.exit()


if __name__ == "__main__":
    main()
