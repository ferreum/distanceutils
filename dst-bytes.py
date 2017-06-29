#!/usr/bin/python
# File:        dst-bytes.py
# Description: dst-bytes
# Created:     2017-06-28


import sys
import argparse
from operator import attrgetter
import traceback

from distance.common import format_bytes, format_duration
from distance.bytes import DstBytes
from distance.detect import Leaderboard, LevelInfos, Replay, parse_maybe_partial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", nargs='+', help=".bytes filename")
    parser.add_argument("--unknown", action='store_true',
                        help="Print unknown data too.")
    args = parser.parse_args()

    have_error = False
    for fname in args.FILE:
        with open(fname, 'rb') as f:
            try:
                if len(args.FILE) > 1:
                    print()
                    print(f.name)
                dbytes = DstBytes(f)
                obj, _, exception = parse_maybe_partial(dbytes)
                print(f"Type: {type(obj).__name__}")
                obj.print_data(sys.stdout, unknown=args.unknown)
            except:
                traceback.print_exc()
                have_error = True
    return 1 if have_error else 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0: