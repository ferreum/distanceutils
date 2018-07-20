

from distance.bytes import Magic
from distance.base import BaseObject, Fragment
from distance.levelobjects import LevelObject, SubObject
from distance.replay import Replay, FTYPE_REPLAY_PREFIX
from distance._default_probers import DefaultProbers


DefaultProbers.get_or_create('file').baseclass = Fragment
DefaultProbers.get_or_create('level_like').baseclass = LevelObject
DefaultProbers.get_or_create('level_objects').baseclass = BaseObject
DefaultProbers.get_or_create('level_objects').baseclass = LevelObject
DefaultProbers.get_or_create('level_subobjects').baseclass = SubObject
DefaultProbers.get_or_create('level_content').baseclass = Fragment
DefaultProbers.get_or_create('fragments').baseclass = Fragment
DefaultProbers.get_or_create('base_objects').baseclass = BaseObject
DefaultProbers.get_or_create('base_fragments').baseclass = Fragment


def _impl_modules():
    return [
        'distance.base',
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


_autoload_module = 'distance._autoload._probers'


DefaultProbers.autoload_modules(_autoload_module, _impl_modules)


@DefaultProbers.file.func('Replay')
def _detect_other(section):
    if section.magic == Magic[6]:
        if section.type.startswith(FTYPE_REPLAY_PREFIX):
            return Replay
    return None


def write_autoload_modules():
    DefaultProbers.write_autoload_module(_autoload_module)


# vim:set sw=4 ts=8 sts=4 et:
