"""LocalLeaderboard .bytes support."""


from .base import BaseObject, require_type
from .prober import ProberGroup
from ._default_probers import DefaultProbers


NO_REPLAY = 0xffffffff_ffffffff

FTYPE_LEADERBOARD = "LocalLeaderboard"


Probers = ProberGroup()


@Probers.non_level_objects.object
@DefaultProbers.fragments.fragment_attrs('Leaderboard')
@require_type
class Leaderboard(BaseObject):

    type = FTYPE_LEADERBOARD


# vim:set sw=4 ts=8 sts=4 et:
