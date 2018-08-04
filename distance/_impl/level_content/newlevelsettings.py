

from distance.base import BaseObject
from distance.classes import CollectorGroup
from distance._default_classes import DefaultClasses


Classes = CollectorGroup()


@Classes.level_content.object
@DefaultClasses.fragments.fragment_attrs('LevelSettings')
class NewLevelSettings(BaseObject):

    type = 'LevelSettings'


# vim:set sw=4 et:
