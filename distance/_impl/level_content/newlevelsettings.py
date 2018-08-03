

from distance.base import BaseObject
from distance.prober import ProberGroup
from distance._default_probers import DefaultProbers


Probers = ProberGroup()


@Probers.level_content.object
@DefaultProbers.fragments.fragment_attrs('LevelSettings')
class NewLevelSettings(BaseObject):

    type = 'LevelSettings'


# vim:set sw=4 et:
