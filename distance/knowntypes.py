# File:        knowntypes.py
# Description: knowntypes
# Created:     2017-07-01


from .bytes import SECTION_6, SECTION_9
from .detect import BytesProber
from .replay import Replay, FTYPE_REPLAY_PREFIX
from .leaderboard import Leaderboard, FTYPE_LEADERBOARD
from .workshoplevelinfos import WorkshopLevelInfos, FTYPE_WSLEVELINFOS
from .levelinfos import LevelInfos, FTYPE_LEVELINFOS
from .profileprogress import ProfileProgress, FTYPE_PROFILEPROGRESS
from .level import Level
from .level import PROBER as LEVEL_PROBER


PROBER = BytesProber({
    FTYPE_LEADERBOARD: Leaderboard,
    FTYPE_WSLEVELINFOS: WorkshopLevelInfos,
    FTYPE_LEVELINFOS: LevelInfos,
    FTYPE_PROFILEPROGRESS: ProfileProgress,
})


@PROBER.func
def _detect_other(section):
    if section.magic == SECTION_6:
        if section.type.startswith(FTYPE_REPLAY_PREFIX):
            return Replay
    if section.magic == SECTION_9:
        return Level
    return None


PROBER.extend(LEVEL_PROBER)


detect_class = PROBER.detect_class
read = PROBER.read
maybe = PROBER.maybe


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
