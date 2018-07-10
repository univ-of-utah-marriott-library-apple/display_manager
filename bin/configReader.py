#!/usr/bin/python

# Reads in a config file and runs the corresponding commands in Display Manager.

import sys
import pickle
import os.path


def main():
    filename = sys.argv[1]

    if os.path.isfile("./config/" + filename):
        with open(sys.argv[1], "r") as file:
            commands = pickle.load(file)
        commands.run()
    else:
        print("File {} not found.".format(filename))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main()
