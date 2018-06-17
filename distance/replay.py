"""Read replay metadata."""


from .bytes import S_COLOR_RGBA, Magic
from .base import (
    BaseObject, Fragment,
    ForwardFragmentAttrs,
    require_type,
)
from .printing import format_duration, format_color
from ._common import set_default_attrs
from ._default_probers import DefaultProbers


FTYPE_REPLAY_PREFIX = "Replay: "

FILE_PROBER = DefaultProbers.file.transaction()
FRAG_PROBER = DefaultProbers.fragments.transaction()

_value_attrs = dict(
    version = None,
    player_name = None,
    player_name_2 = None,
    player_id = None,
    finish_time = None,
    replay_duration = None,
    car_name = None,
    car_color_primary = None,
    car_color_secondary = None,
    car_color_glow = None,
    car_color_sparkle = None,
)


@FRAG_PROBER.fragment(Magic[2], 0x7f, any_version=True)
@set_default_attrs(_value_attrs)
class ReplayFragment(Fragment):

    is_interesting = True

    value_attrs = _value_attrs

    def _read_section_data(self, dbytes, sec):
        # demo data
        self.version = version = sec.version
        self.player_name = dbytes.read_str()
        if version >= 2:
            self.player_id = dbytes.read_uint8()
            self.player_name_2 = dbytes.read_str()
            if version >= 3:
                self.finish_time = dbytes.read_uint4()
                self.replay_duration = dbytes.read_uint4()
        dbytes.read_bytes(4)
        self.car_name = dbytes.read_str()
        self.car_color_primary = dbytes.read_struct(S_COLOR_RGBA)
        self.car_color_secondary = dbytes.read_struct(S_COLOR_RGBA)
        self.car_color_glow = dbytes.read_struct(S_COLOR_RGBA)
        self.car_color_sparkle = dbytes.read_struct(S_COLOR_RGBA)

        if version <= 1:
            dbytes.require_equal_uint4(Magic[1])
            section_size = dbytes.read_uint4() * 4
            dbytes.read_bytes(section_size)
            dbytes.require_equal_uint4(Magic[1])
            section_size = dbytes.read_uint4()
            dbytes.read_bytes(section_size - 8)
            self.finish_time = dbytes.read_uint4()

    def _print_data(self, p):
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


@ForwardFragmentAttrs(ReplayFragment, **ReplayFragment.value_attrs)
@require_type(func=lambda t: t.startswith(FTYPE_REPLAY_PREFIX))
class Replay(BaseObject):

    fragment_prober = FRAG_PROBER


@FILE_PROBER.func('Replay,BaseObject')
def _detect_other(section):
    if section.magic == Magic[6]:
        if section.type.startswith(FTYPE_REPLAY_PREFIX):
            return Replay
    return None


FRAG_PROBER.commit()
FILE_PROBER.commit()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
