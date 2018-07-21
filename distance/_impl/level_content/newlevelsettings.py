

from distance.base import BaseObject
from distance.prober import ProberGroup
from distance._default_probers import DefaultProbers
from .levelsettings_base import BaseLevelSettings


Probers = ProberGroup()


@Probers.level_content.for_type
@DefaultProbers.fragments.fragment_attrs('LevelSettings')
class NewLevelSettings(BaseLevelSettings, BaseObject):

    type = 'LevelSettings'

    def _print_type(self, p):
        BaseObject._print_type(self, p)
        if self.version is not None:
            p(f"Object version: {self.version}")



# vim:set sw=4 et:
