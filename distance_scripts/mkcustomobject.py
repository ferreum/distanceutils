#!/usr/bin/python

"""Creates a CustomObject from a level."""


import os
import sys
import argparse

from distance.level import Level
from distance.bytes import DstBytes


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-f", "--force", action='store_true',
                        help="Allow overwriting OUT file.")
    parser.add_argument("-n", "--objnum", type=int,
                        help="Object number to extract.")
    parser.add_argument("IN",
                        help="Level .bytes filename.")
    parser.add_argument("OUT",
                        help="output .bytes filename.")
    args = parser.parse_args()

    objnum = args.objnum or 0

    write_mode = 'xb'
    if args.force:
        write_mode = 'wb'

    if not args.force and os.path.exists(args.OUT):
        print("file {args.OUT} exists. pass -f to force.", file=sys.stderr)
        return 1

    with open(args.IN, 'rb') as in_f:
        level = Level(DstBytes(in_f))
        for i, obj in enumerate(level.iter_objects()):
            if i == objnum:
                with open(args.OUT, write_mode) as out_f:
                    obj.write(DstBytes(out_f))
                    return 0

    print("no matching object found", file=sys.stderr)
    return 1


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
