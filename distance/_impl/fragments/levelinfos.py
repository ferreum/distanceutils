

from operator import attrgetter

from construct import (
    Struct, Default, Rebuild, Computed, PrefixedArray, Byte,
    Bytes, StopIf,
    this, len_,
)

from distance.bytes import Magic, Section
from distance.construct import (
    BaseConstructFragment,
    UInt, Int, Float, DstString, MagicConst,
)
from distance.printing import format_duration
from distance.constants import Mode
from distance.classes import CollectorGroup


Classes = CollectorGroup()


@Classes.fragments.fragment
class LevelInfosFragment(BaseConstructFragment):

    default_container = Section(Magic[2], 0x97, 0)

    is_interesting = True

    _construct_ = Struct(
        'version' / Computed(this._params.sec.version),
        'num_entries' / Rebuild(UInt, len_(this.levels)),
        'entry_version' / UInt,
        'levels' / Default(Struct(
            'level_name' / DstString,
            'level_path' / DstString,
            'level_basename' / DstString,
            'unk_0' / Bytes(16),
            MagicConst(12),
            'modes' / Default(PrefixedArray(UInt, Struct(
                'mode' / UInt,
                'enabled' / Byte,
            )), ()),
            'medals' / Struct(
                'time' / Float,
                'score' / Int,
            )[4],
            'unk_1' / Bytes(25),
            StopIf(this._.entry_version < 2),
            'description' / Default(DstString, None),
            'author_name' / Default(DstString, None),
        )[this.num_entries], ()),
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        with p.tree_children(len(self.levels)):
            for level in self.levels:
                p.tree_next_child()
                p(f"Level name: {level.level_name!r}")
                p(f"Level path: {level.level_path!r}")
                p(f"Level basename: {level.level_basename!r}")
                if level.modes:
                    mode_str = ', '.join(Mode.to_name(e.mode)
                                         for e in sorted(level.modes, key=attrgetter('mode'))
                                         if e.enabled)
                    p(f"Enabled modes: {mode_str or 'None'}")
                if level.medals:
                    times_str = ', '.join(format_duration(m.time) for m in reversed(level.medals))
                    p(f"Medal times: {times_str}")
                    scores_str = ', '.join(repr(m.score) for m in reversed(level.medals))
                    p(f"Medal scores: {scores_str}")
                if level.get('author_name', None):
                    p(f"Author: {level.author_name!r}")
                if level.get('description', None) and 'description' in p.flags:
                    p(f"Description: {level.description}")


# vim:set sw=4 et:
