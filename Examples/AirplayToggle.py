#!/usr/bin/python


import DisplayManager as dm


def main():
    displays = dm.getAllDisplays()
    if len(displays) == 2:
        if displays[0].isMain and not displays[1].isMain:
            displays[0].setMirrorOf(displays[1])
        elif not displays[0].isMain and displays[0].isMain:
            displays[1].setMirrorOf(displays[0])


if __name__ == "__main__":
    main()
