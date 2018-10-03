

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

    is_interesting = True

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

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        p(f"Enable flying: {self.enable_flying and 'yes' or 'no'}")
        p(f"Enable jumping: {self.enable_jumping and 'yes' or 'no'}")
        p(f"Enable boosting: {self.enable_boosting and 'yes' or 'no'}")
        p(f"Enable jet rotating: {self.enable_jet_rotating and 'yes' or 'no'}")
        p(f"Infinite cooldown: {self.infinite_cooldown and 'yes' or 'no'}")
        p(f"Delay: {self.delay}")
        p(f"Timer text: {self.timer_text!r}")
        p(f"Ignore in arcade: {self.ignore_in_arcade and 'yes' or 'no'}")
        p(f"Use slow mo: {self.use_slow_mo and 'yes' or 'no'}")
        if self.use_slow_mo:
            p(f"Delay before slow mo: {self.delay_before_slow_mo}")
            p(f"Slow mo time scale: {self.slow_mo_time_scale}")
            p(f"Slow mo duration: {self.slow_mo_duration}")
            p(f"Glitch duration after: {self.glitch_duration_after}")
        p(f"Visuals only: {self.visuals_only and 'yes' or 'no'}")


# vim:set sw=4 et:
