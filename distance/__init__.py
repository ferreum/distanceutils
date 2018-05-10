"""Utilities for the Refract Studios game Distance.

There are different classes for reading different types of .bytes files.
Additionally, PROBER can be used to detect any of these files.

Example for accessing objects of a level:

>>> from distance import Level
>>> level = Level("tests/in/level/test-straightroad.bytes")
>>> level.settings.name
'Test-straightroad'
>>> level.layers[0].objects[-1].type
'EmpireEndZone'

The argument of the constructor can be a str or bytes containing the path of
the file, or an already opened binary file.

These classes (and where to find the corresponding files in the profile) can be
used to open .bytes files:

Leaderboard        - LocalLeaderboards/**/<mode_id>.bytes
Level              - Levels/**.bytes
LevelInfos         - Settings/LevelInfos.bytes
ProfilePrgress     - Profiles/Progress/<name>.bytes
Replay             - LocalLeaderboards/**/<mode_id>_<rep_id>.bytes
WorkshopLevelInfos - Levels/WorkshopLevels/WorkshopLevelInfos.bytes

The PROBER can be used to detect any of these files:

>>> from distance import PROBER
>>> obj = PROBER.read("tests/in/leaderboard/version_1.bytes")
>>> obj.type
'LocalLeaderboard'

The PROBER is also used to open CustomObject files.

Passing str or bytes to the classes reads the whole file into memory first.
This is required because no context manager can be used and the file has to be
closed immediately. If this is undesired, open the file manually (Note: this
direct I/O may be slower if a lot of data is accessed):

>>> from distance import Level
>>> with open("tests/in/level/test-straightroad.bytes", 'rb') as f:
...     level = Level(f)
...     level.layers[0].objects[0].type
'LevelEditorCarSpawner'

Content of files is read on-demand as it is accessed. This means that the file
needs to be kept open for as long as the object is used. This also means that
the file needs to be seekable.
This lazy-loading changes the seek position of the file.

"""


from distance.level import Level
from distance.replay import Replay
from distance.leaderboard import Leaderboard
from distance.levelinfos import LevelInfos
from distance.profileprogress import ProfileProgress
from distance.workshoplevelinfos import WorkshopLevelInfos

from distance.knowntypes import PROBER

from distance.constants import (
    AbilityToggle, Completion, Difficulty,
    ForceType, Mode, Rating
)


__all__ = [
    'Level', 'Replay', 'Leaderboard', 'LevelInfos',
    'ProfileProgress', 'WorkshopLevelInfos', 'PROBER',

    'AbilityToggle', 'Completion', 'Difficulty',
    'ForceType', 'Mode', 'Rating',
]

__version__ = '0.4.6'


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
