
from operator import attrgetter

from construct import (
    Struct, Computed, Rebuild, If, Default,
    Bytes,
    this, len_,
)

from distance.bytes import Magic, Section
from distance.construct import (
    BaseConstructFragment,
    UInt, DstString, ULong,
)
from distance.classes import CollectorGroup
from distance.printing import format_duration


NO_REPLAY = 0xffffffff_ffffffff


Classes = CollectorGroup()


@Classes.fragments.fragment(any_version=True)
class LeaderboardFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x37)

    is_interesting = True

    _construct_ = Struct(
        'version' / Computed(this._params.sec.version),
        'num_entries' / Rebuild(UInt, len_(this.entries)),
        'unk_1' / Bytes(4),
        'unk_2' / If(this.version >= 1, Bytes(4)),
        'entries' / Default(Struct(
            'playername' / DstString,
            'time' / UInt,
            'unk_1' / If(this._.version == 0, UInt),
            'replay' / If(this._.version >= 1, Default(ULong, NO_REPLAY)),
            'unk_2' / If(this._.version >= 1, Bytes(12))
        )[this.num_entries], ()),
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        entries = self.entries
        p(f"Entries: {len(entries)}")
        if 'nosort' not in p.flags:
            nones = [e for e in entries if e.time is None]
            entries = [e for e in entries if e.time is not None]
            entries.sort(key=attrgetter('time'))
            entries.extend(nones)
        for i, entry in enumerate(entries, 1):
            rep_str = ""
            if entry.replay is not None and entry.replay != NO_REPLAY:
                rep_str = f" Replay: {entry.replay:X}"
            p(f"{i}. {entry.playername!r} - {format_duration(entry.time)}{rep_str}")


# vim:set sw=4 et:
