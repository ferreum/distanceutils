#!/usr/bin/python
# File:        detect.py
# Description: detect
# Created:     2017-06-28


from .bytes import Section, SECTION_TYPE
from .replay import Replay, FTYPE_REPLAY_PREFIX
from .leaderboard import Leaderboard, FTYPE_LEADERBOARD
from .levelinfos import LevelInfos, FTYPE_LEVELINFOS


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
            raise IOError("Unknown filetype: {filetype!r}")
        return cls(dbytes, sections=sections)
    else:
        raise IOError("Unknown initial section: {section.ident}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
