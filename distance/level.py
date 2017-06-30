#!/usr/bin/python
# File:        level.py
# Description: level
# Created:     2017-06-28


from struct import Struct
import sys

from .bytes import (BytesModel, Section, S_FLOAT,
                    SECTION_LEVEL, SECTION_LAYER, SECTION_TYPE,
                    SECTION_UNK_2, SECTION_UNK_3, SECTION_LEVEL_INFO,
                    print_exception)
from .common import format_duration


MODE_SPRINT = 1
MODE_STUNT = 2
MODE_FREE_ROAM = 4
MODE_TAG = 5
MODE_CHALLENGE = 8
MODE_SPEED_AND_STYLE = 10
MODE_MAIN_MENU = 13

MODE_NAMES = {
    MODE_SPRINT: "Sprint",
    MODE_STUNT: "Stunt",
    MODE_FREE_ROAM: "Free Roam",
    MODE_TAG: "Reverse Tag",
    MODE_CHALLENGE: "Challenge",
    MODE_SPEED_AND_STYLE: "Speed and Style",
    MODE_MAIN_MENU: "Main Menu",
}

ABILITY_NAMES = (
    {0: "", 1: "Infinite Cooldown"},
    {0: "", 1: "Disable Flying"},
    {0: "", 1: "Disable Jumping"},
    {0: "", 1: "Disable Boosting"},
    {0: "", 1: "Disable Jet Rotation"},
)

DIFFICULTY_NAMES = {
    0: "Casual",
    1: "Normal",
    2: "Advanced",
    3: "Expert",
    4: "Nightmare",
    5: "None",
}

S_ABILITIES = Struct("5b")


class LevelObject(BytesModel):

    type = None
    version = None
    name = None
    skybox_name = None
    modes = ()
    medal_times = ()
    medal_scores = ()
    abilities = ()
    difficulty = None

    def parse(self, dbytes, shared_info=None):
        next_section = dbytes.read_fixed_number(4)
        dbytes.pos -= 4
        if next_section == SECTION_LEVEL_INFO:
            # Levelinfo section only found in old (v1) maps
            isec = self.require_section(SECTION_LEVEL_INFO)
            self.type = 'Section 88888888'
            self.report_end_pos(isec.data_start + isec.size)
            self.add_unknown(4)
            self.skybox_name = dbytes.read_string()
            self.add_unknown(143)
            self.name = dbytes.read_string()
            return
        ts = self.require_section(SECTION_TYPE, shared_info=shared_info)
        self.report_end_pos(ts.data_start + ts.size)
        self.type = type = ts.filetype
        self.require_section(SECTION_UNK_3)
        if type == 'LevelSettings':
            self.version = version = self.require_section(SECTION_UNK_2).version
            shared_info['version'] = version
            self.add_unknown(12)
            self.name = dbytes.read_string()
            self.add_unknown(4)
            self.modes = modes = {}
            num_modes = dbytes.read_fixed_number(4)
            for i in range(num_modes):
                mode = dbytes.read_fixed_number(4)
                modes[mode] = dbytes.read_byte()
            self.music_id = dbytes.read_fixed_number(4)
            if version <= 3:
                self.skybox_name = dbytes.read_string()
                self.add_unknown(57)
            elif version == 4:
                self.add_unknown(141)
            elif version == 5:
                self.add_unknown(172) # confirmed only for v5
            elif 6 <= version:
                # confirmed only for v6..v9
                self.add_unknown(176)
            self.medal_times = times = []
            self.medal_scores = scores = []
            for i in range(4):
                times.append(dbytes.read_struct(S_FLOAT)[0])
                scores.append(dbytes.read_fixed_number(4, signed=True))
            if version >= 1:
                self.abilities = dbytes.read_struct(S_ABILITIES)
            if version >= 2:
                self.difficulty = dbytes.read_fixed_number(4)

    def _print_data(self, file, p):
        if 'noobjlist' not in p.flags:
            p(f"Object type: {self.type!r}")
        if self.version is not None:
            p(f"Object version: {self.version!r}")
        if self.name is not None:
            p(f"Level name: {self.name!r}")
        if self.skybox_name is not None:
            p(f"Skybox name: {self.skybox_name!r}")
        if self.medal_times:
            medal_str = ', '.join(format_duration(t) for t in self.medal_times)
            p(f"Medal times: {medal_str}")
        if self.medal_scores:
            medal_str = ', '.join(str(s) for s in self.medal_scores)
            p(f"Medal scores: {medal_str}")
        if self.modes:
            modes_str = ', '.join(MODE_NAMES.get(mode, f"Unknown({mode})")
                                  for mode, value in sorted(self.modes.items())
                                  if value)
            p(f"Level modes: {modes_str}")
        if self.abilities:
            ab_str = ', '.join(names.get(value, f"Unknown({value})")
                               for value, names in zip(self.abilities, ABILITY_NAMES)
                               if names.get(value, True))
            if not ab_str:
                ab_str = "All"
            p(f"Abilities: {ab_str}")
        if self.difficulty is not None:
            diff_str = (DIFFICULTY_NAMES.get(self.difficulty, None)
                        or f"Unknown({self.difficulty})")
            p(f"Difficulty: {diff_str}")


class Level(BytesModel):

    def parse(self, dbytes):
        ls = self.require_section(SECTION_LEVEL, 0)
        if not ls:
            raise IOError("No level section")
        self.level_name = ls.level_name

    def iter_objects(self, with_layers=False, with_objects=True):
        dbytes = self.dbytes
        info = {}
        settings, sane, exc = LevelObject.maybe_partial(dbytes, shared_info=info)
        yield settings, sane, exc
        if not sane:
            return
        for layer, sane, exc in Section.iter_maybe_partial(dbytes, shared_info=info):
            layer_end = layer.size + layer.data_start
            if with_layers:
                yield layer, sane, exc
            if not sane:
                return
            if with_objects:
                for obj, sane, exc in LevelObject.iter_maybe_partial(dbytes, max_pos=layer_end, shared_info=info):
                    yield obj, sane, exc
                    if not sane:
                        return
            dbytes.pos = layer_end

    def _print_data(self, file, p):
        p(f"Level name: {self.level_name!r}")
        try:
            num_objects = 0
            layer_objects = 0
            num_layers = 0
            gen = self.iter_objects(with_layers='nolayers' not in p.flags,
                                    with_objects='noobjlist' not in p.flags)
            for obj, sane, exc in gen:
                if isinstance(obj, Section) and obj.ident == SECTION_LAYER:
                    p(f"Layer: {num_layers}")
                    num_layers += 1
                    layer_objects += obj.num_objects
                else:
                    num_objects += 1
                    if 'noobjlist' not in p.flags:
                        p(f"Level object: {num_objects}")
                obj.print_data(file, flags=p.flags)
            if 'nolayers' not in p.flags:
                p(f"Total layers: {num_layers}")
                p(f"Total objects in layers: {layer_objects}")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print_exception(sys.exc_info(), file, p)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
