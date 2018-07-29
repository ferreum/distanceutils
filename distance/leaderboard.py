"""LocalLeaderboard .bytes support."""


from operator import attrgetter

from .base import BaseObject, require_type
from .printing import format_duration
from .prober import ProberGroup
from ._default_probers import DefaultProbers


NO_REPLAY = 0xffffffff_ffffffff

FTYPE_LEADERBOARD = "LocalLeaderboard"


Probers = ProberGroup()


@Probers.non_level_objects.object
@DefaultProbers.fragments.fragment_attrs('Leaderboard')
@require_type
class Leaderboard(BaseObject):

    type = FTYPE_LEADERBOARD

    def _print_data(self, p):
        super()._print_data(p)
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


# vim:set sw=4 ts=8 sts=4 et:
