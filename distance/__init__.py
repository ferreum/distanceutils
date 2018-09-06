"""Read and modify .bytes files of the Refract Studios game Distance.

A detailed introduction to the usage of this module can be found at
https://gitlab.com/ferreum/distanceutils/blob/{version_tag}/GENERAL_USAGE.rst

"""


from distance._version import __version__

from distance._core import DefaultClasses

from distance._nonlevel import (
    Replay, Leaderboard, LevelInfos,
    ProfileProgress, WorkshopLevelInfos,
)
from distance._level import Level


__doc__ = __doc__.format(version_tag=f"v{__version__}")


__all__ = [
    'Level', 'Replay', 'Leaderboard', 'LevelInfos',
    'ProfileProgress', 'WorkshopLevelInfos',

    'DefaultClasses', 'PROBER',
]


PROBER = DefaultClasses.file


# vim:set sw=4 ts=8 sts=4 et:
