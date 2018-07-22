"""Replay files."""


from .base import BaseObject, require_type
from ._default_probers import DefaultProbers


FTYPE_REPLAY_PREFIX = "Replay: "


# Registered in distance._core via prober function because of
# dynamic object name.
@DefaultProbers.fragments.fragment_attrs('Replay')
@require_type(func=lambda t: t.startswith(FTYPE_REPLAY_PREFIX))
class Replay(BaseObject):
    pass


# vim:set sw=4 ts=8 sts=4 et:
