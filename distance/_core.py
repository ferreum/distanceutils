

from distance.bytes import Magic, Section
from distance.base import BaseObject, Fragment
from distance.levelobjects import LevelObject, SubObject
from distance.classes import ProbeError, DefaultClasses


def _fallback_obj_container(tag):
    return Section(Magic[6], tag)


DefaultClasses.init_category('common', baseclass=Fragment)
DefaultClasses.init_category('level_objects', baseclass=LevelObject,
                             get_fallback_container=_fallback_obj_container)
DefaultClasses.init_category('level_subobjects', baseclass=SubObject,
                             get_fallback_container=_fallback_obj_container)
DefaultClasses.init_category('level_fallback', baseclass=LevelObject)
DefaultClasses.init_category('fragments', baseclass=Fragment)
DefaultClasses.init_category('base_objects', baseclass=BaseObject)
DefaultClasses.init_category('base_fragments', baseclass=Fragment)
DefaultClasses.init_category('level', baseclass=Fragment)
DefaultClasses.init_category('level_content', baseclass=Fragment)
DefaultClasses.init_category('non_level_objects', baseclass=BaseObject, probe_baseclass=False)
DefaultClasses.init_category('blacklist_non_level_objects', baseclass=Fragment)
DefaultClasses.init_category('blacklist_non_customobject', baseclass=Fragment)
DefaultClasses.init_composite(
    'customobject', ['level_objects', 'blacklist_non_customobject'],
    baseclass=LevelObject)
DefaultClasses.init_composite(
    'level_like', ['level', 'level_objects', 'blacklist_non_level_objects'],
    baseclass=LevelObject)
DefaultClasses.init_composite(
    'file', ['level_objects', 'level', 'non_level_objects', 'level_fallback'],
    baseclass=Fragment)


def _impl_modules():
    return [
        'distance.base',
        'distance.levelfragments',
        'distance._impl.fragments.group',
        'distance._impl.fragments.levelfragments',
        'distance._impl.fragments.npfragments',
        'distance._impl.fragments.replay',
        'distance._impl.fragments.levelsettings',
        'distance._impl.fragments.leaderboard',
        'distance._impl.fragments.levelinfos',
        'distance._impl.fragments.profileprogress',
        'distance._impl.fragments.workshoplevelinfos',
        'distance._impl.fragments.info',
        'distance._impl.level_objects.group',
        'distance._impl.level_objects.objects',
        'distance._impl.level_content.layer',
        'distance._impl.level_content.newlevelsettings',
        'distance._impl.level_content.oldlevelsettings',
        'distance._level',
        'distance._nonlevel',
    ]


_autoload_module = 'distance._autoload._classes'


DefaultClasses.autoload_modules(_autoload_module, _impl_modules)


@DefaultClasses.non_level_objects.func('dst._core.nonlevel_fallback')
def _detect_non_level_objects_other(section):
    if section.magic == Magic[6]:
        # Replay requires dynamic check.
        from distance._nonlevel import Replay
        if section.type.startswith(Replay.type_prefix):
            return Replay
    return None


@DefaultClasses.level_fallback.func('dst._core.level_fallback')
def _level_fallback(section):
    if section.magic == Magic[6]:
        return LevelObject
    return None


@DefaultClasses.blacklist_non_level_objects.func('dst._core.blacklist_nonlevel')
def _blacklist_nonlevel(section):
    if section.magic == Magic[6]:
        if DefaultClasses.non_level_objects.probe_section(section) is BaseObject:
            return None
    raise ProbeError


@DefaultClasses.blacklist_non_customobject.func('dst._core.blacklist_non_customobject')
def _blacklist_non_customobject(section):
    if section.magic == Magic[6]:
        if DefaultClasses.non_level_objects.probe_section(section) is BaseObject:
            return None
    raise ProbeError


def write_autoload_modules():
    DefaultClasses.write_autoload_module(_autoload_module)


# vim:set sw=4 ts=8 sts=4 et:
