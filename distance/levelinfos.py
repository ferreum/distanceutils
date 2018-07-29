"""LevelInfos .bytes support."""


from .base import BaseObject, require_type
from .prober import ProberGroup
from ._default_probers import DefaultProbers


Probers = ProberGroup()


FTYPE_LEVELINFOS = 'LevelInfos'


@Probers.non_level_objects.object
@DefaultProbers.fragments.fragment_attrs('LevelInfos')
@require_type
class LevelInfos(BaseObject):

    type = FTYPE_LEVELINFOS


# vim:set sw=4 ts=8 sts=4 et:
