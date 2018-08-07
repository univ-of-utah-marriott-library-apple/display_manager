#!/usr/bin/python


from display_manager_lib import *


def main():
    displays = getAllDisplays()
    # Only perform on 2 displays
    if len(displays) == 2:
        # Neither display is mirroring; set ext0 to mirror main
        if not displays[0].mirrorSource and not displays[1].mirrorSource:
            if displays[0].isMain and not displays[1].isMain:
                displays[1].setMirrorSource(displays[0])
            elif not displays[0].isMain and displays[0].isMain:
                displays[0].setMirrorSource(displays[1])
        # Mirroring enabled; disable on all displays
        else:
            for display in displays:
                display.setMirrorSource(None)


if __name__ == "__main__":
    main()
