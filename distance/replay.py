#!/usr/bin/python
# File:        replay.py
# Description: replay
# Created:     2017-06-28


from .section import Section, SECTION_TYPE, SECTION_UNK_2


class Replay(object):

    def __init__(self, dbytes):
        self.unknown = unknown = []
        self.sections = sections = Section.read_to_map(dbytes, SECTION_UNK_2)
        try:
            ts = sections[SECTION_TYPE]
        except KeyError:
            raise IOError("Missing type information")
        if not ts.filetype.startswith("Replay: "):
            raise IOError(f"Invalid bytes filetype: {ts.filetype}")
        self.version = sections[SECTION_UNK_2].version
        unknown.append(dbytes.read_n(4))
        self.player_name = dbytes.read_string()
        self.player_id = dbytes.read_fixed_number(8)
        self.player_name_2 = dbytes.read_string()
        self.finish_time = dbytes.read_fixed_number(4)
        self.replay_duration = dbytes.read_fixed_number(4)
        unknown.append(dbytes.read_n(4))
        self.car_name = dbytes.read_string()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
