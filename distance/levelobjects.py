"""Level objects."""


from .bytes import (
    Section,
    MAGIC_2, MAGIC_3, MAGIC_6
)
from .base import BaseObject
from .fragments import (
    PROBER as FRAG_PROBER,
    ForwardFragmentAttrs,
    ForwardFragmentColors,
    GoldenSimplesFragment,
    GroupFragment,
    CustomNameFragment,
    BaseTeleporterEntranceFragment,
    BaseTeleporterExitFragment,
    TeleporterExitCheckpointFragment,
    RaceEndLogicFragment,
    ForceZoneFragment,
    TextMeshFragment,
    EnableAbilitiesTriggerFragment,
    SphereColliderFragment,
    GravityToggleFragment,
    MusicTriggerFragment,
    BaseCarScreenTextDecodeTriggerFragment,
    BaseInfoDisplayLogicFragment,
)
from .prober import BytesProber
from .printing import need_counters


def print_objects(p, gen):
    counters = p.counters
    for obj in gen:
        p.tree_next_child()
        counters.num_objects += 1
        if 'numbers' in p.flags:
            p(f"Level object: {counters.num_objects}")
        p.print_data_of(obj)


PROBER = BytesProber()

SUBOBJ_PROBER = BytesProber()


@PROBER.func
def _fallback_object(section):
    if section.magic == MAGIC_6:
        return LevelObject
    return None


@SUBOBJ_PROBER.func
def _fallback_subobject(section):
    if section.magic == MAGIC_6:
        return SubObject
    return None


class LevelObject(BaseObject):

    child_prober = SUBOBJ_PROBER
    fragment_prober = FRAG_PROBER

    def _handle_opts(self, opts):
        try:
            self.fragment_prober = opts['level_frag_prober']
        except KeyError:
            pass
        try:
            self.children_prober = opts['level_subobj_prober']
        except KeyError:
            pass

    def _print_children(self, p):
        if 'subobjects' in p.flags and self.children:
            num = len(self.children)
            p(f"Subobjects: {num}")
            with p.tree_children():
                for obj in self.children:
                    p.tree_next_child()
                    p.print_data_of(obj)


class SubObject(LevelObject):

    def _print_type(self, p):
        start_sec = self.start_section
        if start_sec and start_sec.magic == MAGIC_6:
            type_str = start_sec.type
            p(f"Subobject type: {type_str!r}")


@PROBER.for_type('Group')
class Group(ForwardFragmentAttrs, LevelObject):

    child_prober = PROBER
    is_object_group = True
    has_children = True
    type = 'Group'

    default_sections = (
        *LevelObject.default_sections,
        Section(MAGIC_2, 0x1d, version=1),
        Section(MAGIC_2, 0x63, version=0),
    )

    forward_fragment_attrs = (
        (GroupFragment, GroupFragment.value_attrs),
        (CustomNameFragment, CustomNameFragment.value_attrs),
    )

    def _handle_opts(self, opts):
        LevelObject._handle_opts(self, opts)
        try:
            self.child_prober = opts['level_obj_prober']
        except KeyError:
            pass

    def _print_children(self, p):
        with need_counters(p) as counters:
            num = len(self.children)
            if num:
                p(f"Grouped objects: {num}")
                if 'groups' in p.flags:
                    p.counters.grouped_objects += num
                    with p.tree_children():
                        print_objects(p, self.children)
            if counters:
                counters.print_data(p)

    def recenter(self, center):
        pos, rot, scale = self.transform or ((0, 0, 0), (), ())
        self.transform = center, rot, scale
        diff = tuple(c - o for c, o in zip(pos, center))
        for obj in self.children:
            pos, rot, scale = obj.transform or ((0, 0, 0), (), ())
            pos = tuple(o + d for o, d in zip(pos, diff))
            obj.transform = pos, rot, scale


@SUBOBJ_PROBER.for_type('Teleporter')
class SubTeleporter(ForwardFragmentAttrs, SubObject):

    forward_fragment_attrs = (
        (BaseTeleporterEntranceFragment, dict(destination=None)),
        (BaseTeleporterExitFragment, dict(link_id=None)),
        (TeleporterExitCheckpointFragment, dict(trigger_checkpoint=None)),
    )


@SUBOBJ_PROBER.for_type('WinLogic')
class WinLogic(ForwardFragmentAttrs, SubObject):

    forward_fragment_attrs = (
        (RaceEndLogicFragment, dict(delay_before_broadcast=None)),
    )


@PROBER.for_type('WorldText')
class WorldText(ForwardFragmentAttrs, LevelObject):

    forward_fragment_attrs = (
        (TextMeshFragment, dict(text=None)),
    )


@PROBER.for_type('InfoDisplayBox')
class InfoDisplayBox(ForwardFragmentAttrs, LevelObject):

    forward_fragment_attrs = (
        (BaseInfoDisplayLogicFragment, dict(
            fadeout_time = None,
            texts = (),
            per_char_speed = None,
            destroy_on_trigger_exit = None,
            random_char_count = None,
        )),
    )


@PROBER.for_type('CarScreenTextDecodeTrigger')
class CarScreenTextDecodeTrigger(ForwardFragmentAttrs, LevelObject):

    forward_fragment_attrs = (
        (BaseCarScreenTextDecodeTriggerFragment, dict(
            text = None,
            per_char_speed = None,
            clear_on_finish = None,
            clear_on_trigger_exit = None,
            destroy_on_trigger_exit = None,
            static_time_text = None,
            time_text = None,
            delay = None,
            announcer_action = None,
            announcer_phrases = (),
        )),
    )


@PROBER.for_type('GravityTrigger')
class GravityTrigger(ForwardFragmentAttrs, LevelObject):

    forward_fragment_attrs = (
        (SphereColliderFragment, dict(
            trigger_center = None,
            trigger_radius = None,
        )),
        (GravityToggleFragment, dict(
            disable_gravity = None,
            drag_scale = None,
            drag_scale_angular = None,
        )),
        (MusicTriggerFragment, dict(
            music_id = None,
            one_time_trigger = None,
            reset_before_trigger = None,
            disable_music_trigger = None,
        )),
    )


@PROBER.for_type('ForceZoneBox')
class ForceZoneBox(ForwardFragmentAttrs, LevelObject):

    forward_fragment_attrs = (
        (CustomNameFragment, CustomNameFragment.value_attrs),
        (ForceZoneFragment, ForceZoneFragment.value_attrs),
    )


@PROBER.for_type('EnableAbilitiesBox')
class EnableAbilitiesBox(ForwardFragmentAttrs, LevelObject):

    forward_fragment_attrs = (
        (EnableAbilitiesTriggerFragment, {'abilities', 'bloom_out'}),
    )


@PROBER.for_type('WedgeGS')
class WedgeGS(ForwardFragmentAttrs, ForwardFragmentColors, LevelObject):

    type = 'WedgeGS'
    has_children = True

    default_sections = (
        *LevelObject.default_sections,
        Section(MAGIC_3, 3, 2),
        Section(MAGIC_2, 0x83, 3),
    )

    forward_fragment_colors = dict(
        mat_color = ('SimplesMaterial', '_Color', (.3, .3, .3, 1)),
        mat_emit = ('SimplesMaterial', '_EmitColor', (.8, .8, .8, .5)),
        mat_reflect = ('SimplesMaterial', '_ReflectColor', (.3, .3, .3, .9)),
        mat_spec = ('SimplesMaterial', '_SpecColor', (1, 1, 1, 1)),
    )

    forward_fragment_attrs = (
        (GoldenSimplesFragment, GoldenSimplesFragment.value_attrs),
    )


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
