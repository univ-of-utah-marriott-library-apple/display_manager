#!/usr/bin/python

# Experiment with different Python libraries


import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--verbosity")
args = parser.parse_args()

print(args.verbose)
