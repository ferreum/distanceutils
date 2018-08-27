

from .base import BaseObject, require_type
from .classes import CollectorGroup, DefaultClasses


Classes = CollectorGroup()


@Classes.non_level_objects.object
@DefaultClasses.fragments.fragment_attrs('Leaderboard')
@require_type
class Leaderboard(BaseObject):

    type = 'LocalLeaderboard'


@Classes.non_level_objects.object
@DefaultClasses.fragments.fragment_attrs('LevelInfos')
@require_type
class LevelInfos(BaseObject):

    type = 'LevelInfos'


@Classes.non_level_objects.object
@DefaultClasses.fragments.fragment_attrs('ProfileProgress')
@require_type
class ProfileProgress(BaseObject):

    type = 'ProfileProgress'

    @property
    def stats(self):
        try:
            return self['ProfileStats']
        except KeyError:
            raise AttributeError("ProfileStats fragment is not present.")


# Registered in distance._core via prober function because of
# dynamic object name.
@Classes.common.add_info(tag='Replay')
@DefaultClasses.fragments.fragment_attrs('Replay')
@require_type(func=lambda t: t.startswith('Replay: '))
class Replay(BaseObject):

    type_prefix = 'Replay: '


@Classes.non_level_objects.object
@require_type
@DefaultClasses.fragments.fragment_attrs('WorkshopLevelInfos')
class WorkshopLevelInfos(BaseObject):

    type = 'WorkshopLevelInfos'


# vim:set sw=4 et:
