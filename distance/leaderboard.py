"""LocalLeaderboard .bytes support."""


from operator import attrgetter

from construct import (
    Struct, Computed, Rebuild, If, Default,
    Bytes,
    this, len_,
)

from .bytes import Magic, Section
from .base import (
    BaseObject,
    ForwardFragmentAttrs,
    require_type,
)
from .construct import (
    BaseConstructFragment,
    UInt, DstString, Long,
)
from .printing import format_duration
from ._default_probers import DefaultProbers


NO_REPLAY = 0xffffffff_ffffffff

FTYPE_LEADERBOARD = "LocalLeaderboard"


FILE_PROBER = DefaultProbers.file.transaction()
FRAG_PROBER = DefaultProbers.fragments.transaction()


@FRAG_PROBER.fragment(any_version=True)
class LeaderboardFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x37)

    _construct = Struct(
        version = Computed(this._params.sec.version),
        num_entries = Rebuild(UInt, len_(this.entries)),
        unk_1 = Bytes(4),
        unk_2 = If(this.version >= 1, Bytes(4)),
        entries = Struct(
            playername = DstString,
            time = UInt,
            unk_1 = If(this._.version == 0, UInt),
            replay = If(this._.version >= 1, Default(Long, NO_REPLAY)),
            unk_2 = If(this._.version >= 1, Bytes(12))
        )[this.num_entries],
    )


@FILE_PROBER.for_type
@ForwardFragmentAttrs(LeaderboardFragment, **LeaderboardFragment._fields_map)
@require_type
class Leaderboard(BaseObject):

    type = FTYPE_LEADERBOARD

    def _print_data(self, p):
        super()._print_data(p)
        p(f"Version: {self.version}")
        entries = self.entries or ()
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


FRAG_PROBER.commit()
FILE_PROBER.commit()


# vim:set sw=4 ts=8 sts=4 et:
