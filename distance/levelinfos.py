"""LevelInfos .bytes support."""


from .bytes import BytesModel, MAGIC_2, MAGIC_12, S_FLOAT
from .base import BaseObject
from .printing import format_duration
from .constants import Mode


FTYPE_LEVELINFOS = 'LevelInfos'


class Entry(BytesModel):

    level_name = None
    level_path = None
    level_basename = None
    modes = ()
    medal_times = ()
    medal_scores = ()

    def _read(self, dbytes):
        self.level_name = dbytes.read_str()
        self.level_path = dbytes.read_str()
        self.level_basename = dbytes.read_str()
        self._add_unknown(16)
        self._require_equal(MAGIC_12, 4)
        num_modes = dbytes.read_int(4)
        self.modes = modes = {}
        for _ in range(num_modes):
            mode = dbytes.read_int(4)
            modes[mode] = dbytes.read_byte()
        self.medal_times = times = []
        self.medal_scores = scores = []
        for _ in range(4):
            times.append(dbytes.read_struct(S_FLOAT)[0])
            scores.append(dbytes.read_int(4, signed=True))
        self._add_unknown(25)

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


class LevelInfos(BaseObject):

    version = None

    def _read(self, dbytes):
        self._require_type(FTYPE_LEVELINFOS)
        BaseObject._read(self, dbytes)

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_2, 0x97):
            self.version = sec.version
            num_entries = dbytes.read_int(8)
            self.levels = Entry.lazy_n_maybe(dbytes, num_entries)
            return False
        return BaseObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        p(f"Version: {self.version}")
        p(f"Level entries: {len(self.levels)}")
        with p.tree_children():
            for entry in self.levels:
                p.tree_next_child()
                p.print_data_of(entry)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
