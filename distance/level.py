#!/usr/bin/python
# File:        level.py
# Description: level
# Created:     2017-06-28


from .bytes import (BytesModel, S_COLOR_RGBA, SECTION_LEVEL)
from .common import format_bytes


class Level(BytesModel):

    def parse(self, dbytes):
        ls = self.require_section(SECTION_LEVEL, 0)
        if not ls:
            raise IOError("No level section")
        self.level_name = ls.level_name

    def print_data(self, file, unknown=False):
        BytesModel.print_data(self, file, unknown=unknown)
        def p(*args):
            print(*args, file=file)
        p(f"Level name: {self.level_name!r}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
