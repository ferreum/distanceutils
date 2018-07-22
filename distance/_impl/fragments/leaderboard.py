

from construct import (
    Struct, Computed, Rebuild, If, Default,
    Bytes,
    this, len_,
)

from distance.bytes import Magic, Section
from distance.construct import (
    BaseConstructFragment,
    UInt, DstString, ULong,
)
from distance.prober import ProberGroup


NO_REPLAY = 0xffffffff_ffffffff


Probers = ProberGroup()


@Probers.fragments.fragment(any_version=True)
class LeaderboardFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x37)

    _construct = Struct(
        version = Computed(this._params.sec.version),
        num_entries = Rebuild(UInt, len_(this.entries)),
        unk_1 = Bytes(4),
        unk_2 = If(this.version >= 1, Bytes(4)),
        entries = Default(Struct(
            playername = DstString,
            time = UInt,
            unk_1 = If(this._.version == 0, UInt),
            replay = If(this._.version >= 1, Default(ULong, NO_REPLAY)),
            unk_2 = If(this._.version >= 1, Bytes(12))
        )[this.num_entries], ()),
    )


# vim:set sw=4 et:
