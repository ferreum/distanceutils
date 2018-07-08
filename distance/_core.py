

from distance.base import BaseObject, Fragment
from distance.levelobjects import LevelObject, SubObject
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
del _autoload_prober_keys
del _autoload_mods


DefaultProbers.file.baseclass = Fragment
DefaultProbers.level_like.baseclass = LevelObject
DefaultProbers.level_objects.baseclass = BaseObject
DefaultProbers.level_objects.baseclass = LevelObject
DefaultProbers.level_subobjects.baseclass = SubObject
DefaultProbers.fragments.baseclass = Fragment
DefaultProbers.get_or_create('base_objects').baseclass = BaseObject
DefaultProbers.get_or_create('base_fragments').baseclass = Fragment


# vim:set sw=4 ts=8 sts=4 et:
