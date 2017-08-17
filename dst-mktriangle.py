#!/usr/bin/python
# File:        dst-mktriangle.py
# Description: dst-mktriangle
# Created:     2017-08-16


import sys
import argparse
import traceback

from distance.bytes import DstBytes, PrintContext
from distance.level import WedgeGS, Group


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", nargs=1, help=".bytes filename")
    args = parser.parse_args()

    with open(args.FILE[0], 'wb') as f:
        dbytes = DstBytes(f)
        wedge1 = WedgeGS()
        wedge1.transform = ((0, -50, 0), (0, 0, 1, 0), (1e-10, 1, 1))
        wedge2 = WedgeGS()
        wedge2.transform = ((0, 50, 0), (0, 0, 0, -1), (1e-10, 1, 1))
        group = Group()
        group.subobjects = [wedge1, wedge2]
        group.write(dbytes)


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
