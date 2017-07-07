#!/usr/bin/python
# File:        levelinfos.py
# Description: levelinfos
# Created:     2017-07-07


from .bytes import BytesModel, SECTION_UNK_2, S_FLOAT
from .common import format_duration
from .constants import Mode


FTYPE_LEVELINFOS = 'LevelInfos'


class Entry(BytesModel):

    level_name = None
    level_path = None
    level_basename = None
    modes = ()
    medal_times = ()
    medal_scores = ()

    def parse(self, dbytes):
        self.level_name = dbytes.read_string()
        self.recoverable = True
        self.level_path = dbytes.read_string()
        self.level_basename = dbytes.read_string()
        self.add_unknown(16)
        self.require_equal(12121212, 4)
        num_modes = dbytes.read_fixed_number(4)
        self.modes = modes = {}
        for _ in range(num_modes):
            mode = dbytes.read_fixed_number(4)
            modes[mode] = dbytes.read_byte()
        self.medal_times = times = []
        self.medal_scores = scores = []
        for _ in range(4):
            times.append(dbytes.read_struct(S_FLOAT)[0])
            scores.append(dbytes.read_fixed_number(4, signed=True))
        self.add_unknown(25)

    def _print_data(self, p):
        p(f"Level name: {self.level_name!r}")
        p(f"Level path: {self.level_path!r}")
        p(f"Level basename: {self.level_basename!r}")
        if self.modes:
            mode_str = ', '.join(Mode.to_name(m) for m, e in sorted(self.modes.items()) if e)
            p(f"Enabled modes: {mode_str}")
        if self.medal_times:
            times_str = ', '.join(format_duration(t) for t in reversed(self.medal_times))
            p(f"Medal times: {times_str}")
        if self.medal_scores:
            scores_str = ', '.join(str(s) for s in reversed(self.medal_scores))
            p(f"Medal scores: {scores_str}")


class LevelInfos(BytesModel):

    def parse(self, dbytes):
        ts = self.require_type(FTYPE_LEVELINFOS)
        self.recoverable = True
        s2 = self.require_section(SECTION_UNK_2)
        self.version = s2.version
        self.entries_s2 = s2
        self.add_unknown(4)

    def iter_levels(self):
        dbytes = self.dbytes
        self.num_entries = length = dbytes.read_fixed_number(8)
        s2 = self.entries_s2
        def gen():
            with dbytes.limit(s2.data_end):
                for _ in range(length):
                    yield Entry.maybe_partial(dbytes)
        return gen(), length

    def _print_data(self, p):
        p(f"Version: {self.version}")
        gen, length = self.iter_levels()
        if length:
            p(f"Level entries: {length}")
        with p.tree_children(length):
            for entry, sane, exc in gen:
                p.tree_next_child()
                p.print_data_of(entry)
                if not sane:
                    break


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
