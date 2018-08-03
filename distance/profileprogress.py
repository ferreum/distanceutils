"""ProfilePrgress .bytes support."""


from .base import BaseObject, require_type
from .prober import ProberGroup
from ._default_probers import DefaultProbers


Probers = ProberGroup()


FTYPE_PROFILEPROGRESS = 'ProfileProgress'


@Probers.non_level_objects.object
@DefaultProbers.fragments.fragment_attrs('ProfileProgress')
@require_type
class ProfileProgress(BaseObject):

    type = FTYPE_PROFILEPROGRESS

    @property
    def stats(self):
        try:
            return self['ProfileStats']
        except KeyError:
            raise AttributeError("ProfileStats fragment is not present.")


# vim:set sw=4 ts=8 sts=4 et:
