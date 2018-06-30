#!/usr/bin/python

# Reads in a config file and runs the corresponding commands in Display Manager.


import sys
import pickle
import os.path
import main.DisplayManager as dm


def main():
    fileName = sys.argv[1]

    if os.path.isfile("./" + fileName):
        with open(sys.argv[1], "r") as file:
            commands = pickle.load(file)
        dm.run(commands)
    else:
        print("File {} not found.".format(fileName))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main()
