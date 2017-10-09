"""LocalLeaderboard .bytes support."""


from operator import attrgetter

from .bytes import BytesModel, MAGIC_2
from .base import BaseObject, Fragment, ForwardFragmentAttrs
from .prober import BytesProber
from .printing import format_duration


NO_REPLAY = 0xffffffffffffffff

FTYPE_LEADERBOARD = "LocalLeaderboard"


FRAG_PROBER = BytesProber()
FRAG_PROBER.extend(BaseObject.fragment_prober)


class Entry(BytesModel):

    playername = None
    time = None
    replay = None

    def _read(self, dbytes, version=None):
        self.playername = dbytes.read_str()
        self.time = dbytes.read_uint4()
        if version == 0:
            dbytes.read_bytes(4)
        elif version == 1:
            self.replay = dbytes.read_uint8()
            dbytes.read_bytes(12)
        else:
            raise ValueError(f"unknown version: {version}")


@FRAG_PROBER.fragment(MAGIC_2, 0x37, any_version=True)
class LeaderboardFragment(Fragment):

    version = None
    entries = None

    def _read_section_data(self, dbytes, sec):
        self.version = version = sec.version
        num_entries = dbytes.read_uint4()
        start = sec.content_start + 8
        if version >= 1:
            start += 4
        self.entries = Entry.lazy_n_maybe(dbytes, num_entries,
                                          start_pos=start,
                                          version=version)


@ForwardFragmentAttrs(LeaderboardFragment, version=None, entries=())
class Leaderboard(BaseObject):

    fragment_prober = FRAG_PROBER

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
            p(f"{unk_str}{i}. {entry.playername!r} - {format_duration(entry.time)}{rep_str}")
            if entry.exception:
                p.print_exception(entry.exception)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
