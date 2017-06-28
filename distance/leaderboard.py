#!/usr/bin/python
# File:        leaderboard.py
# Description: leaderboard
# Created:     2017-06-27


from operator import attrgetter

from .bytes import BytesModel, SECTION_TYPE, SECTION_UNK_2
from .common import format_bytes, format_duration


NO_REPLAY = 0xffffffffffffffff

FTYPE_LEADERBOARD = "LocalLeaderboard"


class Entry(BytesModel):

    replay = None

    def parse(self, dbytes, version=None):
        if version >= 1:
            self.add_unknown(4)
        else:
            self.add_unknown(0)
        self.playername = dbytes.read_string()
        self.time = dbytes.read_fixed_number(4)
        if version == 0:
            self.add_unknown(4)
        elif version == 1:
            self.replay = dbytes.read_fixed_number(8)
            self.add_unknown(8)
        else:
            raise IOError(f"unknown version: {version}")

    @staticmethod
    def iter_all(dbytes, version):
        try:
            while True:
                yield Entry(dbytes, version=version)
        except EOFError:
            pass


class Leaderboard(BytesModel):

    def parse(self, dbytes):
        sections = self.read_sections_to(SECTION_UNK_2)
        ts = sections.get(SECTION_TYPE, ())
        if not ts:
            raise IOError("Missing type information")
        if ts[0].filetype != FTYPE_LEADERBOARD:
            raise IOError(f"Invalid bytes filetype: {ts.filetype!r}")
        self.version = sections[SECTION_UNK_2][0].version
        self.add_unknown(12)

    def iter_entries(self):
        return Entry.iter_all(self.dbytes, self.version)

    def read_entries(self):
        return list(self.iter_entries())

    def print_data(self, file, unknown=False):
        BytesModel.print_data(self, file, unknown=unknown)
        def p(*args):
            print(*args, file=file)
        p(f"Version: {self.version}")
        entries = self.read_entries()
        entries.sort(key=attrgetter('time'))
        unk_str = ""
        for i, entry in enumerate(entries, 1):
            rep_str = ""
            if entry.replay is not None and entry.replay != NO_REPLAY:
                rep_str = f" Replay: {entry.replay:X}"
            if unknown:
                unk_str = f"Unknown: {format_bytes(entry.unknown)} "
            p(f"{unk_str}{i}. {entry.playername!r} - {format_duration(entry.time)}{rep_str}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
