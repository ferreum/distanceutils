#!/usr/bin/python
# File:        knowntypes.py
# Description: knowntypes
# Created:     2017-07-01


from .bytes import SECTION_TYPE, SECTION_LEVEL
from .detect import BytesProber
from .replay import Replay, FTYPE_REPLAY_PREFIX
from .leaderboard import Leaderboard, FTYPE_LEADERBOARD
from .workshoplevelinfos import WorkshopLevelInfos, FTYPE_WSLEVELINFOS
from .profileprogress import ProfileProgress, FTYPE_PROFILEPROGRESS
from .level import Level
from .level import PROBER as LEVEL_PROBER


PROBER = BytesProber({
    FTYPE_LEADERBOARD: Leaderboard,
    FTYPE_WSLEVELINFOS: WorkshopLevelInfos,
    FTYPE_PROFILEPROGRESS: ProfileProgress,
})


@PROBER.func
def _detect_other(section):
    if section.ident == SECTION_TYPE:
        if section.type.startswith(FTYPE_REPLAY_PREFIX):
            return Replay
    if section.ident == SECTION_LEVEL:
        return Level
    return None


PROBER.extend(LEVEL_PROBER)


detect_class = PROBER.detect_class
parse = PROBER.parse
maybe_partial = PROBER.maybe_partial


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
