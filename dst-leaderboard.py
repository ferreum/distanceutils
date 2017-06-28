#!/usr/bin/python
# File:        dst-leaderboard.py
# Description: dst-leaderboard
# Created:     2017-06-27


import argparse
from operator import attrgetter

from distance.common import format_bytes, format_duration
from distance.bytes import DstBytes
from distance.leaderboard import Leaderboard


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", nargs='+', type=argparse.FileType('rb'),
                        help="LocalLeaderboard 1.bytes filename.")
    parser.add_argument("--nosort", action='store_true',
                        help="Print entries in order they occur in the file.")
    parser.add_argument("--unknown", action='store_true',
                        help="Print unknown data too.")
    args = parser.parse_args()

    for filenr, f in enumerate(args.FILE):
        try:
            if len(args.FILE) > 1:
                if filenr > 0:
                    print()
                print(f.name)
            dbytes = DstBytes(f)
            lb = Leaderboard(dbytes)
            if args.unknown:
                for section in lb.sections.values():
                    print(f"section {section.ident} unknown: {format_bytes(section.unknown)}")
            if args.nosort:
                entries = lb.iter_entries()
            else:
                entries = lb.read_entries()
                entries.sort(key=attrgetter('time'))
            unknown = ""
            for i, entry in enumerate(entries, 1):
                replay = ""
                if entry.replay is not None and entry.replay != 0xffffffffffffffff:
                    replay = f" Replay: {entry.replay:X}"
                if args.unknown:
                    unknown = f"{format_bytes(entry.unknown)} "
                print(f"{unknown}{i}. {entry.playername!r} - {format_duration(entry.time)}{replay}")
        except:
            import traceback
            traceback.print_exc()
    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
