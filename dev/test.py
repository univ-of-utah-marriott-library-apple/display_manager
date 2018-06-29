#!/usr/bin/python

# Experiment with different Python libraries


import ctypes
import ctypes.util

iokit = ctypes.cdll.LoadLibrary(ctypes.util.find_library("IOKit"))


class Thing(object):

    def __init__(self, x):
        self.x = x

    def __gt__(self, otherThing):
        return self.x > otherThing.x

    def __lt__(self, otherThing):
        return self.x < otherThing.x

    def __str__(self):
        return str(self.x)


a = Thing(2)
b = Thing(1)
c = Thing(42)
this = [a, b, c]

for i in sorted(this, reverse=True):
    print(i)
