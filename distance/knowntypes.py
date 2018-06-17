"""Probe top-level objects in .bytes files"""


from .bytes import Magic
from .base import Fragment, BaseObject
from .replay import Replay, FTYPE_REPLAY_PREFIX
from .leaderboard import Leaderboard, FTYPE_LEADERBOARD
from .workshoplevelinfos import WorkshopLevelInfos, FTYPE_WSLEVELINFOS
from .levelinfos import LevelInfos, FTYPE_LEVELINFOS
from .profileprogress import ProfileProgress, FTYPE_PROFILEPROGRESS
from .level import Level
from .levelobjects import PROBER as LEVELOBJ_PROBER
from ._default_probers import DefaultProbers


PROBER = DefaultProbers.get_or_create('file').transaction()

PROBER.add_fragment(Leaderboard, Magic[6], FTYPE_LEADERBOARD)
PROBER.add_fragment(WorkshopLevelInfos, Magic[6], FTYPE_WSLEVELINFOS)
PROBER.add_fragment(LevelInfos, Magic[6], FTYPE_LEVELINFOS)
PROBER.add_fragment(ProfileProgress, Magic[6], FTYPE_PROFILEPROGRESS)
PROBER.add_fragment(Level, Magic[9])


@PROBER.func('Replay,BaseObject')
def _detect_other(section):
    if section.magic == Magic[6]:
        if section.type.startswith(FTYPE_REPLAY_PREFIX):
            return Replay
        return BaseObject
    return None


PROBER.extend_from(LEVELOBJ_PROBER)
PROBER.commit()

DefaultProbers.file.baseclass = Fragment

probe = DefaultProbers.file.probe
read = DefaultProbers.file.read
maybe = DefaultProbers.file.maybe


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
