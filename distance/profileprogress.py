"""ProfilePrgress .bytes support."""


from itertools import islice

from construct import (
    Struct, Default, Computed, PrefixedArray, Const, StopIf,
    Bytes,
    this,
)

from .bytes import BytesModel, Magic, Section
from .base import (
    BaseObject, Fragment,
    ForwardFragmentAttrs,
    require_type
)
from .construct import (
    BaseConstructFragment,
    UInt, Double, Long, DstString,
)
from .printing import format_duration, format_duration_dhms, format_distance
from .constants import Completion, Mode, TIMED_MODES
from ._default_probers import DefaultProbers


FTYPE_PROFILEPROGRESS = 'ProfileProgress'

FILE_PROBER = DefaultProbers.file.transaction()
FRAG_PROBER = DefaultProbers.fragments.transaction()


def _print_stringentries(p, title, prefix, entries, num_per_row=1):
    if entries:
        p(f"{title}: {len(entries)}")
        with p.tree_children():
            if 'offset' in p.flags or 'size' in p.flags:
                for entry in entries:
                    p.tree_next_child()
                    p.print_data_of(entry)
            else:
                it = iter(entries)
                for _ in range(0, len(entries), num_per_row):
                    p.tree_next_child()
                    t_str = ', '.join(repr(t.value) for t in islice(it, num_per_row))
                    p(f"{prefix}: {t_str}")


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

        dbytes.require_equal_uint4(Magic[1])
        num_levels = dbytes.read_uint4()
        self.completion = completion = []
        for i in range(num_levels):
            completion.append(dbytes.read_uint4())

        dbytes.require_equal_uint4(Magic[1])
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

    def _print_data(self, p):
        p(f"Value: {self.value!r}")


@FRAG_PROBER.fragment(any_version=True)
class ProfileStatsFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x8e)

    is_interesting = True

    _construct = Struct(
        'version' / Computed(this._params.sec.version),
        'unk_0' / Bytes(4),
        'deaths' / Long,
        'laser_deaths' / Long,
        'reset_deaths' / Long,
        'impact_deaths' / Long,
        'overheat_deaths' / Long,
        'killgrid_deaths' / Long,
        'gibs_seconds' / Double,
        'unk_1' / Double,
        'forward_meters' / Double,
        'reverse_meters' / Double,
        'air_fly_meters' / Double,
        'air_nofly_meters' / Double,
        'wallride_meters' / Double,
        'ceilingride_meters' / Double,
        'grinding_meters' / Double,
        'boost_seconds' / Double,
        'grip_seconds' / Double,
        'splits' / Long,
        'impacts' / Long,
        'checkpoints' / Long,
        'jumps' / Long,
        'wings' / Long,
        'unk_2' / Long,
        'horns' / Long,
        'tricks' / Long,
        'ev' / Long,
        'lamps' / Long,
        'pumpkins' / Long,
        'eggs' / Long,
        'unk_3' / Long,
        'unk_4' / Long,
        'unk_5' / Long,
        'cooldowns' / Long,
        'total_seconds' / Double,
        'editor_working_seconds' / Double,
        'editor_playing_seconds' / Double,
        Const(Magic[1], UInt),
        'offline_times' / Default(PrefixedArray(UInt, Double), ()),
        Const(Magic[1], UInt),
        'modes_unknown' / Default(PrefixedArray(UInt, Long), ()),
        Const(Magic[1], UInt),
        'online_times' / Default(PrefixedArray(UInt, Double), ()),
        StopIf(this.version < 1),
        'unk_6' / Bytes(8),
        Const(Magic[1], UInt),
        'trackmogrify_mods' / Default(PrefixedArray(UInt, DstString), ()),
    )

    def _print_data(self, p):
        super()._print_data(p)
        p(f"Player stats version: {self.version}")

        def ps(stat, name):
            value = getattr(self, stat)
            if value is None:
                val_str = "None"
            elif stat.endswith('_seconds'):
                val_str = format_duration_dhms(value)
            elif stat.endswith('_meters'):
                val_str = format_distance(value)
            elif stat == 'ev':
                val_str = f"{value:,d} eV"
            else:
                val_str = repr(value)
            p(f"{name}: {val_str}")

        ps('total_seconds', "All play time")
        with p.tree_children():
            total_in_modes = sum(self.offline_times) + sum(self.online_times)
            p.tree_next_child()
            p(f"Total time in modes: {format_duration_dhms(total_in_modes * 1000)}")
            total_offline = sum(self.offline_times)
            total_online = sum(self.online_times)
            p.tree_next_child()
            p(f"Total time in offline modes: {format_duration_dhms(total_offline * 1000)}")
            with p.tree_children():
                for mode, time in enumerate(self.offline_times):
                    if time >= 0.001:
                        p.tree_next_child()
                        p(f"Time playing {Mode.to_name(mode)} offline: {format_duration_dhms(time * 1000)}")
            p.tree_next_child()
            p(f"Total time in online modes: {format_duration_dhms(total_online * 1000)}")
            with p.tree_children():
                for mode, time in enumerate(self.online_times):
                    if time >= 0.001:
                        p.tree_next_child()
                        p(f"Time playing {Mode.to_name(mode)} online: {format_duration_dhms(time * 1000)}")
            p.tree_next_child()
            ps('editor_working_seconds', "Time working in editor")
            p.tree_next_child()
            ps('editor_playing_seconds', "Time playing in editor")

        total_distance = sum([self.forward_meters or 0, self.reverse_meters or 0,
                              self.air_fly_meters or 0, self.air_nofly_meters or 0])
        ps('deaths', "Total deaths")
        with p.tree_children():
            ps('impact_deaths', "Impact deaths")
            p.tree_next_child()
            ps('killgrid_deaths', "Killgrid deaths")
            p.tree_next_child()
            ps('laser_deaths', "Laser deaths")
            p.tree_next_child()
            ps('overheat_deaths', "Overheat deaths")
            p.tree_next_child()
            ps('reset_deaths', "Reset deaths")
            p.tree_next_child()
            ps('gibs_seconds', "Gibs time")
        ps('impacts', "Impact count")
        ps('splits', "Split count")
        ps('checkpoints', "Checkpoints hit")
        ps('cooldowns', "Cooldowns hit")
        p(f"Distance traveled: {format_distance(total_distance)}")
        with p.tree_children():
            ps('forward_meters', "Distance driven forward")
            p.tree_next_child()
            ps('reverse_meters', "Distance driven reverse")
            p.tree_next_child()
            ps('air_fly_meters', "Distance airborn flying")
            p.tree_next_child()
            ps('air_nofly_meters', "Distance airborn not flying")
            p.tree_next_child()
            ps('wallride_meters', "Distance wall riding")
            p.tree_next_child()
            ps('ceilingride_meters', "Distance ceiling riding")
            p.tree_next_child()
            ps('grinding_meters', "Distance grinding")
        ps('lamps', "Lamps broken")
        ps('pumpkins', "Pumpkins smashed")
        ps('eggs', "Eggs cracked")
        ps('boost_seconds', "Boost held down time")
        ps('grip_seconds', "Grip held down time")
        ps('jumps', "Jump count")
        ps('wings', "Wings count")
        ps('horns', "Horn count")
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


@FRAG_PROBER.fragment(any_version=True)
class ProfileProgressFragment(Fragment):

    base_container = Section.base(Magic[2], 0x6a)

    is_interesting = True

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
            dbytes.require_equal_uint4(Magic[1])
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
                dbytes.require_equal_uint4(Magic[1])
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
                dbytes.require_equal_uint4(Magic[1])
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
                dbytes.require_equal_uint4(Magic[1])
                num = dbytes.read_uint4()
                levels = StringEntry.lazy_n_maybe(dbytes, num)
            self._somelevels = levels
        return levels

    def _print_data(self, p):
        super()._print_data(p)
        p(f"Level progress version: {self.version}")
        levels = self.levels
        p(f"Level count: {len(levels)}")
        with p.tree_children():
            for level in levels:
                p.tree_next_child()
                p.print_data_of(level)
        _print_stringentries(p, "Unlocked Levels", "Levels", self.officials, num_per_row=5)
        _print_stringentries(p, "Found tricks", "Tricks", self.tricks, num_per_row=5)
        _print_stringentries(p, "Unlocked adventure stages", "Level", self.unlocked_adventures)
        _print_stringentries(p, "Some levels", "Level", self.somelevels)
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


@FILE_PROBER.for_type
@ForwardFragmentAttrs(ProfileProgressFragment, **ProfileProgressFragment.value_attrs)
@require_type
class ProfileProgress(BaseObject):

    type = FTYPE_PROFILEPROGRESS

    @property
    def stats(self):
        return self.fragment_by_type(ProfileStatsFragment)


FRAG_PROBER.commit()
FILE_PROBER.commit()


# vim:set sw=4 ts=8 sts=4 et:
