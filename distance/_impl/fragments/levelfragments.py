

from construct import (
    If, this,
    Container,
)

from distance.bytes import Section, Magic
from distance.construct import (
    BaseConstructFragment,
    Byte, UInt, Float, DstString,
    Struct, Default, DstOptional, Remainder,
)
from distance.classes import CollectorGroup
from distance.constants import ForceType
from . import bases


Classes = CollectorGroup()


@Classes.fragments.fragment
class CarScreenTextDecodeTriggerFragment(bases.BaseCarScreenTextDecodeTrigger, BaseConstructFragment):

    container_versions = 1

    _construct_ = Struct(
        'text' / Default(DstString, ""),
        'per_char_speed' / Default(Float, 0),
        'clear_on_finish' / Default(Byte, 0),
        'clear_on_trigger_exit' / Default(Byte, 0),
        'destroy_on_trigger_exit' / Default(Byte, 0),
        'time_text' / Default(DstString, ""),
        'static_time_text' / Default(Byte, 1),
        'delay' / Default(Float, 0),
        'announcer_action' / Default(UInt, 0),
    )


@Classes.fragments.fragment
class GoldenSimplesFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x83)
    container_versions = 3

    _construct_ = Struct(
        'image_index' / Default(UInt, 17),
        'emit_index' / Default(UInt, 17),
        'preset' / Default(UInt, 0),
        'tex_scale' / Default(Float[3], (1, 1, 1)),
        'tex_offset' / Default(Float[3], (0, 0, 0)),
        'flip_tex_uv' / Default(Byte, 0),
        'world_mapped' / Default(Byte, 0),
        'disable_diffuse' / Default(Byte, 0),
        'disable_bump' / Default(Byte, 0),
        'bump_strength' / Default(Float, 0),
        'disable_reflect' / Default(Byte, 0),
        'disable_collision' / Default(Byte, 0),
        'additive_transp' / Default(Byte, 0),
        'multip_transp' / Default(Byte, 0),
        'invert_emit' / Default(Byte, 0),
    )


@Classes.fragments.fragment
class TeleporterEntranceFragment(bases.BaseTeleporterEntrance, BaseConstructFragment):

    container_versions = 1, 2, 3

    _construct_ = Struct(
        'destination' / Default(UInt, 0),
        'rem' / Remainder,
    )


@Classes.fragments.fragment
class TeleporterExitFragment(bases.BaseTeleporterExit, BaseConstructFragment):

    container_versions = 1

    _construct_ = Struct(
        'link_id' / Default(UInt, 0),
    )


@Classes.fragments.fragment
class TeleporterExitCheckpointFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x51)
    container_versions = 0

    _construct_ = Struct(
        'trigger_checkpoint' / Default(Byte, 1),
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if self.trigger_checkpoint is not None:
            p(f"Trigger checkpoint: {self.trigger_checkpoint}")


@Classes.fragments.fragment
class SphereColliderFragment(BaseConstructFragment):

    base_container = Section.base(Magic[3], 0x0e)
    container_versions = 1

    _construct_ = Struct(
        'trigger_center' / Default(DstOptional(Float[3]), None),
        'trigger_radius' / Default(DstOptional(Float), None),
    )


@Classes.fragments.fragment
class BoxColliderFragment(BaseConstructFragment):

    base_container = Section.base(Magic[3], 0xf)
    container_versions = 2

    _construct_ = Struct(
        'trigger_center' / Default(DstOptional(Float[3]), None),
        'trigger_size' / Default(DstOptional(Float[3]), None),
    )


@Classes.fragments.fragment
class GravityToggleFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x45)
    container_versions = 1

    is_interesting = True

    _construct_ = Struct(
        'disable_gravity' / Default(Byte, 1),
        'drag_scale' / Default(Float, 1.0),
        'drag_scale_angular' / Default(Float, 1.0),
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if self.disable_gravity is not None:
            p(f"Disable gravity: {self.disable_gravity and 'yes' or 'no'}")
        if self.drag_scale is not None:
            p(f"Drag scale: {self.drag_scale}")
        if self.drag_scale_angular is not None:
            p(f"Angular drag scale: {self.drag_scale_angular}")


@Classes.fragments.fragment
class MusicTriggerFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x4b)
    container_versions = 1

    is_interesting = True

    _construct_ = Struct(
        'music_id' / Default(UInt, 19),
        'one_time_trigger' / Default(Byte, 1),
        'reset_before_trigger' / Default(Byte, 0),
        'disable_music_trigger' / Default(Byte, 0),
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if self.music_id is not None:
            p(f"Music ID: {self.music_id}")
        if self.one_time_trigger is not None:
            p(f"One time trigger: {self.one_time_trigger and 'yes' or 'no'}")
        if self.reset_before_trigger is not None:
            p(f"Reset before trigger: {self.reset_before_trigger and 'yes' or 'no'}")
        if self.disable_music_trigger is not None:
            p(f"Disable music trigger: {self.disable_music_trigger and 'yes' or 'no'}")


@Classes.fragments.fragment
class ForceZoneFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0xa0)
    container_versions = 0

    is_interesting = True

    _construct_ = Struct(
        'force_direction' / Default(DstOptional(Float[3], (0.0, 0.0, 1.0)), (0.0, 0.0, 1.0)),
        'global_force' / Default(Byte, 0),
        'force_type' / Default(UInt, ForceType.WIND),
        'gravity_magnitude' / Default(Float, 25.0),
        'disable_global_gravity' / Default(Byte, 0),
        'wind_speed' / Default(Float, 300.0),
        'drag_multiplier' / Default(Float, 1.0)
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if self.force_direction:
            dir_str = ', '.join(str(v) for v in self.force_direction)
            p(f"Force direction: {dir_str}")
        if self.global_force is not None:
            p(f"Global force: {self.global_force and 'yes' or 'no'}")
        if self.force_type is not None:
            p(f"Force type: {ForceType.to_name(self.force_type)}")
        if self.force_type == ForceType.WIND:
            p(f"Wind speed: {self.wind_speed}")
            p(f"Drag multiplier: {self.drag_multiplier}")
        elif self.force_type == ForceType.GRAVITY:
            p(f"Magnitude: {self.gravity_magnitude}")
            p(f"Disable global gravity: {self.disable_global_gravity and 'yes' or 'no'}")
            p(f"Drag multiplier: {self.drag_multiplier}")


@Classes.fragments.fragment
class TextMeshFragment(BaseConstructFragment):

    base_container = Section.base(Magic[3], 0x7)
    container_versions = 1, 2

    is_interesting = True

    _construct_ = Struct(
        'text' / Default(DstOptional(DstString), None),
        'font_style' / Default(DstOptional(UInt), None),
        'font' / If(this._params.sec.version >= 2, Default(DstOptional(UInt), None)),
        'rem' / Default(Remainder, b''),
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        p(f"World text: {self.text!r}")


@Classes.fragments.fragment
class TrackNodeFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x16)
    container_versions = 2

    _construct_ = Struct(
        'parent_id' / Default(UInt, 0),
        'snap_id' / Default(UInt, 0),
        'conn_id' / Default(UInt, 0),
        'primary' / Default(Byte, 0),
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if 'sections' in p.flags or 'track' in p.flags:
            p(f"Parent ID: {self.parent_id}")
            p(f"Snapped to: {self.snap_id}")
            p(f"Connection ID: {self.conn_id}")
            p(f"Primary: {self.primary and 'yes' or 'no'}")


@Classes.fragments.fragment
class InfoDisplayLogicFragment(bases.BaseInfoDisplayLogic, BaseConstructFragment):

    container_versions = 2

    _construct_ = Struct(
        'fadeout_time' / Default(Float, 1.0),
        'entries' / Struct(
            'delay' / Float,
            'text' / DstString,
        )[5],
        'random_char_count' / Default(UInt, 1),
        'per_char_speed' / Default(Float, 0.035),
        'destroy_on_trigger_exit' / Default(Byte, 0),
        'display_in_arcade' / Default(Byte, 0),
    )

    _add_fields_ = dict(
        texts = (),
    )

    @property
    def texts(self):
        return [e.text for e in (self.entries or ())]

    @texts.setter
    def texts(self, value):
        self.entries = [Container(e.delay, t)
                        for e, t in zip(self.entries, value)]


@Classes.fragments.fragment
class AnimatorFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x9a)
    container_versions = 7, 10, 11

    _construct_ = Struct(
        # 2: hinge
        'motion_mode' / Default(UInt, 2),
        'do_scale' / Default(Byte, 0),
        'scale_exponents' / Default(Float[3], (0, 1, 0)),
        'do_rotate' / Default(Byte, 1),
        'rotate_axis' / Default(Float[3], (0, 1, 0)),
        'rotate_global' / Default(Byte, 0),
        'rotate_magnitude' / Default(Float, 90),
        'centerpoint' / Default(Float[3], (0, 0, 0)),
        # 0: none
        'translate_type' / Default(UInt, 0),
        'translate_vector' / Default(Float[3], (0, 10, 0)),
        'follow_track_distance' / Default(Float, 25),
        'double_pivot_distance' / Default(If(this._params.sec.version >= 11, Float), 0.0),
        'follow_percent_of_track' / Default(If(this._params.sec.version >= 10, Byte), 1),
        'wrap_around' / Default(If(this._params.sec.version >= 10, Byte), 1),
        'projectile_gravity' / Default(Float[3], (0, -25, 0)),
        'delay' / Default(Float, 1),
        'duration' / Default(Float, 1),
        'time_offset' / Default(Float, 0),
        'do_loop' / Default(Byte, 1),
        # 1: pingpong
        'extrapolation_type' / Default(If(this._params.sec.version <= 7, UInt), 1),
        'do_extend' / Default(If(this._params.sec.version >= 10, Byte), 0),
        # 3: ease in out
        'curve_type' / Default(UInt, 3),
        'editor_anim_time' / Default(Float, 0),
        'use_custom_pong_values' / Default(Byte, 0),
        'pong_delay' / Default(Float, 1),
        'pong_duration' / Default(Float, 1),
        # 2: ease in out
        'pong_curve_type' / Default(UInt, 2),
        'anim_physics' / Default(Byte, 1),
        'always_animate' / Default(Byte, 0),
        # 1: play
        'default_action' / Default(UInt, 1),
        # 1: play
        'trigger_on_action' / Default(UInt, 1),
        'trigger_wait_for_anim_finish' / Default(Byte, 0),
        'trigger_on_reset' / Default(Byte, 0),
        # 2: play reverse
        'trigger_off_action' / Default(UInt, 2),
        'trigger_off_wait_for_anim_finish' / Default(Byte, 0),
        'trigger_off_reset' / Default(Byte, 0),
    )


@Classes.fragments.fragment
class EventListenerFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x8a)
    container_versions = 1, 2

    _construct_ = Struct(
        'event_name' / Default(DstString, "Event 0"),
        'delay' / If(this._params.sec.version >= 2, Default(Float, 0.0)),
    )


@Classes.fragments.fragment
class EventTriggerFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x89)
    container_versions = 2
    is_interesting = True

    _construct_ = Struct(
        'event_name' / Default(DstString, "Event 0"),
        'one_shot' / Default(Byte, 0),
    )


@Classes.fragments.fragment
class InterpolateToPositionOnTriggerFragment(
        bases.BaseInterpolateToPositiononTrigger, BaseConstructFragment):

    container_versions = 1, 2

    _construct_ = Struct(
        'actually_interpolate' / Default(Byte, 0),
        'relative' / Default(Byte, 1),
        'interp_end_pos' / Default(DstOptional(Float[3]), None),
        'interp_time' / Default(Float, None),
        'local_movement' / Default(If(this._.sec.version >= 2, Byte), 0),
    )


@Classes.fragments.fragment
class RigidbodyAxisRotationLogicFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x17)
    container_versions = 1

    _construct_ = Struct(
        'angular_speed' / Float,
        'rotation_axis' / UInt,
        'limit_rotation' / Byte,
        'rotation_bounds' / Float,
        'starting_angle_offset' / Float,
    )


# vim:set sw=4 ts=8 sts=4 et:
