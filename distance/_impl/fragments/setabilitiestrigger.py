

from distance.bytes import Section, Magic
from distance.construct import (
    BaseConstructFragment,
    Byte, Float, DstString,
    Struct, Default,
)
from distance.classes import CollectorGroup


Classes = CollectorGroup()


@Classes.fragments.fragment
class SetAbilitiesTriggerFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0xad)
    container_versions = 7

    _construct_ = Struct(
        'enable_flying' / Default(Byte, 1),
        'enable_jumping' / Default(Byte, 1),
        'enable_boosting' / Default(Byte, 1),
        'enable_jet_rotating' / Default(Byte, 1),
        'infinite_cooldown' / Default(Byte, 0),
        'delay' / Default(Float, 0.0),
        'show_ability_alert' / Default(Byte, 1),
        'bloom_out' / Default(Byte, 0),
        'play_sound' / Default(Byte, 1),
        'show_car_screen_image' / Default(Byte, 1),
        'timer_text' / Default(DstString, "downloading"),
        'ignore_in_arcade' / Default(Byte, 0),
        'use_slow_mo' / Default(Byte, 0),
        'delay_before_slow_mo' / Default(Float, 0.0),
        'slow_mo_time_scale' / Default(Float, 0.25),
        'slow_mo_duration' / Default(Float, 2.0),
        'glitch_duration_after' / Default(Float, 0.66),
        'play_slow_mo_audio' / Default(Byte, 1),
        'visuals_only' / Default(Byte, 0),
    )


# vim:set sw=4 et:
