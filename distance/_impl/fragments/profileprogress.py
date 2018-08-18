

from itertools import islice

from construct import (
    Struct, Default, Computed, PrefixedArray, StopIf, If, Rebuild,
    Bytes,
    this, len_,
)

from distance.bytes import Magic, Section
from distance.construct import (
    BaseConstructFragment,
    UInt, Int, Double, Long, DstString, Remainder, MagicConst,
)
from distance.printing import format_duration, format_duration_dhms, format_distance
from distance.constants import Completion, Mode, TIMED_MODES
from distance.classes import CollectorGroup


Classes = CollectorGroup()


def _print_stringentries(p, title, prefix, entries, num_per_row=1):
    if entries:
        p(f"{title}: {len(entries)}")
        rangeobj = range(0, len(entries), num_per_row)
        it = iter(entries)
        with p.tree_children(len(rangeobj)):
            for _ in rangeobj:
                p.tree_next_child()
                t_str = ', '.join(map(repr, islice(it, num_per_row)))
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


@Classes.fragments.fragment(any_version=True)
class ProfileProgressFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x6a)

    is_interesting = True

    _construct_ = Struct(
        'version' / Computed(this._params.sec.version),
        'num_levels' / Rebuild(UInt, len_(this.levels)),
        'unk_0' / UInt,
        'levels' / Default(Struct(
            'level_path' / DstString,
            'unk_0' / DstString,
            'unk_1' / Bytes(1),
            MagicConst(1),
            'completion' / Default(PrefixedArray(UInt, UInt), ()),
            MagicConst(1),
            'scores' / Default(PrefixedArray(UInt, Int), ()),
            'unk_2' / If(this._.version > 2, Bytes(8)),
        )[this.num_levels], ()),
        MagicConst(1),
        'officials' / Default(PrefixedArray(UInt, DstString), ()),
        'unk_1' / If(this.version < 6, Remainder),
        StopIf(this.version < 6),
        'unk_2' / Bytes(36),
        MagicConst(1),
        'tricks' / Default(PrefixedArray(UInt, DstString), ()),
        MagicConst(1),
        'unlocked_adventures' / Default(PrefixedArray(UInt, DstString), ()),
        'unk_3' / Bytes(10),
        MagicConst(1),
        'somelevels' / Default(PrefixedArray(UInt, DstString), ()),
        'unk_4' / Remainder,
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        levels = self.levels
        p(f"Level count: {len(levels)}")
        with p.tree_children(len(levels)):
            for level in levels:
                p.tree_next_child()
                p(f"Level path: {level.level_path!r}")
                for mode, (score, comp) in enumerate(zip(level.scores, level.completion)):
                    if comp != Completion.UNPLAYED:
                        p(format_score(mode, score, comp))
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
            with p.tree_children(len(comps)):
                for comp, num in enumerate(comps, Completion.BRONZE):
                    p.tree_next_child()
                    p(f"{Completion.to_name(comp)} medals: {num}")



@Classes.fragments.fragment(any_version=True)
class ProfileStatsFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x8e)

    is_interesting = True

    _construct_ = Struct(
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
        MagicConst(1),
        'offline_times' / Default(PrefixedArray(UInt, Double), ()),
        MagicConst(1),
        'modes_unknown' / Default(PrefixedArray(UInt, Long), ()),
        MagicConst(1),
        'online_times' / Default(PrefixedArray(UInt, Double), ()),
        StopIf(this.version < 1),
        'unk_6' / Bytes(8),
        MagicConst(1),
        'trackmogrify_mods' / Default(PrefixedArray(UInt, DstString), ()),
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)

        def ps(stat, name):
            value = getattr(self, stat)
            if value is None:
                val_str = "None"
            elif stat.endswith('_seconds'):
                val_str = format_duration_dhms(value * 1000)
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
            rangeobj = range(0, len(mods), 5)
            with p.tree_children(len(rangeobj)):
                for i in rangeobj:
                    mods_str = ', '.join(repr(m) for m in islice(mods, i, i + 5))
                    p.tree_next_child()
                    p(f"Found: {mods_str}")


# vim:set sw=4 et:
