#!/usr/bin/python
# File:        dst-replay.py
# Description: dst-replay
# Created:     2017-06-28


import argparse
from operator import attrgetter

from distance.common import format_bytes, format_duration
from distance.bytes import DstBytes
from distance.replay import Replay


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
            replay = Replay(dbytes)
            if args.unknown:
                for s_list in replay.sections.values():
                    for section in s_list:
                        print(f"section {section.ident} unknown: {format_bytes(section.unknown)}")
                print(f"Unknown: {format_bytes(replay.unknown)}")
            print(f"Version: {replay.version}")
            print(f"Player name: {replay.player_name!r}")
            print(f"Player name: {replay.player_name_2!r}")
            print(f"Player ID: {replay.player_id}")
            print(f"Car name: {replay.car_name!r}")
            print(f"Finish time: {format_duration(replay.finish_time)}")
            print(f"Replay duration: {format_duration(replay.replay_duration)}")
        except:
            import traceback
            traceback.print_exc()
            have_error = True
    return 1 if have_error else 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
