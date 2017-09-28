"""Level objects."""


import math

from .bytes import (
    Section,
    S_FLOAT, SKIP_BYTES,
    MAGIC_1, MAGIC_2, MAGIC_3, MAGIC_6
)
from .base import BaseObject
from .fragments import (
    PROBER as FRAG_PROBER,
    ForwardFragmentAttrs,
    ForwardFragmentColors,
    GoldenSimplesFragment,
    GroupFragment,
    CustomNameFragment,
    TeleporterEntranceFragment,
    TeleporterExitFragment,
    TeleporterExitCheckpointFragment,
    RaceEndLogicFragment,
    EnableAbilitiesTriggerFragment,
    SphereColliderFragment,
    GravityToggleFragment,
    MusicTriggerFragment,
    BaseCarScreenTextDecodeTriggerFragment,
)
from .constants import ForceType
from .prober import BytesProber
from .printing import need_counters


def read_n_floats(dbytes, n, default):
    def read_float():
        return dbytes.read_struct(S_FLOAT)[0]
    f = read_float()
    if math.isnan(f):
        return default
    else:
        return (f, *(read_float() for _ in range(n - 1)))


def iter_named_properties(dbytes, end):
    num_props = dbytes.read_int(4)
    for i in range(num_props):
        propname = dbytes.read_str()
        dbytes.read_bytes(8) # unknown
        spos = dbytes.pos
        if spos + 4 <= end:
            peek = dbytes.read_bytes(4)
            # this is weird
            if peek == SKIP_BYTES:
                yield propname, True
            else:
                dbytes.pos = spos
                yield propname, False
        else:
            yield propname, False


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
        (TeleporterEntranceFragment, dict(destination=None)),
        (TeleporterExitFragment, dict(link_id=None)),
        (TeleporterExitCheckpointFragment, dict(trigger_checkpoint=None)),
    )


@SUBOBJ_PROBER.for_type('WinLogic')
class WinLogic(ForwardFragmentAttrs, SubObject):

    forward_fragment_attrs = (
        (RaceEndLogicFragment, dict(delay_before_broadcast=None)),
    )


@PROBER.for_type('WorldText')
class WorldText(LevelObject):

    text = None

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_3, 0x07):
            pos = sec.data_start + 12
            if pos < sec.data_end:
                dbytes.pos = pos
                self.text = dbytes.read_str()
                for i in range((sec.data_end - dbytes.pos) // 4):
                    self._add_unknown(value=dbytes.read_struct(S_FLOAT)[0])
            else:
                self.text = f"Hello World"
            return False
        return LevelObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        if self.text is not None:
            p(f"World text: {self.text!r}")


@PROBER.for_type('InfoDisplayBox')
class InfoDisplayBox(LevelObject):

    version = None
    texts = ()
    delays = ()
    per_char_speed = None
    destroy_on_trigger_exit = None
    random_char_count = None

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_2, 0x4A):
            texts = self.texts
            self.version = version = sec.version
            if version == 0:
                self.texts = texts = [None] * 5
                self.delays = delays = [None] * 5
                for propname, is_skip in iter_named_properties(
                        dbytes, sec.data_end):
                    if is_skip:
                        continue
                    if propname.startswith('InfoText'):
                        index = int(propname[-1])
                        texts[index] = dbytes.read_str()
                    elif propname.startswith('Delay'):
                        index = int(propname[-1])
                        delays[index] = dbytes.read_struct(S_FLOAT)[0]
                    elif propname == 'PerCharSpeed':
                        self.per_char_speed = dbytes.read_struct(S_FLOAT)[0]
                    elif propname == 'DestroyOnTriggerExit':
                        self.destroy_on_trigger_exit = dbytes.read_int(1)
                    elif propname == 'RandomCharCount':
                        self.random_char_count = dbytes.read_int(4)
                    else:
                        raise ValueError(f"unknown property: {propname!r}")
            else:
                # only verified in v2
                self.fadeout_time = dbytes.read_struct(S_FLOAT)
                for i in range(5):
                    self._add_unknown(4) # f32 delay
                    if texts is ():
                        self.texts = texts = []
                    texts.append(dbytes.read_str())
            return False
        return LevelObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        p(f"Version: {self.version}")
        for i, text in enumerate(self.texts):
            if text:
                p(f"Text {i}: {text!r}")
        if self.per_char_speed is not None:
            p(f"Per char speed: {self.per_char_speed}")
        if self.destroy_on_trigger_exit is not None:
            p(f"Destroy on trigger exit: {self.destroy_on_trigger_exit and 'yes' or 'no'}")
        if self.random_char_count is not None:
            p(f"Random char count: {self.random_char_count}")


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
class ForceZoneBox(LevelObject):

    custom_name = None
    force_direction = ()
    global_force = None
    force_type = None
    gravity_magnitude = None
    disable_global_gravity = None
    wind_speed = None
    drag_multiplier = None

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_3, 0x0f): # collider
            return False
        elif sec.match(MAGIC_2, 0x63): # CustomName
            if dbytes.pos < sec.data_end:
                with dbytes.limit(sec.data_end):
                    self.custom_name = dbytes.read_str()
            return False
        elif sec.match(MAGIC_2, 0xa0):
            self.force_direction = (0.0, 0.0, 1.0)
            self.global_force = 0
            self.force_type = ForceType.WIND
            self.gravity_magnitude = 25.0
            self.disable_global_gravity = 0
            self.wind_speed = 300.0
            self.drag_multiplier = 1.0
            with dbytes.limit(sec.data_end, True):
                self.force_direction = read_n_floats(dbytes, 3, (0.0, 0.0, 1.0))
                self.global_force = dbytes.read_byte()
                self.force_type = dbytes.read_int(4)
                self.gravity_magnitude = dbytes.read_struct(S_FLOAT)[0]
                self.disable_global_gravity = dbytes.read_byte()
                self.wind_speed = dbytes.read_struct(S_FLOAT)[0]
                self.drag_multiplier = dbytes.read_struct(S_FLOAT)[0]
            return False
        return LevelObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        if self.custom_name:
            p(f"Custom name: {self.custom_name!r}")
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
