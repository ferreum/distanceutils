#!/usr/bin/python
# File:        dst-levelinfos.py
# Description: dst-levelinfos
# Created:     2017-06-24


import os
import argparse

from distance.bytes import DstBytes
from distance.levelinfos import LevelInfos, Level
from distance.levelids import LevelIds
from distance.common import format_bytes


LID_LOST_FORTRESS = 469806096
LID_MAINMENU_DATASTREAM = 822049253

PATH_WS_XML = "~/.config/refract/Distance/Levels/WorkshopLevels/WorkshopPublishedFileIDs.xml"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", type=argparse.FileType('rb'),
                        help="WorkshopLevelInfos.bytes filename")
    args = parser.parse_args()

    dbytes = DstBytes(args.FILE)

    def dump_infos():
        print(f"pos: 0x{dbytes.pos:08x}")
        print(f"level id: {dbytes.read_fixed_number(8)}")
        print(f"next string: {dbytes.read_string()!r}")
        print(f"next string: {dbytes.read_string()}")
        print(f"8 bytes: {format_bytes(dbytes.read_n(8))}")
        print(f"next string: {dbytes.read_string()}")
        print(f"8 bytes: {format_bytes(dbytes.read_n(8))}")
        print(f"next string: {dbytes.read_string()}")
        print(f"next string: {dbytes.read_string()}")
        print(f"24 bytes: {format_bytes(dbytes.read_n(24))}")

    # def handle(key, path):
    #     try:
    #         dbytes.pos = 0
    #         dbytes.find_long_long(int(key))
    #         dump_infos()
    #     except EOFError:
    #         print(f"level not found: {path}")
    # levelids = LevelIds()
    # levelids.handle_entry = handle
    # with open(os.path.expanduser(PATH_WS_XML), 'r', encoding='utf-16-le') as wsxml:
    #     levelids.parse(wsxml)

    # dbytes.find_long_long(LID_LOST_FORTRESS)
    # pos = dbytes.pos
    # dump_infos()
    # dbytes.pos = pos

    # try:
    #     while True:
    #         dump_infos()
    # except EOFError:
    #     pass

    # levels = infos.Level.read_all(dbytes)

    infos = LevelInfos(dbytes)

    # print(levels[-1].title)
    # print(levels[-1].author)
    # print(levels[-1].path)

    total = 0
    prevpos = dbytes.pos
    for level in infos.iter_levels():
        if level.title in {"Red", "Blue", "Yellow", "White", "Main Menu Datastream"}:
            # print(f"{level.title} by {level.author}; pos: {prevpos:08x}")
            savedpos = dbytes.pos
            dbytes.pos -= 8
            print(f"{prevpos:08x} number: {format_bytes(level.unknown[0])} {format_bytes(level.unknown[0], '08b')} {dbytes.read_fixed_number(2)} {level.tags} {level.title}")
            dbytes.pos = savedpos
            total += 1
        prevpos = dbytes.pos
    print(f"total: {total} levels")

    # n = len(levels)
    # s = ""
    # while n > 0x7f:
    #     s += f"{0x80 | (n & 0x7f):02x}"
    #     n >>= 7
    # s += f"{n:02x}"
    # print(s)

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
