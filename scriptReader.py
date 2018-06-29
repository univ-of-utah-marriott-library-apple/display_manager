#!/usr/bin/python

# Reads in a script file and runs the corresponding commands in Display Manager.


import sys
import main.DisplayManager as dm


def main():
    try:
        file = open(sys.argv[1], "r")

        for line in file:
            words = line.split()
            for word in words:
                print(word)

    except IOError:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main()
