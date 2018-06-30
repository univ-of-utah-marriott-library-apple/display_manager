#!/usr/bin/python

# Writes to a config file per given Display Manager commands.


import pickle
import sys
sys.path.append("..")  # to allow import from current directory
import DisplayManager as dm
import commandLine as cl


def main():
    print("Write each command out on its own line. After final command, hit return on empty line.")

    commands = []
    while True:
        line = raw_input()
        if line:
            commands.append(cl.getCommand(line))
        else:
            break

    commandList = dm.CommandList()
    for command in commands:
        commandList.addCommands(command)
        commandList.addCommands(command)
        commandList.addCommands(command)

    with open(sys.argv[1], "w") as file:
        pickle.dump(commandList, file)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main()
