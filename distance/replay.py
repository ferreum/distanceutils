#!/usr/bin/python
# File:        replay.py
# Description: replay
# Created:     2017-06-28


from .bytes import (BytesModel, S_COLOR_RGBA,
                    SECTION_2, SECTION_1)
from .common import format_duration, format_color


FTYPE_REPLAY_PREFIX = "Replay: "


class Replay(BytesModel):

    version = None
    player_name = None
    player_name_2 = None
    player_id = None
    finish_time = None
    replay_duration = None
    car_name = None
    car_color_primary = None
    car_color_secondary = None
    car_color_glow = None
    car_color_sparkle = None

    def _read(self, dbytes):
        ts = self.require_type(lambda t: t.startswith(FTYPE_REPLAY_PREFIX))
        self.report_end_pos(ts.data_end)
        self._read_sections(ts.data_end)

    def _read_section_data(self, dbytes, sec):
        if sec.ident == SECTION_2:
            if sec.value_id == 0x7f:
                # demo data
                self.version = version = sec.version
                self.player_name = dbytes.read_string()
                if version >= 2:
                    self.player_id = dbytes.read_num(8)
                    self.player_name_2 = dbytes.read_string()
                    if version >= 3:
                        self.finish_time = dbytes.read_num(4)
                        self.replay_duration = dbytes.read_num(4)
                self.add_unknown(4)
                self.car_name = dbytes.read_string()
                self.car_color_primary = dbytes.read_struct(S_COLOR_RGBA)
                self.car_color_secondary = dbytes.read_struct(S_COLOR_RGBA)
                self.car_color_glow = dbytes.read_struct(S_COLOR_RGBA)
                self.car_color_sparkle = dbytes.read_struct(S_COLOR_RGBA)

                if version <= 1:
                    self.require_equal(SECTION_1, 4)
                    section_size = dbytes.read_num(4) * 4
                    dbytes.pos += section_size
                    self.require_equal(SECTION_1, 4)
                    section_size = dbytes.read_num(4)
                    dbytes.pos += section_size - 8
                    self.finish_time = dbytes.read_num(4)
                return True
        return BytesModel._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        p(f"Version: {self.version}")
        p(f"Player name: {self.player_name!r}")
        p(f"Player name: {self.player_name_2!r}")
        p(f"Player ID: {self.player_id}")
        p(f"Finish time: {format_duration(self.finish_time)}")
        p(f"Replay duration: {format_duration(self.replay_duration)}")
        p(f"Car name: {self.car_name!r}")
        p(f"Car color primary: {format_color(self.car_color_primary)}")
        p(f"Car color secondary: {format_color(self.car_color_secondary)}")
        p(f"Car color glow: {format_color(self.car_color_glow)}")
        p(f"Car color sparkle: {format_color(self.car_color_sparkle)}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
