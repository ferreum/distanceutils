

from construct import (
    Struct,
)

from distance.bytes import Magic, Section
from distance.construct import (
    BaseConstructFragment,
    Bytes,
    DstString, Remainder,
)
from distance.classes import CollectorGroup
from .levelsettings_base import BaseLevelSettings


Classes = CollectorGroup()


@Classes.level_content.fragment
class OldLevelSettings(BaseLevelSettings, BaseConstructFragment):

    """Special settings section only found in very old maps."""

    class_tag = 'OldLevelSettings'
    default_container = Section(Magic[8])

    # fallbacks for base LevelSettings and other usages
    version = None
    description = None
    author_name = None
    modes = ()
    medal_times = ()
    medal_scores = ()
    background_layer = None
    abilities = ()
    difficulty = None

    _construct_ = Struct(
        'unk_0' / Bytes(4),
        'skybox_name' / DstString,
        'unk_1' / Bytes(143),
        'name' / DstString,
        'unk_2' / Remainder,
    )

    def _print_type(self, p):
        p(f"Type: LevelSettings (old)")


# vim:set sw=4 et:
