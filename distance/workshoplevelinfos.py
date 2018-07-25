"""WorkshopLevelInfos .bytes support."""


from .base import BaseObject, require_type
from .prober import ProberGroup
from ._default_probers import DefaultProbers


Probers = ProberGroup()


FTYPE_WSLEVELINFOS = "WorkshopLevelInfos"


@Probers.file.object
@require_type
@DefaultProbers.fragments.fragment_attrs('WorkshopLevelInfos')
class WorkshopLevelInfos(BaseObject):

    type = FTYPE_WSLEVELINFOS


# vim:set sw=4 ts=8 sts=4 et:
