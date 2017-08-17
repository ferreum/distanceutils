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

    scale = (1 / 16,) * 3
    objs = []
    from math import pi, cos, sin
    for i in range(13):
        r = pi * i * .1
        x = (i - 6) * 6
        objs.append(WedgeGS(transform=((x, 0, 0), (sin(r), 0, 0, cos(r)), scale)))
    group = Group(subobjects=objs)

    with open(args.FILE[0], 'wb') as f:
        group.write(DstBytes(f))


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
