"""ProfilePrgress .bytes support."""


from collections import OrderedDict
from itertools import islice

from .bytes import (BytesModel, S_DOUBLE,
                    MAGIC_1, MAGIC_2)
from .common import format_duration, format_duration_dhms, format_distance
from .constants import Completion, Mode, TIMED_MODES


FTYPE_PROFILEPROGRESS = 'ProfileProgress'


def format_score(mode, score, comp):
    comp_str = Completion.to_name(comp)
    mode_str = Mode.to_name(mode)
    if mode in TIMED_MODES:
        type_str = "time"
        if score < 0:
            score_str = "None"
        else:
            score_str = format_duration(score)
    else:
        type_str = "score"
        if score < 0:
            score_str = "None"
        else:
            score_str = str(score)
    return f"{mode_str} {type_str}: {score_str} ({comp_str})"


class LevelProgress(BytesModel):

    level_path = None
    completion = ()
    scores = ()

    def _read(self, dbytes, version=None):
        self.level_path = dbytes.read_str()
        self.recoverable = True
        self._add_unknown(value=dbytes.read_str())
        self._add_unknown(1)

        self._require_equal(MAGIC_1, 4)
        num_levels = dbytes.read_int(4)
        self.completion = completion = []
        for i in range(num_levels):
            completion.append(dbytes.read_int(4))

        self._require_equal(MAGIC_1, 4)
        num_levels = dbytes.read_int(4)
        self.scores = scores = []
        for i in range(num_levels):
            scores.append(dbytes.read_int(4, signed=True))
        if version > 2:
            self._add_unknown(8)

    def _print_data(self, p):
        p(f"Level path: {self.level_path!r}")
        for mode, (score, comp) in enumerate(zip(self.scores, self.completion)):
            if comp != Completion.UNPLAYED:
                p(format_score(mode, score, comp))


class Stat(object):

    def __init__(self, type, ident, unit='num', nbytes=None):
        if type == 'd':
            def _read(dbytes):
                return dbytes.read_struct(S_DOUBLE)[0]
        elif type == 'u8':
            def _read(dbytes):
                return dbytes.read_int(8)
        elif type == 'unk':
            def _read(dbytes):
                return dbytes.read_n(nbytes)
        else:
            raise ValueError(f"invalid type: {type!r}")
        self.read_value = _read
        if unit == 'sec':
            self.format = lambda v: format_duration_dhms(v * 1000)
        elif unit == 'num':
            self.format = str
        elif unit == 'unknown':
            self.format = str
        elif unit == 'meters':
            self.format = format_distance
        elif unit == 'ev':
            self.format = lambda v: f"{v:,d} eV"
        else:
            raise ValueError(f"invalid unit: {unit!r}")
        self.ident = ident
        self.type = type
        self.unit = unit

    def read_value(self, dbytes):
        raise NotImplementedError


class AttrOrderedDict(OrderedDict):

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


STATS = AttrOrderedDict((s.ident, s) for s in (
    Stat('u8', 'deaths'),
    Stat('u8', 'laser_deaths'),
    Stat('u8', 'reset_deaths'),
    Stat('u8', 'impact_deaths'),
    Stat('u8', 'overheat_deaths'),
    Stat('u8', 'killgrid_deaths'),
    Stat('d', 'gibs_time', 'sec'),
    Stat('d', 'unk_0', 'meters'),
    Stat('d', 'forward', 'meters'),
    Stat('d', 'reverse', 'meters'),
    Stat('d', 'air_fly', 'meters'),
    Stat('d', 'air_nofly', 'meters'),
    Stat('d', 'wallride', 'meters'),
    Stat('d', 'ceilingride', 'meters'),
    Stat('d', 'grinding', 'meters'),
    Stat('d', 'boost', 'sec'),
    Stat('d', 'grip', 'sec'),
    Stat('u8', 'splits'),
    Stat('u8', 'impacts'),
    Stat('u8', 'checkpoints'),
    Stat('u8', 'jumps'),
    Stat('u8', 'wings'),
    Stat('u8', 'unk_1', 'unknown'),
    Stat('u8', 'horns'),
    Stat('u8', 'tricks'),
    Stat('u8', 'ev', 'ev'),
    Stat('u8', 'lamps'),
    Stat('u8', 'pumpkins'),
    Stat('u8', 'eggs'),
    Stat('u8', 'unk_2', 'unknown'),
    Stat('u8', 'unk_3', 'unknown'),
    Stat('u8', 'unk_4', 'unknown'),
    Stat('u8', 'cooldowns'),
    Stat('d', 'total', 'sec'),
    Stat('d', 'editor_working', 'sec'),
    Stat('d', 'editor_playing', 'sec'),
))


class PlayerStats(BytesModel):

    version = None
    stats = {}
    modes_offline = ()
    modes_online = ()
    trackmogrify_mods = ()

    def _read(self, dbytes, version=None):
        def read_double():
            return dbytes.read_struct(S_DOUBLE)[0]
        self.version = version
        self.recoverable = True

        self.stats = stats = {}
        for k, stat in STATS.items():
            stats[k] = stat.read_value(dbytes)

        self._require_equal(MAGIC_1, 4)
        num = dbytes.read_int(4)
        self.modes_offline = offline_times = []
        for i in range(num):
            offline_times.append(read_double())

        self._require_equal(MAGIC_1, 4)
        num = dbytes.read_int(4)
        modes_unknown = self._add_unknown(value=[])
        for i in range(num):
            modes_unknown.append(dbytes.read_int(8))

        self._require_equal(MAGIC_1, 4)
        num = dbytes.read_int(4)
        self.modes_online = online_times = []
        for i in range(num):
            online_times.append(read_double())

        if version >= 6:
            self._add_unknown(8)
            self._require_equal(MAGIC_1, 4)
            num = dbytes.read_int(4)
            self.trackmogrify_mods = mods = []
            for i in range(num):
                mods.append(dbytes.read_str())

    def _print_data(self, p):
        p(f"Player stats version: {self.version}")
        s = STATS
        values = self.stats

        def ps(stat, name):
            value = values.get(stat.ident, None)
            if value is None:
                val_str = "None"
            else:
                val_str = stat.format(value)
            p.tree_next_child()
            p(f"{name}: {val_str}")

        ps(s.total, "All play time")
        with p.tree_children():
            total_in_modes = sum(self.modes_offline) + sum(self.modes_online)
            p.tree_next_child()
            p(f"Total time in modes: {format_duration_dhms(total_in_modes * 1000)}")
            total_offline = sum(self.modes_offline)
            total_online = sum(self.modes_online)
            p.tree_next_child()
            p(f"Total time in offline modes: {format_duration_dhms(total_offline * 1000)}")
            with p.tree_children():
                for mode, time in enumerate(self.modes_offline):
                    if time >= 0.001:
                        p.tree_next_child()
                        p(f"Time playing {Mode.to_name(mode)} offline: {format_duration_dhms(time * 1000)}")
            p.tree_next_child()
            p(f"Total time in online modes: {format_duration_dhms(total_online * 1000)}")
            with p.tree_children():
                for mode, time in enumerate(self.modes_online):
                    if time >= 0.001:
                        p.tree_next_child()
                        p(f"Time playing {Mode.to_name(mode)} online: {format_duration_dhms(time * 1000)}")
            ps(s.editor_working, "Time working in editor")
            ps(s.editor_playing, "Time playing in editor")

        total_distance = sum(values.get(stat.ident) for stat in
                             (s.forward, s.reverse, s.air_fly, s.air_nofly))
        ps(s.deaths, "Total deaths")
        with p.tree_children():
            ps(s.impact_deaths, "Impact deaths")
            ps(s.killgrid_deaths, "Killgrid deaths")
            ps(s.laser_deaths, "Laser deaths")
            ps(s.overheat_deaths, "Overheat deaths")
            ps(s.reset_deaths, "Reset deaths")
            ps(s.gibs_time, "Gibs time")
        ps(s.impacts, "Impact count")
        ps(s.splits, "Split count")
        ps(s.checkpoints, "Checkpoints hit")
        ps(s.cooldowns, "Cooldowns hit")
        p(f"Distance traveled: {format_distance(total_distance)}")
        with p.tree_children():
            ps(s.forward, "Distance driven forward")
            ps(s.reverse, "Distance driven reverse")
            ps(s.air_fly, "Distance airborn flying")
            ps(s.air_nofly, "Distance airborn not flying")
            ps(s.wallride, "Distance wall riding")
            ps(s.ceilingride, "Distance ceiling riding")
            ps(s.grinding, "Distance grinding")
        ps(s.lamps, "Lamps broken")
        ps(s.pumpkins, "Pumpkins smashed")
        ps(s.eggs, "Eggs cracked")
        ps(s.boost, "Boost held down time")
        ps(s.grip, "Grip held down time")
        ps(s.jumps, "Jump count")
        ps(s.wings, "Wings count")
        ps(s.horns, "Horn count")
        if total_in_modes:
            avg_speed = total_distance / total_in_modes * 3.6
        else:
            avg_speed = "None"
        p(f"Average speed: {avg_speed}")

        mods = self.trackmogrify_mods
        if mods:
            p(f"Found trackmogrify mods: {len(mods)}")
            with p.tree_children():
                for i in range(0, len(mods), 5):
                    mods_str = ', '.join(repr(m) for m in islice(mods, i, i + 5))
                    p.tree_next_child()
                    p(f"Found: {mods_str}")


class ProfileProgress(BytesModel):

    level_s2 = None
    num_levels = None
    stats_s2 = None

    def _read(self, dbytes):
        ts = self._require_type(FTYPE_PROFILEPROGRESS)
        self._report_end_pos(ts.data_end)
        self._read_sections(ts.data_end)

    def _read_section_data(self, dbytes, sec):
        if sec.magic == MAGIC_2:
            if sec.ident == 0x6A:
                self.level_s2 = sec
                self.num_levels = dbytes.read_int(4)
                return True
            elif sec.ident == 0x8E:
                self.stats_s2 = sec
                return True
        return BytesModel._read_section_data(self, dbytes, sec)

    def iter_levels(self):
        s2 = self.level_s2
        if s2 is None:
            return
        data_end = s2.data_end
        dbytes = self.dbytes
        dbytes.pos = s2.data_start + 20
        with dbytes.limit(data_end):
            num = self.num_levels
            if num:
                for obj in LevelProgress.iter_n_maybe(
                        dbytes, num, version=s2.version):
                    yield obj
        self.off_mapname_start = dbytes.pos

    def iter_official_levels(self):
        dbytes = self.dbytes
        dbytes.pos = self.off_mapname_start
        self._require_equal(MAGIC_1, 4)
        num_maps = dbytes.read_int(4)
        def gen():
            for i in range(num_maps):
                yield dbytes.read_str()
            self.found_tricks_start = dbytes.pos + 36
        return gen(), num_maps

    def iter_tricks(self):
        dbytes = self.dbytes
        if self.level_s2.version < 6:
            return (), 0
        dbytes.pos = self.found_tricks_start
        self._require_equal(MAGIC_1, 4)
        num_tricks = dbytes.read_int(4)
        def gen():
            for i in range(num_tricks):
                yield dbytes.read_str()
            self.adventure_levels_start = dbytes.pos
        return gen(), num_tricks

    def iter_unlocked_adventure(self):
        if self.level_s2.version < 6:
            return (), 0
        dbytes = self.dbytes
        dbytes.pos = self.adventure_levels_start
        self._require_equal(MAGIC_1, 4)
        num_advlevels = dbytes.read_int(4)
        def gen():
            for i in range(num_advlevels):
                yield dbytes.read_str()
            self.somelevel_list_start = dbytes.pos + 10
        return gen(), num_advlevels

    def iter_somelevels(self):
        if self.level_s2.version < 6:
            return (), 0
        dbytes = self.dbytes
        dbytes.pos = self.somelevel_list_start
        self._require_equal(MAGIC_1, 4)
        num_somelevels = dbytes.read_int(4)
        def gen():
            for i in range(num_somelevels):
                yield dbytes.read_str()
        return gen(), num_somelevels

    def read_stats(self):
        s2 = self.stats_s2
        if s2 is None:
            return None
        dbytes = self.dbytes
        dbytes.pos = s2.data_start + 16
        with dbytes.limit(s2.data_end):
            return PlayerStats.maybe(dbytes, version=s2.version)

    def _print_data(self, p):
        if self.level_s2:
            p(f"Level progress version: {self.level_s2.version}")
            p(f"Level count: {self.num_levels}")
            with p.tree_children():
                for level in self.iter_levels():
                    p.tree_next_child()
                    p.print_data_of(level)
            gen, length = self.iter_official_levels()
            if length:
                p(f"Unlocked levels: {length}")
            with p.tree_children():
                # need to ensure that gen is exhausted
                gen = iter(list(gen))
                for _ in range(0, length, 5):
                    p.tree_next_child()
                    l_str = ', '.join(repr(n) for n in islice(gen, 5))
                    p(f"Levels: {l_str}")
            gen, length = self.iter_tricks()
            if length:
                p(f"Found tricks: {length}")
            with p.tree_children():
                # need to ensure that gen is exhausted
                gen = iter(list(gen))
                for _ in range(0, length, 5):
                    p.tree_next_child()
                    t_str = ', '.join(repr(t) for t in islice(gen, 5))
                    p(f"Tricks: {t_str}")
            gen, length = self.iter_unlocked_adventure()
            if length:
                p(f"Unlocked adventure stages: {length}")
            with p.tree_children():
                for advlevel in gen:
                    p.tree_next_child()
                    p(f"Level: {advlevel!r}")
            gen, length = self.iter_somelevels()
            if length:
                p(f"Some levels: {length}")
            with p.tree_children():
                for somelevel in gen:
                    p.tree_next_child()
                    p(f"Level: {somelevel!r}")
            stats = self.read_stats()
            if stats:
                p.print_data_of(stats)
        else:
            p("No level progress")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
