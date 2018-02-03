"""ProfilePrgress .bytes support."""


from collections import OrderedDict
from itertools import islice

from .bytes import BytesModel, S_DOUBLE, MAGIC_1, MAGIC_2
from .base import (
    BaseObject, Fragment,
    BASE_FRAG_PROBER,
    ForwardFragmentAttrs,
    require_type,
)
from .printing import format_duration, format_duration_dhms, format_distance
from .constants import Completion, Mode, TIMED_MODES
from .prober import BytesProber


FTYPE_PROFILEPROGRESS = 'ProfileProgress'

FRAG_PROBER = BytesProber()

FRAG_PROBER.extend(BASE_FRAG_PROBER)


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
        dbytes.read_str() # unknown
        dbytes.read_bytes(1) # unknown

        dbytes.require_equal_uint4(MAGIC_1)
        num_levels = dbytes.read_uint4()
        self.completion = completion = []
        for i in range(num_levels):
            completion.append(dbytes.read_uint4())

        dbytes.require_equal_uint4(MAGIC_1)
        num_levels = dbytes.read_uint4()
        self.scores = scores = []
        for i in range(num_levels):
            scores.append(dbytes.read_int4())
        if version > 2:
            dbytes.read_bytes(8)

    def _print_data(self, p):
        p(f"Level path: {self.level_path!r}")
        for mode, (score, comp) in enumerate(zip(self.scores, self.completion)):
            if comp != Completion.UNPLAYED:
                p(format_score(mode, score, comp))


class StringEntry(BytesModel):

    value = None

    def _read(self, dbytes):
        self.value = dbytes.read_str()

    def _write(self, dbytes):
        dbytes.write_str(self.value)


class Stat(object):

    def __init__(self, type, ident, unit='num', nbytes=None):
        if type == 'd':
            def _read(dbytes):
                return dbytes.read_struct(S_DOUBLE)[0]
        elif type == 'u8':
            def _read(dbytes):
                return dbytes.read_uint8()
        elif type == 'unk':
            def _read(dbytes):
                return dbytes.read_bytes(nbytes)
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


@FRAG_PROBER.fragment(MAGIC_2, 0x8e, any_version=True)
class ProfileStatsFragment(Fragment):

    version = None
    stats = {}
    modes_offline = ()
    modes_online = ()
    trackmogrify_mods = ()

    def _read_section_data(self, dbytes, sec):
        def read_double():
            return dbytes.read_struct(S_DOUBLE)[0]
        self.version = version = sec.version

        dbytes.read_bytes(4) # unknown

        self.stats = stats = {}
        for k, stat in STATS.items():
            stats[k] = stat.read_value(dbytes)

        dbytes.require_equal_uint4(MAGIC_1)
        num = dbytes.read_uint4()
        self.modes_offline = offline_times = []
        for i in range(num):
            offline_times.append(read_double())

        dbytes.require_equal_uint4(MAGIC_1)
        num = dbytes.read_uint4()
        self.modes_unknown = modes_unknown = []
        for i in range(num):
            modes_unknown.append(dbytes.read_uint8())

        dbytes.require_equal_uint4(MAGIC_1)
        num = dbytes.read_uint4()
        self.modes_online = online_times = []
        for i in range(num):
            online_times.append(read_double())

        if version >= 6:
            dbytes.add_read_bytes(8)
            dbytes.require_equal_uint4(MAGIC_1)
            num = dbytes.read_uint4()
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


@FRAG_PROBER.fragment(MAGIC_2, 0x6a, any_version=True)
class ProfileProgressFragment(Fragment):

    value_attrs = dict(
        levels = (),
        officials = (),
        official_levels = (),
        tricks = (),
        unlocked_adventures = (),
        somelevels = (),
    )

    version = None
    levels = ()
    _officials = None
    _official_levels = None
    _tricks = None
    _unlocked_adventures = None
    _somelevels = None

    def _read_section_data(self, dbytes, sec):
        self.version = sec.version
        num_levels = dbytes.read_uint4()
        self._data_start = start = dbytes.tell() + 4
        self.levels = LevelProgress.lazy_n_maybe(
            dbytes, num_levels, start_pos=start,
            version=sec.version)

    def _officials_start_pos(self):
        levels = self.levels
        if levels:
            last = levels[-1]
            if not last.sane_end_pos:
                return None
            return last.end_pos
        else:
            return self._data_start

    @property
    def officials(self):
        lazy = self._official_levels
        if lazy is None:
            dbytes = self.dbytes
            dbytes.seek(self._officials_start_pos())
            dbytes.require_equal_uint4(MAGIC_1)
            num = dbytes.read_uint4()
            lazy = StringEntry.lazy_n_maybe(dbytes, num)
            self.lazy = lazy
        return lazy

    def _tricks_start_pos(self):
        officials = self.officials
        if officials:
            last = officials[-1]
            if not last.sane_end_pos:
                return None
            # officials_end + 36b (unknown)
            return last.end_pos + 36
        else:
            # officials_start + 4b (s1) + 4b (num_officials) + 36b (unknown)
            return self._officials_start_pos() + 8 + 36

    @property
    def tricks(self):
        tricks = self._tricks
        if tricks is None:
            if self.version < 6:
                tricks = ()
            else:
                dbytes = self.dbytes
                dbytes.seek(self._tricks_start_pos())
                dbytes.require_equal_uint4(MAGIC_1)
                num = dbytes.read_uint4()
                tricks = StringEntry.lazy_n_maybe(dbytes, num)
            self._tricks = tricks
        return tricks

    def _adventures_start_pos(self):
        tricks = self.tricks
        if tricks:
            last = tricks[-1]
            if not last.sane_end_pos:
                return None
            return last.end_pos
        else:
            # officials_start + 4b (s1) + 4b (num_tricks)
            return self._tricks_start_pos() + 8

    @property
    def unlocked_adventures(self):
        adventures = self._unlocked_adventures
        if adventures is None:
            if self.version < 6:
                adventures = ()
            else:
                dbytes = self.dbytes
                dbytes.seek(self._adventures_start_pos())
                dbytes.require_equal_uint4(MAGIC_1)
                num = dbytes.read_uint4()
                adventures = StringEntry.lazy_n_maybe(dbytes, num)
            self._unlocked_adventures = adventures
        return adventures

    def _somelevels_start_pos(self):
        adventures = self.unlocked_adventures
        if adventures:
            last = adventures[-1]
            if not last.sane_end_pos:
                return None
            # last pos + 10b (unknown)
            return last.end_pos + 10
        else:
            # unlocks_start + 4b (s1) + 4b (num_unlocks) + 10 (unknown)
            return self._adventures_start_pos() + 18

    @property
    def somelevels(self):
        levels = self._somelevels
        if levels is None:
            if self.version < 6:
                levels = ()
            else:
                dbytes = self.dbytes
                dbytes.seek(self._somelevels_start_pos())
                dbytes.require_equal_uint4(MAGIC_1)
                num = dbytes.read_uint4()
                levels = StringEntry.lazy_n_maybe(dbytes, num)
            self._somelevels = levels
        return levels


@ForwardFragmentAttrs(ProfileProgressFragment, **ProfileProgressFragment.value_attrs)
@require_type(FTYPE_PROFILEPROGRESS)
class ProfileProgress(BaseObject):

    fragment_prober = FRAG_PROBER

    @property
    def stats(self):
        return self.fragment_by_type(ProfileStatsFragment)

    def _print_data(self, p):
        progress = self.fragment_by_type(ProfileProgressFragment)
        if progress:
            p(f"Level progress version: {progress.version}")
            levels = self.levels
            p(f"Level count: {len(levels)}")
            with p.tree_children():
                for level in levels:
                    p.tree_next_child()
                    p.print_data_of(level)
            officials = self.officials
            if officials:
                p(f"Unlocked levels: {len(officials)}")
                with p.tree_children():
                    it = iter(officials)
                    for _ in range(0, len(officials), 5):
                        p.tree_next_child()
                        l_str = ', '.join(repr(n.value) for n in islice(it, 5))
                        p(f"Levels: {l_str}")
            tricks = self.tricks
            if tricks:
                p(f"Found tricks: {len(tricks)}")
                with p.tree_children():
                    it = iter(tricks)
                    for _ in range(0, len(tricks), 5):
                        p.tree_next_child()
                        t_str = ', '.join(repr(t.value) for t in islice(it, 5))
                        p(f"Tricks: {t_str}")
            adventures = self.unlocked_adventures
            if adventures:
                p(f"Unlocked adventure stages: {len(adventures)}")
                with p.tree_children():
                    for advlevel in adventures:
                        p.tree_next_child()
                        p(f"Level: {advlevel.value!r}")
            somelevels = self.somelevels
            if somelevels:
                p(f"Some levels: {len(somelevels)}")
                with p.tree_children():
                    for somelevel in somelevels:
                        p.tree_next_child()
                        p(f"Level: {somelevel.value!r}")
            if levels:
                comps = [0] * 4
                total = 0
                for level in levels:
                    for score, comp in zip(level.scores, level.completion):
                        comp -= Completion.BRONZE
                        if comp >= 0:
                            total += comp + 1
                            comps[comp] += 1
                p(f"Medal points: {total}")
                with p.tree_children():
                    for comp, num in enumerate(comps, Completion.BRONZE):
                        p.tree_next_child()
                        p(f"{Completion.to_name(comp)} medals: {num}")
        else:
            p("No level progress")
        if self.stats:
            p.print_data_of(self.stats)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
