#!/usr/bin/python
# File:        leaderboard.py
# Description: leaderboard
# Created:     2017-06-27


from operator import attrgetter
import sys

from .bytes import (BytesModel, SECTION_TYPE, SECTION_UNK_2,
                    print_exception)
from .common import format_bytes, format_duration


NO_REPLAY = 0xffffffffffffffff

FTYPE_LEADERBOARD = "LocalLeaderboard"


class Entry(BytesModel):

    playername = None
    time = None
    replay = None

    def parse(self, dbytes, version=None):
        self.playername = dbytes.read_string()
        self.recoverable = True
        self.time = dbytes.read_fixed_number(4)
        if version == 0:
            self.add_unknown(4)
        elif version == 1:
            self.replay = dbytes.read_fixed_number(8)
            self.add_unknown(12)
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
        self.require_type(FTYPE_LEADERBOARD)
        self.version = version = self.require_section(SECTION_UNK_2).version
        self.add_unknown(12)
        if version >= 1:
            self.add_unknown(4)

    def iter_entries(self):
        try:
            while True:
                entry, sane, exc = Entry.maybe_partial(self.dbytes, version=self.version)
                yield entry
                if not sane:
                    break
        except EOFError:
            pass

    def read_entries(self):
        entries = []
        try:
            for entry in self.iter_entries():
                entries.append(entry)
            return entries, None
        except:
            return entries, sys.exc_info()

    def _print_data(self, file, unknown, p):
        p(f"Version: {self.version}")
        entries, exception = self.read_entries()
        nones = [e for e in entries if e.time is None]
        entries = [e for e in entries if e.time is not None]
        entries.sort(key=attrgetter('time'))
        entries.extend(nones)
        unk_str = ""
        for i, entry in enumerate(entries, 1):
            rep_str = ""
            if entry.replay is not None and entry.replay != NO_REPLAY:
                rep_str = f" Replay: {entry.replay:X}"
            if unknown:
                unk_str = f"Unknown: {format_bytes(entry.unknown)} "
            p(f"{unk_str}{i}. {entry.playername!r} - {format_duration(entry.time)}{rep_str}")
            if entry.exception:
                print_exception(entry.exception, file, p)
        if exception:
            print_exception(exception, file, p)



# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
