#!/usr/bin/python
# File:        level.py
# Description: level
# Created:     2017-06-28


from struct import Struct
import sys

from .bytes import (BytesModel, S_COLOR_RGBA, SECTION_LEVEL,
                    SECTION_TYPE, SECTION_UNK_2, SECTION_UNK_3,
                    print_exception)
from .common import format_bytes, format_duration


class LevelObject(BytesModel):

    type = None
    version = None
    name = None
    skybox_name = None
    medal_times = ()

    def parse(self, dbytes, shared_info=None):
        ts = self.require_section(SECTION_TYPE, shared_info=shared_info)
        self.report_end_pos(ts.data_start + ts.size)
        self.type = type = ts.filetype
        self.require_section(SECTION_UNK_3)
        if type == 'LevelSettings':
            self.version = version = self.require_section(SECTION_UNK_2).version
            shared_info['version'] = version
            self.add_unknown(12)
            self.name = dbytes.read_string()
            if version <= 3:
                if 0 <= version <= 2:
                    self.add_unknown(47) # confirmed only for v0 & v1
                elif version == 3:
                    self.add_unknown(42)
                self.skybox_name = dbytes.read_string()
                self.add_unknown(57)
            elif version == 4:
                self.add_unknown(183)
            elif version == 5 or version == 6:
                self.add_unknown(214) # confirmed only for v5
            elif version == 7:
                self.add_unknown(218)
            elif version == 8:
                self.add_unknown(223)
            elif version >= 9:
                self.add_unknown(213) # confirmed only for v9
            self.medal_times = times = []
            for i in range(4):
                times.append(dbytes.read_struct("f")[0])
                self.add_unknown(4)

    def _print_data(self, file, unknown, p):
        p(f"Object type: {self.type!r}")
        if self.version is not None:
            p(f"Object version: {self.version!r}")
        if self.skybox_name is not None:
            p(f"Skybox name: {self.skybox_name!r}")
        if self.medal_times:
            medal_str = ', '.join(format_duration(t) for t in self.medal_times)
            p(f"Medal times: {medal_str}")


class Level(BytesModel):

    def parse(self, dbytes):
        ls = self.require_section(SECTION_LEVEL, 0)
        if not ls:
            raise IOError("No level section")
        self.level_name = ls.level_name

    def iter_objects(self):
        return LevelObject.iter_maybe_partial(
            self.dbytes, shared_info={})

    def _print_data(self, file, unknown, p):
        p(f"Level name: {self.level_name!r}")
        try:
            for i, (obj, sane, exc) in enumerate(self.iter_objects()):
                p(f"Level object: {i}")
                obj.print_data(file, unknown=unknown)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print_exception(sys.exc_info(), file, p)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
