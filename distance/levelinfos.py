"""LevelInfos .bytes support."""


from .bytes import BytesModel, MAGIC_2, MAGIC_12, S_FLOAT
from .base import (
    BaseObject, Fragment,
    BASE_FRAG_PROBER,
    ForwardFragmentAttrs,
    require_type,
)
from .printing import format_duration
from .constants import Mode
from .prober import BytesProber


FTYPE_LEVELINFOS = 'LevelInfos'


FRAG_PROBER = BytesProber()

FRAG_PROBER.extend(BASE_FRAG_PROBER)


class Entry(BytesModel):

    level_name = None
    level_path = None
    level_basename = None
    modes = ()
    medal_times = ()
    medal_scores = ()
    description = None
    author_name = None

    def _read(self, dbytes, version=0):
        self.level_name = dbytes.read_str()
        self.level_path = dbytes.read_str()
        self.level_basename = dbytes.read_str()
        dbytes.read_bytes(16)
        dbytes.require_equal_uint4(MAGIC_12)
        num_modes = dbytes.read_uint4()
        self.modes = modes = {}
        for _ in range(num_modes):
            mode = dbytes.read_uint4()
            modes[mode] = dbytes.read_byte()
        self.medal_times = times = []
        self.medal_scores = scores = []
        for _ in range(4):
            times.append(dbytes.read_struct(S_FLOAT)[0])
            scores.append(dbytes.read_int4())
        dbytes.read_bytes(25)
        if version >= 2:
            self.description = dbytes.read_str()
            self.author_name = dbytes.read_str()

    def _print_data(self, p):
        p(f"Level name: {self.level_name!r}")
        p(f"Level path: {self.level_path!r}")
        p(f"Level basename: {self.level_basename!r}")
        if self.modes:
            mode_str = ', '.join(Mode.to_name(m) for m, e in sorted(self.modes.items()) if e)
            p(f"Enabled modes: {mode_str or 'None'}")
        if self.medal_times:
            times_str = ', '.join(format_duration(t) for t in reversed(self.medal_times))
            p(f"Medal times: {times_str}")
        if self.medal_scores:
            scores_str = ', '.join(str(s) for s in reversed(self.medal_scores))
            p(f"Medal scores: {scores_str}")
        if self.author_name:
            p(f"Author: {self.author_name!r}")
        if self.description and 'description' in p.flags:
            p(f"Description: {self.description}")


@FRAG_PROBER.fragment(MAGIC_2, 0x97, 0)
class LevelInfosFragment(Fragment):

    version = None
    levels = ()

    def _read_section_data(self, dbytes, sec):
        self.version = sec.version
        num_entries = dbytes.read_uint4()
        entry_version = dbytes.read_uint4()
        self.levels = Entry.lazy_n_maybe(
            dbytes, num_entries, version=entry_version)


@ForwardFragmentAttrs(LevelInfosFragment, levels=(), version=None)
@require_type(FTYPE_LEVELINFOS)
class LevelInfos(BaseObject):

    fragment_prober = FRAG_PROBER

    def _print_data(self, p):
        p(f"Version: {self.version}")
        p(f"Level entries: {len(self.levels)}")
        with p.tree_children():
            for entry in self.levels:
                p.tree_next_child()
                p.print_data_of(entry)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
