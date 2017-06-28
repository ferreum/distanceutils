#!/usr/bin/python
# File:        dst-bytes.py
# Description: dst-bytes
# Created:     2017-06-28


import argparse
from operator import attrgetter

from distance.common import format_bytes, format_duration
from distance.bytes import DstBytes
from distance.detect import Leaderboard, LevelInfos, Replay, detect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", nargs='+', type=argparse.FileType('rb'),
                        help="Replay filename.")
    parser.add_argument("--unknown", action='store_true',
                        help="Print unknown data too.")
    args = parser.parse_args()

    have_error = False
    for f in args.FILE:
        try:
            if len(args.FILE) > 1:
                print()
                print(f.name)
            dbytes = DstBytes(f)
            obj = detect(dbytes)
            print(f"Type: {type(obj).__name__}")
        except:
            import traceback
            traceback.print_exc()
            have_error = True
    return 1 if have_error else 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
