"""Read replay metadata."""


from .bytes import S_COLOR_RGBA, MAGIC_1, MAGIC_2
from .base import BaseObject, Fragment, BASE_FRAG_PROBER
from .fragments import ForwardFragmentAttrs
from .prober import BytesProber
from .printing import format_duration, format_color


FTYPE_REPLAY_PREFIX = "Replay: "


FRAG_PROBER = BytesProber()


FRAG_PROBER.extend(BASE_FRAG_PROBER)


@FRAG_PROBER.fragment(MAGIC_2, 0x7f, 0)
@FRAG_PROBER.fragment(MAGIC_2, 0x7f, 1)
@FRAG_PROBER.fragment(MAGIC_2, 0x7f, 2)
@FRAG_PROBER.fragment(MAGIC_2, 0x7f, 3)
@FRAG_PROBER.fragment(MAGIC_2, 0x7f, 4)
class ReplayFragment(Fragment):

    value_attrs = dict(
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

    locals().update(value_attrs)

    def _read_section_data(self, dbytes, sec):
        # demo data
        self.version = version = sec.version
        self.player_name = dbytes.read_str()
        if version >= 2:
            self.player_id = dbytes.read_int(8)
            self.player_name_2 = dbytes.read_str()
            if version >= 3:
                self.finish_time = dbytes.read_int(4)
                self.replay_duration = dbytes.read_int(4)
        self._add_unknown(4)
        self.car_name = dbytes.read_str()
        self.car_color_primary = dbytes.read_struct(S_COLOR_RGBA)
        self.car_color_secondary = dbytes.read_struct(S_COLOR_RGBA)
        self.car_color_glow = dbytes.read_struct(S_COLOR_RGBA)
        self.car_color_sparkle = dbytes.read_struct(S_COLOR_RGBA)

        if version <= 1:
            self._require_equal(MAGIC_1, 4)
            section_size = dbytes.read_int(4) * 4
            dbytes.read_bytes(section_size)
            self._require_equal(MAGIC_1, 4)
            section_size = dbytes.read_int(4)
            dbytes.read_bytes(section_size - 8)
            self.finish_time = dbytes.read_int(4)
        return False


class Replay(ForwardFragmentAttrs, BaseObject):

    fragment_prober = FRAG_PROBER

    forward_fragment_attrs = (
        (ReplayFragment, ReplayFragment.value_attrs),
    )

    def _read(self, dbytes):
        self._require_type(lambda t: t.startswith(FTYPE_REPLAY_PREFIX))
        BaseObject._read(self, dbytes)

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


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
