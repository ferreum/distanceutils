#!/usr/bin/python
# File:        leaderboard.py
# Description: leaderboard
# Created:     2017-06-27


from .section import Section, SECTION_TYPE, SECTION_UNK_2


class Entry(object):

    replay = None

    def __init__(self, dbytes, version):
        self.unknown = unknown = []
        if version >= 1:
            unknown.append(dbytes.read_n(4))
            if unknown[0] == b'\x01\x00\x00\x00':
                try:
                    b = dbytes.read_n(1)
                except EOFError:
                    raise
                else:
                    raise IOError(f"expected EOF but got {b!r}")
        else:
            unknown.append(b'')
        self.playername = dbytes.read_string()
        self.time = dbytes.read_fixed_number(4)
        if version == 0:
            unknown.append(dbytes.read_n(4))
        elif version == 1:
            self.replay = dbytes.read_fixed_number(8)
            unknown.append(dbytes.read_n(8))
        else:
            raise IOError(f"unknown version: {version}")

    @staticmethod
    def iter_all(dbytes, version):
        try:
            while True:
                yield Entry(dbytes, version)
        except EOFError:
            pass


class Leaderboard(object):

    def __init__(self, dbytes):
        self.dbytes = dbytes
        self.sections = sections = Section.read_to_map(dbytes, SECTION_UNK_2)
        try:
            ts = sections[SECTION_TYPE]
        except KeyError:
            raise IOError("Missing type information")
        if ts.filetype != "LocalLeaderboard":
            raise IOError(f"Invalid bytes filetype: {ts.filetype!r}")
        self.unknown = unknown = []
        self.version = version = sections[SECTION_UNK_2].version

    def iter_entries(self):
        return Entry.iter_all(self.dbytes, self.version)

    def read_entries(self):
        return list(self.iter_entries())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
