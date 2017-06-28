#!/usr/bin/python
# File:        detect.py
# Description: detect
# Created:     2017-06-28


from .bytes import Section, SECTION_TYPE, SECTION_LEVEL
from .replay import Replay, FTYPE_REPLAY_PREFIX
from .leaderboard import Leaderboard, FTYPE_LEADERBOARD
from .levelinfos import LevelInfos, FTYPE_LEVELINFOS
from .level import Level


def detect(dbytes):
    sections = {}
    section = Section(dbytes).put_into(sections)
    if section.ident == SECTION_TYPE:
        filetype = section.filetype
        if filetype == FTYPE_LEADERBOARD:
            cls = Leaderboard
        elif filetype == FTYPE_LEVELINFOS:
            cls = LevelInfos
        elif filetype.startswith(FTYPE_REPLAY_PREFIX):
            cls = Replay
        else:
            raise IOError(f"Unknown filetype: {filetype!r}")
    elif section.ident == SECTION_LEVEL:
        cls = Level
    else:
        raise IOError(f"Unknown initial section: {section.ident}")
    return cls(dbytes, sections=sections)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
