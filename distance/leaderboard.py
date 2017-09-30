"""LocalLeaderboard .bytes support."""


from operator import attrgetter

from .bytes import BytesModel, MAGIC_2
from .base import BaseObject
from .printing import format_bytes, format_duration


NO_REPLAY = 0xffffffffffffffff

FTYPE_LEADERBOARD = "LocalLeaderboard"


class Entry(BytesModel):

    playername = None
    time = None
    replay = None

    def _read(self, dbytes, version=None):
        self.playername = dbytes.read_str()
        self.time = dbytes.read_int(4)
        if version == 0:
            self._add_unknown(4)
        elif version == 1:
            self.replay = dbytes.read_int(8)
            self._add_unknown(12)
        else:
            raise ValueError(f"unknown version: {version}")


class Leaderboard(BaseObject):

    version = None

    def _read(self, dbytes):
        ts = self._require_type(FTYPE_LEADERBOARD)
        self._report_end_pos(ts.data_end)
        self._read_sections(ts.data_end)

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_2, 0x37):
            self.version = version = sec.version
            num_entries = dbytes.read_int(4)
            start = sec.data_start + 20
            if version >= 1:
                start += 4
            self.entries = Entry.lazy_n_maybe(dbytes, num_entries,
                                              start_pos=start,
                                              version=version)
            return False
        return BaseObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        p(f"Version: {self.version}")
        entries = self.entries
        p(f"Entries: {len(entries)}")
        if 'nosort' not in p.flags:
            nones = [e for e in entries if e.time is None]
            entries = [e for e in entries if e.time is not None]
            entries.sort(key=attrgetter('time'))
            entries.extend(nones)
        unk_str = ""
        for i, entry in enumerate(entries, 1):
            rep_str = ""
            if entry.replay is not None and entry.replay != NO_REPLAY:
                rep_str = f" Replay: {entry.replay:X}"
            if 'unknown' in p.flags:
                unk_str = f"Unknown: {format_bytes(entry.unknown)} "
            p(f"{unk_str}{i}. {entry.playername!r} - {format_duration(entry.time)}{rep_str}")
            if entry.exception:
                p.print_exception(entry.exception)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
