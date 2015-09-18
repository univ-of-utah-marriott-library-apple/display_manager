#!/usr/bin/python

import Quartz

if __name__ == '__main__':
    print("Attempting to do:")
    print("  (error, config_ref) = Quartz.CGBeginDisplayConfiguration(None)")
    (error, config_ref) = Quartz.CGBeginDisplayConfiguration(None)
    print("Success.")
