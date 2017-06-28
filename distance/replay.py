#!/usr/bin/python
# File:        replay.py
# Description: replay
# Created:     2017-06-28


from .bytes import S_COLOR_RGBA
from .section import Section, SECTION_TYPE, SECTION_UNK_2, SECTION_UNK_1


class Replay(object):

    player_name_2 = None
    player_id = None
    replay_duration = None
    finish_time = None

    def __init__(self, dbytes):
        self.unknown = unknown = []
        self.sections = sections = Section.read_to_map(dbytes, SECTION_UNK_2)
        try:
            ts = sections[SECTION_TYPE]
        except KeyError:
            raise IOError("Missing type information")
        if not ts.filetype.startswith("Replay: "):
            raise IOError(f"Invalid bytes filetype: {ts.filetype}")
        self.version = version = sections[SECTION_UNK_2].version
        unknown.append(dbytes.read_n(4))
        self.player_name = dbytes.read_string()
        if version >= 2:
            self.player_id = dbytes.read_fixed_number(8)
            self.player_name_2 = dbytes.read_string()
            if version >= 3:
                self.finish_time = dbytes.read_fixed_number(4)
                self.replay_duration = dbytes.read_fixed_number(4)
        unknown.append(dbytes.read_n(4))
        self.car_name = dbytes.read_string()
        self.car_color_primary = dbytes.read_struct(S_COLOR_RGBA)
        self.car_color_secondary = dbytes.read_struct(S_COLOR_RGBA)
        self.car_color_glow = dbytes.read_struct(S_COLOR_RGBA)
        self.car_color_sparkle = dbytes.read_struct(S_COLOR_RGBA)

        if version <= 1:
            ident = dbytes.read_fixed_number(4)
            if ident != SECTION_UNK_1:
                raise IOError(f"unexpected section: {ident}")
            section_size = dbytes.read_fixed_number(4) * 4
            dbytes.pos += section_size
            ident = dbytes.read_fixed_number(4)
            if ident != SECTION_UNK_1:
                raise IOError(f"unexpected section: {ident}")
            section_size = dbytes.read_fixed_number(4)
            dbytes.pos += section_size - 8
            self.finish_time = dbytes.read_fixed_number(4)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
