#!/usr/bin/python
# File:        profileprogress.py
# Description: profileprogress
# Created:     2017-07-05


from collections import OrderedDict
from itertools import islice

from .bytes import (BytesModel, Section, S_DOUBLE,
                    SECTION_UNK_1, SECTION_UNK_2, SECTION_UNK_3)
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

    def parse(self, dbytes):
        self.level_path = dbytes.read_string()
        self.recoverable = True
        self.add_unknown(value=dbytes.read_string())
        self.add_unknown(1)

        self.require_equal(SECTION_UNK_1, 4)
        num_levels = dbytes.read_fixed_number(4)
        self.completion = completion = []
        for i in range(num_levels):
            completion.append(dbytes.read_fixed_number(4))

        self.require_equal(SECTION_UNK_1, 4)
        num_levels = dbytes.read_fixed_number(4)
        self.scores = scores = []
        for i in range(num_levels):
            scores.append(dbytes.read_fixed_number(4, signed=True))
        self.add_unknown(8)

    def _print_data(self, p):
        p(f"Level path: {self.level_path!r}")
        for mode, (score, comp) in enumerate(zip(self.scores, self.completion)):
            if comp != Completion.UNPLAYED:
                p(format_score(mode, score, comp))


class Stat(object):

    def __init__(self, type, ident, unit='num', nbytes=None):
        if type == 'd':
            def parse(dbytes):
                return dbytes.read_struct(S_DOUBLE)[0]
        elif type == 'u8':
            def parse(dbytes):
                return dbytes.read_fixed_number(8)
        elif type == 'unk':
            def parse(dbytes):
                return dbytes.read_n(nbytes)
        else:
            raise ValueError(f"invalid type: {type!r}")
        self.parse_value = parse
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

    def parse_value(self, dbytes):
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

    def parse(self, dbytes, version=None):
        def read_double():
            return dbytes.read_struct(S_DOUBLE)[0]
        self.version = version
        self.recoverable = True

        self.stats = stats = {}
        for k, stat in STATS.items():
            stats[k] = stat.parse_value(dbytes)

        self.require_equal(SECTION_UNK_1, 4)
        num = dbytes.read_fixed_number(4)
        self.modes_offline = offline_times = []
        for i in range(num):
            offline_times.append(read_double())

        self.require_equal(SECTION_UNK_1, 4)
        num = dbytes.read_fixed_number(4)
        modes_unknown = self.add_unknown(value=[])
        for i in range(num):
            modes_unknown.append(dbytes.read_fixed_number(8))

        self.require_equal(SECTION_UNK_1, 4)
        num = dbytes.read_fixed_number(4)
        self.modes_online = online_times = []
        for i in range(num):
            online_times.append(read_double())

        self.add_unknown(8)
        self.require_equal(SECTION_UNK_1, 4)
        num = dbytes.read_fixed_number(4)
        self.trackmogrify_mods = mods = []
        for i in range(num):
            mods.append(dbytes.read_string())

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
        with p.tree_children(5):
            total_in_modes = sum(self.modes_offline) + sum(self.modes_online)
            p.tree_next_child()
            p(f"Total time in modes: {format_duration_dhms(total_in_modes * 1000)}")
            total_offline = sum(self.modes_offline)
            total_online = sum(self.modes_online)
            p.tree_next_child()
            p(f"Total time in offline modes: {format_duration_dhms(total_offline * 1000)}")
            with p.tree_children(sum(1 for t in self.modes_offline if t >= 0.001)):
                for mode, time in enumerate(self.modes_offline):
                    if time >= 0.001:
                        p.tree_next_child()
                        p(f"Time playing {Mode.to_name(mode)} offline: {format_duration_dhms(time * 1000)}")
            p.tree_next_child()
            p(f"Total time in online modes: {format_duration_dhms(total_online * 1000)}")
            with p.tree_children(sum(1 for t in self.modes_online if t >= 0.001)):
                for mode, time in enumerate(self.modes_online):
                    if time >= 0.001:
                        p.tree_next_child()
                        p(f"Time playing {Mode.to_name(mode)} online: {format_duration_dhms(time * 1000)}")
            ps(s.editor_working, "Time working in editor")
            ps(s.editor_playing, "Time playing in editor")

        total_distance = sum(values.get(stat.ident) for stat in
                             (s.forward, s.reverse, s.air_fly, s.air_nofly))
        ps(s.deaths, "Total deaths")
        with p.tree_children(6):
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
        with p.tree_children(7):
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
            with p.tree_children((len(mods) + 4) // 5):
                for i in range(0, len(mods), 5):
                    mods_str = ', '.join(repr(m) for m in mods[i:i+5])
                    p.tree_next_child()
                    p(f"Found: {mods_str}")


class ProfileProgress(BytesModel):

    level_s2 = None
    num_levels = None
    stats_s2 = None

    def parse(self, dbytes):
        ts = self.require_type(FTYPE_PROFILEPROGRESS)
        self.report_end_pos(ts.data_end)
        s3 = self.require_section(SECTION_UNK_3)
        dbytes.pos = s3.data_end
        while dbytes.pos < ts.data_end:
            section = Section(dbytes)
            if section.ident == SECTION_UNK_2:
                with dbytes.limit(section.data_end):
                    if section.value_id == 0x6A:
                        self.level_s2 = section
                        self.add_unknown(4)
                        self.num_levels = dbytes.read_fixed_number(4)
                        self.add_unknown(4)
                    elif section.value_id == 0x8E:
                        self.stats_s2 = section
            dbytes.pos = section.data_start + section.size

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
                for res in LevelProgress.iter_maybe_partial(dbytes, max_pos=data_end):
                    yield res
                    if not res[1]:
                        break
                    num -= 1
                    if num <= 0:
                        break
        self.off_mapname_start = dbytes.pos

    def iter_official_levels(self):
        dbytes = self.dbytes
        dbytes.pos = self.off_mapname_start
        self.require_equal(SECTION_UNK_1, 4)
        num_maps = dbytes.read_fixed_number(4)
        def gen():
            for i in range(num_maps):
                yield dbytes.read_string()
            self.found_tricks_start = dbytes.pos + 36
        return gen(), num_maps

    def iter_tricks(self):
        dbytes = self.dbytes
        dbytes.pos = self.found_tricks_start
        self.require_equal(SECTION_UNK_1, 4)
        num_tricks = dbytes.read_fixed_number(4)
        def gen():
            for i in range(num_tricks):
                yield dbytes.read_string()
            self.somelevel_list_start = dbytes.pos + 18
        return gen(), num_tricks

    def iter_somelevels(self):
        dbytes = self.dbytes
        dbytes.pos = self.somelevel_list_start
        self.require_equal(SECTION_UNK_1, 4)
        num_somelevels = dbytes.read_fixed_number(4)
        def gen():
            for i in range(num_somelevels):
                yield dbytes.read_string()
        return gen(), num_somelevels

    def read_stats(self):
        s2 = self.stats_s2
        if s2 is None:
            return None
        dbytes = self.dbytes
        dbytes.pos = s2.data_start + 16
        with dbytes.limit(s2.data_end):
            return PlayerStats.maybe_partial(dbytes, version=s2.version)

    def _print_data(self, p):
        if self.level_s2:
            p(f"Level progress version: {self.level_s2.version}")
            p(f"Level count: {self.num_levels}")
            with p.tree_children(self.num_levels):
                for level, sane, exc in self.iter_levels():
                    p.tree_next_child()
                    p.print_data_of(level)
            gen, length = self.iter_official_levels()
            if length:
                p(f"Unlocked levels: {length}")
            with p.tree_children((length + 4) // 5):
                # need to ensure that gen is exhausted
                gen = iter(list(gen))
                for _ in range(0, length, 5):
                    p.tree_next_child()
                    l_str = ', '.join(repr(n) for n in islice(gen, 5))
                    p(f"Levels: {l_str}")
            gen, length = self.iter_tricks()
            if length:
                p(f"Found tricks: {length}")
            with p.tree_children((length + 4) // 5):
                # need to ensure that gen is exhausted
                gen = iter(list(gen))
                for _ in range(0, length, 5):
                    p.tree_next_child()
                    t_str = ', '.join(repr(t) for t in islice(gen, 5))
                    p(f"Tricks: {t_str}")
            gen, length = self.iter_somelevels()
            if length:
                p(f"Some levels: {length}")
            with p.tree_children(length):
                for somelevel in gen:
                    p.tree_next_child()
                    p(f"Level: {somelevel!r}")
            stats, sane, exc = self.read_stats()
            if stats:
                p.print_data_of(stats)
        else:
            p("No level progress")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
