

from construct import (
    Struct, Sequence,
    PrefixedArray, If, Computed,
    this,
)

from distance.bytes import Magic, Section
from distance.construct import (
    BaseConstructFragment,
    Int, UInt, Bytes, Byte, Float,
    DstString, Remainder,
)
from distance.classes import CollectorGroup
from distance._common import (
    ModesMapperProperty,
    MedalTimesMapperProperty,
    MedalScoresMapperProperty,
)
from distance._impl.level_content.levelsettings_base import BaseLevelSettings


Classes = CollectorGroup()


@Classes.fragments.fragment(any_version=True)
class LevelSettingsFragment(BaseLevelSettings, BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x52)

    is_interesting = True

    def get_unk_2_size(this):
        version = this.version
        if version <= 3:
            return 57
        elif version == 4:
            return 141
        elif version == 5:
            return 172
        elif 6 <= version < 25:
            # confirmed only for v6..v9
            return 176
        else:
            # confirmed for v25..v26
            return 231

    _construct_ = Struct(
        'version' / Computed(this._params.sec.version),
        'unk_0' / Bytes(8),
        'name' / DstString,
        'description' / If(this.version >= 25, DstString),
        'author_name' / If(this.version >= 25, DstString),
        'unk_1' / Bytes(4),
        'modes_list' / PrefixedArray(UInt, Struct(
            'mode' / UInt,
            'enabled' / Byte,
        )),
        'music_id' / UInt,
        'skybox_name' / If(this.version <= 3, DstString),
        'unk_2' / Bytes(get_unk_2_size),
        # confirmed for v25..26
        'background_layer' / If(this.version >= 25, DstString),
        # confirmed for v25..26
        'unk_3' / If(this.version >= 25, Bytes(61)),
        'medals' / Struct(
            'time' / Float,
            'score' / Int,
        )[4],
        'abilities' / If(this.version >= 1, Sequence(Byte, Byte, Byte, Byte, Byte)),
        'difficulty' / If(this.version >= 2, UInt),
        'unk_4' / Remainder,
    )

    _add_fields_ = dict(
        modes = (),
        medal_times = None,
        medal_scores = None,
    )

    del get_unk_2_size

    modes = ModesMapperProperty('modes_list')

    medal_times = MedalTimesMapperProperty('medals')

    medal_scores = MedalScoresMapperProperty('medals')


# vim:set sw=4 et:
