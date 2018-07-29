

from distance.bytes import Magic
from distance.base import BaseObject, Fragment
from distance.levelobjects import LevelObject, SubObject
from distance._default_probers import DefaultProbers


DefaultProbers.create('common', baseclass=Fragment)
DefaultProbers.create('level_objects', baseclass=LevelObject)
DefaultProbers.create('level_subobjects', baseclass=SubObject)
DefaultProbers.create('level_fallback', baseclass=LevelObject)
DefaultProbers.create('fragments', baseclass=Fragment)
DefaultProbers.create('base_objects', baseclass=BaseObject)
DefaultProbers.create('base_fragments', baseclass=Fragment)
DefaultProbers.create('level', baseclass=Fragment)
DefaultProbers.create('level_content', baseclass=Fragment)
DefaultProbers.create('non_level_objects', baseclass=BaseObject)
DefaultProbers.create_mux(
    'level_like', baseclass=LevelObject,
    keys=['level', 'level_objects'])
DefaultProbers.create_mux(
    'file', baseclass=Fragment,
    keys=['level_objects', 'level', 'non_level_objects', 'level_fallback'])


def _impl_modules():
    return [
        'distance.base',
        'distance._impl.fragments.group',
        'distance._impl.fragments.levelfragments',
        'distance._impl.fragments.npfragments',
        'distance._impl.fragments.replay',
        'distance._impl.fragments.levelsettings',
        'distance._impl.fragments.leaderboard',
        'distance._impl.fragments.levelinfos',
        'distance._impl.fragments.profileprogress',
        'distance._impl.fragments.workshoplevelinfos',
        'distance._impl.level_objects.group',
        'distance._impl.level_objects.objects',
        'distance._impl.level_content.layer',
        'distance._impl.level_content.newlevelsettings',
        'distance._impl.level_content.oldlevelsettings',
        'distance.level',
        'distance.leaderboard',
        'distance.levelinfos',
        'distance.profileprogress',
        'distance.workshoplevelinfos',
        'distance.levelfragments',
    ]


_autoload_module = 'distance._autoload._probers'


DefaultProbers.autoload_modules(_autoload_module, _impl_modules)


@DefaultProbers.non_level_objects.func('dst._core.nonlevel_fallback')
def _detect_non_level_objects_other(section):
    if section.magic == Magic[6]:
        from distance.replay import Replay, FTYPE_REPLAY_PREFIX
        # Replay requires dynamic check.
        if section.type.startswith(FTYPE_REPLAY_PREFIX):
            return Replay
    return None


@DefaultProbers.level_fallback.func('dst._core.level_fallback')
def _level_fallback(section):
    if section.magic == Magic[6]:
        return LevelObject
    return None


def write_autoload_modules():
    DefaultProbers.write_autoload_module(_autoload_module)


# vim:set sw=4 ts=8 sts=4 et:
