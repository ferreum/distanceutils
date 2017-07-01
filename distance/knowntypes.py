#!/usr/bin/python
# File:        knowntypes.py
# Description: knowntypes
# Created:     2017-07-01


from .bytes import SECTION_TYPE, SECTION_LEVEL
from .detect import BytesProber
from .replay import Replay, FTYPE_REPLAY_PREFIX
from .leaderboard import Leaderboard, FTYPE_LEADERBOARD
from .levelinfos import LevelInfos, FTYPE_LEVELINFOS
from .level import Level


PROBER = BytesProber({
    FTYPE_LEADERBOARD: Leaderboard,
    FTYPE_LEVELINFOS: LevelInfos,
})


@PROBER.func
def _detect_other(section):
    if section.ident == SECTION_TYPE:
        if section.filetype.startswith(FTYPE_REPLAY_PREFIX):
            return Replay
    if section.ident == SECTION_LEVEL:
        return Level
    return None


detect_class = PROBER.detect_class
parse = PROBER.parse
parse_maybe_partial = PROBER.parse_maybe_partial


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
