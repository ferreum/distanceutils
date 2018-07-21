"""ProfilePrgress .bytes support."""


from .base import BaseObject, require_type
from .prober import ProberGroup
from ._default_probers import DefaultProbers


Probers = ProberGroup()


FTYPE_PROFILEPROGRESS = 'ProfileProgress'


@Probers.file.for_type
@DefaultProbers.fragments.fragment_attrs('ProfileProgress')
@require_type
class ProfileProgress(BaseObject):

    type = FTYPE_PROFILEPROGRESS

    @property
    def stats(self):
        return self.fragment_by_tag('ProfileStats')


# vim:set sw=4 ts=8 sts=4 et:
