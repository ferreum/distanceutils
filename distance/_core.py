

from distance.bytes import Magic
from distance.base import BaseObject, Fragment
from distance.levelobjects import LevelObject, SubObject
from distance.replay import Replay, FTYPE_REPLAY_PREFIX
from distance._default_probers import DefaultProbers


_autoload_mods = [
    'distance.level',
    'distance.replay',
    'distance.leaderboard',
    'distance.levelinfos',
    'distance.profileprogress',
    'distance.workshoplevelinfos',
    'distance.levelfragments',
    'distance.levelobjects',
    'distance._impl.fragments.levelfragments',
    'distance._impl.fragments.npfragments',
    'distance._impl.level_objects.objects',
]
_autoload_prober_keys = [
    'file',
    'level_like',
    'level_objects',
    'level_subobjects',
    'level_content',
    'fragments',
]
for key in _autoload_prober_keys:
    p = DefaultProbers.get_or_create(key)
    p.key = key
    p.autoload_modules(f"distance._autoload._{key}", *_autoload_mods)
del key


DefaultProbers.file.baseclass = Fragment
DefaultProbers.level_like.baseclass = LevelObject
DefaultProbers.level_objects.baseclass = BaseObject
DefaultProbers.level_objects.baseclass = LevelObject
DefaultProbers.level_subobjects.baseclass = SubObject
DefaultProbers.fragments.baseclass = Fragment
DefaultProbers.get_or_create('base_objects').baseclass = BaseObject
DefaultProbers.get_or_create('base_fragments').baseclass = Fragment


@DefaultProbers.file.func('Replay')
def _detect_other(section):
    if section.magic == Magic[6]:
        if section.type.startswith(FTYPE_REPLAY_PREFIX):
            return Replay
    return None


def write_autoload_modules():
    for key in _autoload_prober_keys:
        p = getattr(DefaultProbers, key)
        p.write_autoload_module()


# vim:set sw=4 ts=8 sts=4 et:
