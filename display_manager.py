#!/usr/bin/env python

## Some info should go here.

__version__ = '0.1.0'

## Imports
import argparse

def usage():
    pass

class ArgumentParser(argparse.ArgumentParser):
    """
    Custom argument parser for printing error messages a bit more nicely.
    """
    def error(self, message):
        print("Error: {}\n".format(message))
        usage()
        self.exit(2)

if __name__ == '__main__':
    parser = ArgumentParser(add_help = False)
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')
    parser.add_argument('-a', '--all-matches', action='store_true')
    parser.add_argument('-c', '--close-matches', action='store_true')
    parser.add_argument('-z', '--highest-match', action='store_true')
    parser.add_argument('-x', '--exact-match', action='store_true')
    parser.add_argument('-M', '--mirroring-on', action='store_true')
    parser.add_argument('-m', '--mirroring-off', dest='mirroring-on', action='store_false')
    parser.add_argument('-n', '--no-change', action='store_true')
