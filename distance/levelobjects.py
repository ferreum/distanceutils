"""Level objects."""


from .bytes import (
    Section,
    MAGIC_2, MAGIC_3, MAGIC_6
)
from .base import BaseObject, ForwardFragmentAttrs
from .levelfragments import (
    PROBER as FRAG_PROBER,
    ForwardMaterialColors,
    GoldenSimplesFragment,
    GroupFragment,
    CustomNameFragment,
    BaseTeleporterEntrance,
    BaseTeleporterExit,
    TeleporterExitCheckpointFragment,
    RaceEndLogicFragment,
    ForceZoneFragment,
    TextMeshFragment,
    EnableAbilitiesTriggerFragment,
    SphereColliderFragment,
    GravityToggleFragment,
    MusicTriggerFragment,
    BaseCarScreenTextDecodeTrigger,
    BaseInfoDisplayLogic,
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
        container = self.container
        if container and container.magic == MAGIC_6:
            type_str = container.type
            p(f"Subobject type: {type_str!r}")


@PROBER.for_type('Group')
@ForwardFragmentAttrs(GroupFragment, **GroupFragment.value_attrs)
@ForwardFragmentAttrs(CustomNameFragment, **CustomNameFragment.value_attrs)
class Group(LevelObject):

    child_prober = PROBER
    is_object_group = True
    has_children = True
    type = 'Group'

    default_sections = (
        *LevelObject.default_sections,
        Section(MAGIC_2, 0x1d, version=1),
        Section(MAGIC_2, 0x63, version=0),
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
@ForwardFragmentAttrs(BaseTeleporterEntrance, destination=None)
@ForwardFragmentAttrs(BaseTeleporterExit, link_id=None)
@ForwardFragmentAttrs(TeleporterExitCheckpointFragment, trigger_checkpoint=None)
class SubTeleporter(SubObject):
    pass


@SUBOBJ_PROBER.for_type('WinLogic')
@ForwardFragmentAttrs(RaceEndLogicFragment, delay_before_broadcast=None)
class WinLogic(SubObject):
    pass


@PROBER.for_type('WorldText')
@ForwardFragmentAttrs(TextMeshFragment, text=None, is_skip=False)
class WorldText(LevelObject):
    pass


@PROBER.for_type('InfoDisplayBox')
@ForwardFragmentAttrs(BaseInfoDisplayLogic,
    fadeout_time = None,
    texts = (),
    per_char_speed = None,
    destroy_on_trigger_exit = None,
    random_char_count = None,
)
class InfoDisplayBox(LevelObject):
    pass


@PROBER.for_type('CarScreenTextDecodeTrigger')
@ForwardFragmentAttrs(BaseCarScreenTextDecodeTrigger,
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
)
class CarScreenTextDecodeTrigger(LevelObject):
    pass


@PROBER.for_type('GravityTrigger')
@ForwardFragmentAttrs(SphereColliderFragment,
    trigger_center = None,
    trigger_radius = None,
)
@ForwardFragmentAttrs(GravityToggleFragment,
    disable_gravity = None,
    drag_scale = None,
    drag_scale_angular = None,
)
@ForwardFragmentAttrs(MusicTriggerFragment,
    music_id = None,
    one_time_trigger = None,
    reset_before_trigger = None,
    disable_music_trigger = None,
)
class GravityTrigger(LevelObject):
    pass


@PROBER.for_type('ForceZoneBox')
@ForwardFragmentAttrs(CustomNameFragment, **CustomNameFragment.value_attrs)
@ForwardFragmentAttrs(ForceZoneFragment, **ForceZoneFragment.value_attrs)
class ForceZoneBox(LevelObject):
    pass


@PROBER.for_type('EnableAbilitiesBox')
@ForwardFragmentAttrs(EnableAbilitiesTriggerFragment, abilities=None, bloom_out=None)
class EnableAbilitiesBox(LevelObject):
    pass


@PROBER.for_type('WedgeGS')
@ForwardFragmentAttrs(GoldenSimplesFragment, **GoldenSimplesFragment.value_attrs)
@ForwardMaterialColors(
    mat_color = ('SimplesMaterial', '_Color', (.3, .3, .3, 1)),
    mat_emit = ('SimplesMaterial', '_EmitColor', (.8, .8, .8, .5)),
    mat_reflect = ('SimplesMaterial', '_ReflectColor', (.3, .3, .3, .9)),
    mat_spec = ('SimplesMaterial', '_SpecColor', (1, 1, 1, 1)),
)
class WedgeGS(LevelObject):

    type = 'WedgeGS'
    has_children = True

    default_sections = (
        *LevelObject.default_sections,
        Section(MAGIC_3, 3, 2),
        Section(MAGIC_2, 0x83, 3),
    )

    def _init_defaults(self):
        super()._init_defaults()
        ForwardMaterialColors.reset_colors(self)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
