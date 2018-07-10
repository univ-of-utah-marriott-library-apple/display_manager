#!/usr/bin/python

# Writes to a config file per given Display Manager commands.

import pickle
import sys
import DisplayManager as dm
import commandLine as cl


def buildConfig(commandList, filename):
    """
    Build the configuration file.
    :param commandList: The DisplayManager.CommandList to write to the file.
    :param filename: The name of the file to write to.
    """
    with open("./config/" + filename, "w") as file:
        pickle.dump(commandList, file)


def main():
    commands = []
    for line in sys.argv[2:]:
        commands.append(cl.getCommand(line))

    commandList = dm.CommandList()
    for command in commands:
        commandList.addCommands(command)

    buildConfig(commandList, sys.argv[1])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
