"""Read replay metadata."""


from construct import (
    Struct, Bytes, Computed, If, Const,
    this,
)

from .bytes import Magic, Section
from .base import (
    BaseObject,
    ForwardFragmentAttrs,
    require_type,
)
from .construct import (
    BaseConstructFragment,
    UInt, ULong, Float, DstString, Remainder,
)
from .printing import format_duration, format_color
from ._default_probers import DefaultProbers


FTYPE_REPLAY_PREFIX = "Replay: "

FILE_PROBER = DefaultProbers.file.transaction()
FRAG_PROBER = DefaultProbers.fragments.transaction()

@FRAG_PROBER.fragment(any_version=True)
class ReplayFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x7f)

    is_interesting = True

    _construct = Struct(
        'version' / Computed(this._params.sec.version),
        'player_name' / DstString,
        'player_id' / If(this.version >= 2, ULong),
        'player_name_2' / If(this.version >= 2, DstString),
        'finish_time_v3' / If(this.version >= 3, UInt),
        'replay_duration' / If(this.version >= 3, UInt),
        'unk_0' / Bytes(4),
        'car_name' / DstString,
        'car_color_primary' / Float[4],
        'car_color_secondary' / Float[4],
        'car_color_glow' / Float[4],
        'car_color_sparkle' / Float[4],
        If(this.version <= 1, Const(Magic[1], UInt)),
        'unk_1_size' / If(this.version <= 1, UInt),
        'unk_1' / If(this.version <= 1, Bytes(this.unk_1_size * 4)),
        If(this.version <= 1, Const(Magic[1], UInt)),
        'unk_2_size' / If(this.version <= 1, UInt),
        'unk_2' / If(this.version <= 1, Bytes(this.unk_2_size - 8)),
        'finish_time_v1' / If(this.version <= 1, UInt),
        'rem' / Remainder,
    )

    @property
    def finish_time(self):
        t = self.finish_time_v3
        if t is None:
            t = self.finish_time_v1
        return t

    @finish_time.setter
    def finish_time(self, value):
        self.finish_time_v1 = value
        self.finish_time_v3 = value

    def _print_data(self, p):
        super()._print_data(p)
        p(f"Version: {self.version}")
        p(f"Player name: {self.player_name!r}")
        p(f"Player name: {self.player_name_2!r}")
        p(f"Player ID: {self.player_id}")
        p(f"Finish time: {format_duration(self.finish_time)}")
        p(f"Replay duration: {format_duration(self.replay_duration)}")
        p(f"Car name: {self.car_name!r}")
        p(f"Car color primary: {format_color(self.car_color_primary)}")
        p(f"Car color secondary: {format_color(self.car_color_secondary)}")
        p(f"Car color glow: {format_color(self.car_color_glow)}")
        p(f"Car color sparkle: {format_color(self.car_color_sparkle)}")


@ForwardFragmentAttrs(ReplayFragment, finish_time=None, **ReplayFragment._fields_map)
@require_type(func=lambda t: t.startswith(FTYPE_REPLAY_PREFIX))
class Replay(BaseObject):
    pass


@FILE_PROBER.func('Replay')
def _detect_other(section):
    if section.magic == Magic[6]:
        if section.type.startswith(FTYPE_REPLAY_PREFIX):
            return Replay
    return None


FRAG_PROBER.commit()
FILE_PROBER.commit()


# vim:set sw=4 ts=8 sts=4 et:
