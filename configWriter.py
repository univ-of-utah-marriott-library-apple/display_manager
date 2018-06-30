#!/usr/bin/python

# Writes a config file per given Display Manager commands.


import pickle
import sys
import main.DisplayManager as dm


def main():
    commands = [
        dm.Command("rotate", "set", angle="90"),
        dm.Command("rotate", "set"),
        dm.Command("set", "closest", width=800, height=600),
        dm.Command("set", "highest")
    ]

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
