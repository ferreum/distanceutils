
from construct import Enum

from distance.bytes import Section, Magic
from distance.construct import (
    BaseConstructFragment,
    Byte, UInt, Int, Float, DstString,
    Struct, Default,
)
from distance.classes import CollectorGroup


Classes = CollectorGroup()


@Classes.fragments.fragment
class WarpAnchorFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x6e)
    container_versions = 18

    is_interesting = True

    _construct_ = Struct(
        # Basics
        # renamed from 'type' to prevent conflict with BaseObject's type attr
        'trigger_type' / Default(Enum(UInt, sphere=0, box=1), 0),
        'my_id' / Default(Int, 0),
        'other_id' / Default(Int, 0),
        'is_primary' / Default(Byte, 1),
        'snap_to_exit' / Default(Byte, 0),
        'one_time_use' / Default(Byte, 1),
        'ignore_in_arcade' / Default(Byte, 0),
        'ignore_in_adventure' / Default(Byte, 0),
        # Warp Style
        'type_of_warp' / Default(Enum(UInt, there_and_back=0, one_way=1), 0),
        'time_before_returning' / Default(Float, 0.01),
        'time_scale' / Default(Float, 1.0),
        'new_anchor_after_warp' / Default(Int, -1),
        # Delay
        'enable_delay' / Default(Byte, 0),
        'delay_time' / Default(Float, 0.0),
        'delay_time_scale' / Default(Float, 1.0),
        'glitch_during_delay' / Default(Byte, 0),
        'shake_during_delay' / Default(Byte, 0),
        'shake_during_delay_strength' / Default(Float, 0.75),
        # Archaic
        'connect_to_archaic' / Default(Byte, 0),
        'archaic_id' / Default(Int, -1),
        'action_index_before' / Default(Int, -1),
        'action_index_during' / Default(Int, -1),
        'action_index_after' / Default(Int, -1),
        'archaic_tractor_beam' / Default(Byte, 0),
        'archaic_tractor_beam_time' / Default(Float, 3.944),
        # Special Effects
        'transition_effect' / Default(Enum(UInt, none=0, glitch_short=1, glitch_long=2, teleport=3, teleport_virus=4), 0),
        'enable_corruption_effect' / Default(Byte, 1),
        'corruption_effect_color' / Default(Float[4], (0.0, 0.0, 0.0, 1.0)),
        'add_noise' / Default(Byte, 1),
        'bloom_out' / Default(Byte, 1),
        'vhs_during' / Default(Byte, 0),
        'shake_before_delay' / Default(Byte, 0),
        'shake_before' / Default(Byte, 0),
        'shake_after' / Default(Byte, 0),
        'shake_strength' / Default(Float, 0.75),
        'glitch_during' / Default(Byte, 1),
        'glitch_intensity' / Default(Float, 1.1),
        'glitch_filter_colors' / Default(Byte, 1),
        'glitch_up' / Default(Byte, 1),
        'glitch_down' / Default(Byte, 1),
        'glitch_displace' / Default(Byte, 1),
        'glitch_scale' / Default(Byte, 1),
        # EMP
        'enable_emp_after_warp' / Default(Byte, 0),
        'emp_radius' / Default(Float, 1000.0),
        'delay_before_turning_on_after_emp' / Default(Float, 3.0),
        'emp_section_randomness' / Default(Int, -1),
        # Audio
        'audio_high_pass_during' / Default(Byte, 1),
        'audio_low_pass_after' / Default(Byte, 1),
        'audio_event_before' / Default(DstString, ""),
        'audio_event_during' / Default(DstString, ""),
        'audio_event_after' / Default(DstString, ""),
        'archaic_audio' / Default(DstString, ""),
        # Car Timer
        'car_timer_state_before' / Default(UInt, 0),
        'car_timer_state_during' / Default(UInt, 1),
        'car_timer_state_after' / Default(UInt, 0),
        # Misc
        'show_countdown_and_gps_after' / Default(Byte, 0),
        'snap_countdown_to_time' / Default(Float, -1.0),
        'set_countdown_time_scale' / Default(Byte, 0),
        'countdown_time_scale' / Default(Float, 1.0),
        'disable_countdown' / Default(Byte, 0),
        'unk_0' / Default(UInt, 0),
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        with p.tree_children():
            p.tree_next_child()
            p("Basics:")
            p(f"Trigger type: {self.trigger_type}")
            p(f"My ID: {self.my_id}")
            p(f"Other ID: {self.other_id}")
            p(f"Is primary: {self.is_primary and 'yes' or 'no'}")
            if self.is_primary:
                p(f"Snap to exit: {self.snap_to_exit and 'yes' or 'no'}")
                p(f"One time use: {self.one_time_use and 'yes' or 'no'}")
                p(f"Ignore in arcade: {self.ignore_in_arcade and 'yes' or 'no'}")
                p(f"Ignore in arcade: {self.ignore_in_adventure and 'yes' or 'no'}")
                p.tree_next_child()
                p(f"Warp style:")
                p(f"Type of warp: {self.type_of_warp}")
                p(f"Time before returning: {self.time_before_returning}")
                p(f"Time scale: {self.time_scale}")
                p(f"New anchor after warp: {self.new_anchor_after_warp}")
                p.tree_next_child()
                p(f"Enable delay: {self.enable_delay and 'yes' or 'no'}")
                if self.enable_delay:
                    p(f"Delay time: {self.delay_time}")
                    p(f"Delay time scale: {self.delay_time_scale}")
                p.tree_next_child()
                p(f"Connect to archaic: {self.connect_to_archaic and 'yes' or 'no'}")
                if self.connect_to_archaic:
                    p(f"Archaic ID: {self.archaic_id}")
                    p(f"Archaic tractor beam: {self.archaic_tractor_beam and 'yes' or 'no'}")
                    p(f"Archaic tractor beam time: {self.archaic_tractor_beam_time}")
                p.tree_next_child()
                p(f"Transition effect: {self.transition_effect}")


# vim:set sw=4 et:
