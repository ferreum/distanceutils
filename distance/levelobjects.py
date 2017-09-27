"""Level objects."""


import math

from .bytes import (
    BytesModel, Section,
    S_FLOAT, S_FLOAT3, S_FLOAT4, SKIP_BYTES,
    MAGIC_1, MAGIC_2, MAGIC_3, MAGIC_6
)
from .base import BaseObject, Fragment
from .constants import ForceType
from .prober import BytesProber
from .printing import need_counters
from .data import NamedPropertyList, MaterialSet


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

FRAG_PROBER = BytesProber(baseclass=Fragment)


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
class Group(LevelObject):

    child_prober = PROBER
    is_object_group = True
    has_children = True
    type = 'Group'

    custom_name = None

    default_sections = (
        *LevelObject.default_sections,
        Section(MAGIC_2, 0x1d, version=1),
        Section(MAGIC_2, 0x63, version=0)
    )

    def _handle_opts(self, opts):
        LevelObject._handle_opts(self, opts)
        try:
            self.child_prober = opts['level_obj_prober']
        except KeyError:
            pass

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_2, 0x1d): # Group / inspect Children
            return False
        elif sec.match(MAGIC_2, 0x63): # Group name
            if sec.data_size > 12:
                self.custom_name = dbytes.read_str()
            return True
        return LevelObject._read_section_data(self, dbytes, sec)

    def _write_sections(self, dbytes):
        LevelObject._write_sections(self, dbytes)

    def _write_section_data(self, dbytes, sec):
        if sec.match(MAGIC_2, 0x1d, version=1):
            dbytes.write_int(4, MAGIC_1)
            dbytes.write_int(4, 0) # num values
            dbytes.write_int(4, 0) # inspect Children: None
            return True
        elif sec.match(MAGIC_2, 0x63, version=0):
            if self.custom_name is not None:
                dbytes.write_str(self.custom_name)
            return True
        return LevelObject._write_section_data(self, dbytes, sec)

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

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        if self.custom_name is not None:
            p(f"Custom name: {self.custom_name!r}")

    def recenter(self, center):
        pos, rot, scale = self.transform or ((0, 0, 0), (), ())
        self.transform = center, rot, scale
        diff = tuple(c - o for c, o in zip(pos, center))
        for obj in self.children:
            pos, rot, scale = obj.transform or ((0, 0, 0), (), ())
            pos = tuple(o + d for o, d in zip(pos, diff))
            obj.transform = pos, rot, scale


@SUBOBJ_PROBER.for_type('Teleporter')
class SubTeleporter(SubObject):

    destination = None
    link_id = None
    trigger_checkpoint = None

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_2, 0x3e):
            value = dbytes.read_int(4)
            self.destination = value
            return False
        elif sec.match(MAGIC_2, 0x3f):
            value = dbytes.read_int(4)
            self.link_id = value
            return False
        elif sec.match(MAGIC_2, 0x51):
            if sec.data_size > 12:
                check = dbytes.read_byte()
            else:
                # if section is too short, the checkpoint is enabled
                check = 1
            self.trigger_checkpoint = check
            return False
        return SubObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        if self.destination is not None:
            p(f"Teleports to: {self.destination}")
        if self.link_id is not None:
            p(f"Link ID: {self.link_id}")
        if self.trigger_checkpoint is not None:
            p(f"Trigger checkpoint: {self.trigger_checkpoint and 'yes' or 'no'}")


@SUBOBJ_PROBER.for_type('WinLogic')
class WinLogic(SubObject):

    delay_before_broadcast = None

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_2, 0x5d):
            if sec.data_size >= 16:
                for propname, is_skip in iter_named_properties(
                        dbytes, sec.data_end):
                    if propname == "DelayBeforeBroadcast":
                        value = 0.0
                        if not is_skip:
                            value = dbytes.read_struct(S_FLOAT)[0]
                        self.delay_before_broadcast = value
                    else:
                        raise ValueError(f"unknown property: {propname!r}")
            return False
        return SubObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        if self.delay_before_broadcast is not None:
            p(f"Delay before broadcast: {self.delay_before_broadcast}")


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
class CarScreenTextDecodeTrigger(LevelObject):

    text = None
    per_char_speed = None
    clear_on_finish = None
    clear_on_trigger_exit = None
    destroy_on_trigger_exit = None
    time_text = None
    static_time_text = None
    delay = None
    announcer_action = None
    announcer_phrases = ()

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_2, 0x57):
            if sec.version == 0:
                for propname, is_skip in iter_named_properties(
                        dbytes, sec.data_end):
                    if is_skip:
                        continue
                    if propname == 'Text':
                        self.text = dbytes.read_str()
                    elif propname == 'PerCharSpeed':
                        self.per_char_speed = dbytes.read_struct(S_FLOAT)[0]
                    elif propname == 'ClearOnFinish':
                        self.clear_on_finish = dbytes.read_byte()
                    elif propname == 'ClearOnTriggerExit':
                        self.clear_on_trigger_exit = dbytes.read_byte()
                    elif propname == 'DestroyOnTriggerExit':
                        self.destroy_on_trigger_exit = dbytes.read_byte()
                    elif propname == 'TimeText':
                        self.time_text = dbytes.read_str()
                    elif propname == 'StaticTimeText':
                        self.static_time_text = dbytes.read_byte()
                    elif propname == 'Delay':
                        self.delay = dbytes.read_struct(S_FLOAT)[0]
                    elif propname == 'AnnouncerAction':
                        self.announcer_action = dbytes.read_int(4)
                    elif propname == 'AnnouncerPhrases':
                        self._require_equal(MAGIC_1, 4)
                        num_phrases = dbytes.read_int(4)
                        self.announcer_phrases = phrases = []
                        for _ in range(num_phrases):
                            phrases.append(dbytes.read_str())
                    else:
                        raise ValueError(f"unknown property: {propname!r}")
            else:
                try:
                    self.text = dbytes.read_str()
                    self.per_char_speed = dbytes.read_struct(S_FLOAT)[0]
                    self.clear_on_finish = dbytes.read_byte()
                    self.clear_on_trigger_exit = dbytes.read_byte()
                    self.destroy_on_trigger_exit = dbytes.read_byte()
                    self.time_text = dbytes.read_str()
                    self.static_time_text = dbytes.read_byte()
                    self.delay = dbytes.read_struct(S_FLOAT)[0]
                    self.announcer_action = dbytes.read_int(4)
                except EOFError:
                    pass
            return False
        return LevelObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        if self.text is not None:
            p(f"Text: {self.text!r}")
        if self.per_char_speed is not None:
            p(f"Per char speed: {self.per_char_speed}")
        if self.clear_on_finish is not None:
            p(f"Clear on finish: {self.clear_on_finish and 'yes' or 'no'}")
        if self.clear_on_trigger_exit is not None:
            p(f"Clear on trigger exit: {self.clear_on_trigger_exit and 'yes' or 'no'}")
        if self.destroy_on_trigger_exit is not None:
            p(f"Destroy on trigger exit: {self.destroy_on_trigger_exit and 'yes' or 'no'}")
        if self.time_text:
            p(f"Time text: {self.time_text!r}")
        if self.static_time_text is not None:
            p(f"Static time text: {self.static_time_text and 'yes' or 'no'}")
        if self.delay is not None:
            p(f"Delay: {self.delay}")
        if self.announcer_action is not None:
            p(f"Announcer action: {self.announcer_action}")
        if self.announcer_phrases:
            p(f"Announcer phrases: {len(self.announcer_phrases)}")
            with p.tree_children():
                for phrase in self.announcer_phrases:
                    p.tree_next_child()
                    p(f"Phrase: {phrase!r}")


@PROBER.for_type('GravityTrigger')
class GravityTrigger(LevelObject):

    trigger_center = (0.0, 0.0, 0.0)
    trigger_radius = 50.0
    disable_gravity = None
    drag_scale = None
    drag_scale_angular = None
    trigger_center = ()
    trigger_radius = None
    music_id = None
    one_time_trigger = None
    reset_before_trigger = None
    disable_music_trigger = None

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_3, 0x0e):
            # SphereCollider
            self.trigger_center = (0.0, 0.0, 0.0)
            self.trigger_radius = 50.0
            with dbytes.limit(sec.data_end, True):
                self.trigger_center = read_n_floats(dbytes, 3, (0.0, 0.0, 0.0))
                self.trigger_radius = dbytes.read_struct(S_FLOAT)[0]
            return False
        elif sec.match(MAGIC_2, 0x45):
            # GravityTrigger
            self.disable_gravity = 1
            self.drag_scale = 1.0
            self.drag_scale_angular = 1.0
            with dbytes.limit(sec.data_end, True):
                self.disable_gravity = dbytes.read_byte()
                self.drag_scale = dbytes.read_struct(S_FLOAT)[0]
                self.drag_scale_angular = dbytes.read_struct(S_FLOAT)[0]
            return False
        elif sec.match(MAGIC_2, 0x4b):
            # MusicTrigger
            self.music_id = 19
            self.one_time_trigger = 1
            self.reset_before_trigger = 0
            self.disable_music_trigger = 0
            with dbytes.limit(sec.data_end, True):
                self.music_id = dbytes.read_int(4)
                self.one_time_trigger = dbytes.read_byte()
                self.reset_before_trigger = dbytes.read_byte()
                self.disable_music_trigger = dbytes.read_byte()
            return False
        return LevelObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        if self.disable_gravity is not None:
            p(f"Disable gravity: {self.disable_gravity and 'yes' or 'no'}")
        if self.drag_scale is not None:
            p(f"Drag scale: {self.drag_scale}")
        if self.drag_scale_angular is not None:
            p(f"Angular drag scale: {self.drag_scale_angular}")
        if self.music_id is not None:
            p(f"Music ID: {self.music_id}")
        if self.one_time_trigger is not None:
            p(f"One time trigger: {self.one_time_trigger and 'yes' or 'no'}")
        if self.reset_before_trigger is not None:
            p(f"Reset before trigger: {self.reset_before_trigger and 'yes' or 'no'}")
        if self.disable_music_trigger is not None:
            p(f"Disable music trigger: {self.disable_music_trigger and 'yes' or 'no'}")


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
class EnableAbilitiesBox(LevelObject):

    abilities = {}
    KNOWN_ABILITIES = {'EnableFlying', 'EnableJumping',
                       'EnableBoosting', 'EnableJetRotating'}
    bloom_out = 1

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_3, 0x0f):
            # BoxCollider
            return False
        elif sec.match(MAGIC_2, 0x5e):
            # Abilities
            if sec.data_size > 16:
                self.abilities = abilities = {}
                for propname, is_skip in iter_named_properties(
                        dbytes, sec.data_end):
                    if propname in self.KNOWN_ABILITIES:
                        value = 0
                        if not is_skip:
                            value = dbytes.read_int(1)
                        abilities[propname] = value
                    elif propname == 'BloomOut':
                        value = 1
                        if not is_skip:
                            value = dbytes.read_int(1)
                        self.bloom_out = value
                    else:
                        raise ValueError(f"unknown property: {propname!r}")
            return False
        return LevelObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        ab_str = ', '.join(k for k, v in self.abilities.items() if v)
        if not ab_str:
            ab_str = "None"
        p(f"Abilities: {ab_str}")
        if self.bloom_out is not None:
            p(f"Bloom out: {self.bloom_out}")


@PROBER.for_type("WedgeGS")
class WedgeGS(LevelObject):

    type = "WedgeGS"
    has_children = True

    default_sections = (
        *LevelObject.default_sections,
        Section(MAGIC_3, 3, 2),
        Section(MAGIC_2, 0x83, 3),
    )

    mat_color = (.3, .3, .3, 1)
    mat_emit = (.8, .8, .8, .5)
    mat_reflect = (.3, .3, .3, .9)
    mat_spec = (1, 1, 1, 1)

    tex_scale = (1, 1, 1)
    tex_offset = (0, 0, 0)
    image_index = 17
    emit_index = 17
    flip_tex_uv = 0
    world_mapped = 0
    disable_diffuse = 0
    disable_bump = 0
    bump_strength = 0
    disable_reflect = 0
    disable_collision = 0
    additive_transp = 0
    multip_transp = 0
    invert_emit = 0

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_3, 3): # Material
            self._require_equal(MAGIC_1, 4)
            num_entries = dbytes.read_int(4)
            for _ in range(num_entries):
                entry_name = dbytes.read_str()
                if entry_name == 'SimplesMaterial':
                    self._require_equal(MAGIC_1, 4)
                    num_values = dbytes.read_int(4)
                    for _ in range(num_values):
                        name = dbytes.read_str()
                        value = dbytes.read_struct(S_FLOAT4)
                        if name == '_Color':
                            self.mat_color = value
                        elif name == '_EmitColor':
                            self.mat_emit = value
                        elif name == '_ReflectColor':
                            self.mat_reflect = value
                        elif name == '_SpecColor':
                            self.mat_spec = value
                        else:
                            return False # unknown name
                else:
                    return False # unknown entry
            return True
        elif sec.match(MAGIC_2, 0x83): # GoldenSimples
            self.image_index = dbytes.read_int(4)
            self.emit_index = dbytes.read_int(4)
            dbytes.read_int(4) # preset
            self.tex_scale = dbytes.read_struct(S_FLOAT3)
            self.tex_offset = dbytes.read_struct(S_FLOAT3)
            self.flip_tex_uv = dbytes.read_int(1)
            self.world_mapped = dbytes.read_int(1)
            self.disable_diffuse = dbytes.read_int(1)
            self.disable_bump = dbytes.read_int(1)
            self.bump_strength = dbytes.read_struct(S_FLOAT)[0]
            self.disable_reflect = dbytes.read_int(1)
            self.disable_collision = dbytes.read_int(1)
            self.additive_transp = dbytes.read_int(1)
            self.multip_transp = dbytes.read_int(1)
            self.invert_emit = dbytes.read_int(1)
            return True
        return LevelObject._read_section_data(self, dbytes, sec)

    def _write_section_data(self, dbytes, sec):
        if sec.match(MAGIC_3, ident=3, version=2):
            dbytes.write_int(4, MAGIC_1)
            dbytes.write_int(4, 1) # num values?
            dbytes.write_str('SimplesMaterial')
            dbytes.write_int(4, MAGIC_1)
            dbytes.write_int(4, 4) # num values?
            dbytes.write_str('_Color')
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_color))
            dbytes.write_str('_EmitColor')
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_emit))
            dbytes.write_str('_ReflectColor')
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_reflect))
            dbytes.write_str('_SpecColor')
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_spec))
            return True

        elif sec.match(MAGIC_2, ident=0x83, version=3):
            dbytes.write_int(4, self.image_index)
            dbytes.write_int(4, self.emit_index)
            dbytes.write_int(4, 0) # preset
            dbytes.write_bytes(S_FLOAT3.pack(*self.tex_scale))
            dbytes.write_bytes(S_FLOAT3.pack(*self.tex_offset))
            dbytes.write_int(1, self.flip_tex_uv and 1 or 0)
            dbytes.write_int(1, self.world_mapped and 1 or 0)
            dbytes.write_int(1, self.disable_diffuse and 1 or 0)
            dbytes.write_int(1, self.disable_bump and 1 or 0)
            dbytes.write_bytes(S_FLOAT.pack(self.bump_strength))
            dbytes.write_int(1, self.disable_reflect)
            dbytes.write_int(1, self.disable_collision)
            dbytes.write_int(1, self.additive_transp)
            dbytes.write_int(1, self.multip_transp)
            dbytes.write_int(1, self.invert_emit)
            return True

        return LevelObject._write_section_data(self, dbytes, sec)


@FRAG_PROBER.fragment(MAGIC_2, 0x16, 2)
class TrackNodeFragment(Fragment):

    default_section = Section(MAGIC_2, 0x16, 2)

    parent_id = 0
    snap_id = 0
    conn_id = 0
    primary = 0

    def _read_section_data(self, dbytes, sec):
        self.parent_id = dbytes.read_int(4)
        self.snap_id = dbytes.read_int(4)
        self.conn_id = dbytes.read_int(4)
        self.primary = dbytes.read_byte()
        return True

    def _write_section_data(self, dbytes, sec):
        dbytes.write_int(4, self.parent_id)
        dbytes.write_int(4, self.snap_id)
        dbytes.write_int(4, self.conn_id)
        dbytes.write_int(1, self.primary)
        return True

    def _print_type(self, p):
        p(f"Fragment: TrackNode")

    def _print_data(self, p):
        if 'sections' in p.flags or 'track' in p.flags:
            p(f"Parent ID: {self.parent_id}")
            p(f"Snapped to: {self.snap_id}")
            p(f"Connection ID: {self.conn_id}")
            p(f"Primary: {self.primary and 'yes' or 'no'}")


@FRAG_PROBER.fragment(MAGIC_3, 0x3, 1)
@FRAG_PROBER.fragment(MAGIC_3, 0x3, 2)
class MaterialFragment(Fragment):

    def __init__(self, *args, **kw):
        self.materials = MaterialSet()
        Fragment.__init__(self, *args, **kw)

    def _read_section_data(self, dbytes, sec):
        if sec.data_size >= 16:
            self.materials.read(dbytes)
        return True

    def _write_section_data(self, dbytes, sec):
        if self.materials:
            self.materials.write(dbytes)
        return True

    def _print_type(self, p):
        p(f"Fragment: Material")

    def _print_data(self, p):
        if 'allprops' in p.flags and self.materials:
            self.materials.print_data(p)


class NamedPropertiesFragment(Fragment):

    _frag_name = "NamedProperties"

    def __init__(self, *args, **kw):
        self.props = NamedPropertyList()
        Fragment.__init__(self, *args, **kw)

    def _read_section_data(self, dbytes, sec):
        if sec.data_size >= 16:
            self.props.read(dbytes)
        return True

    def _write_section_data(self, dbytes, sec):
        if self.props:
            self.props.write(dbytes)
        return True

    def _print_type(self, p):
        p(f"Fragment: {self._frag_name}")

    def _print_data(self, p):
        if 'allprops' in p.flags and self.props:
            self.props.print_data(p)


PROPERTY_FRAGS = (
    (Section(MAGIC_2, 0x25, 0), "PopupBlockerLogic"),
    (Section(MAGIC_2, 0x42, 0), "ObjectSpawnCircle"),
    (Section(MAGIC_2, 0x39, 0), "ParticleEmitLogic"),
    (Section(MAGIC_2, 0x26, 0), "Light"),
    (Section(MAGIC_2, 0x27, 0), "PulseMaterial"),
    (Section(MAGIC_2, 0x28, 0), "SmoothRandomPosition"),
    (Section(MAGIC_2, 0x43, 0), "InterpolateToPositionOnTrigger"),
    (Section(MAGIC_2, 0x5e, 0), "EnableAbilitiesTrigger"),
    (Section(MAGIC_2, 0x45, 0), "GravityToggle"),
    (Section(MAGIC_2, 0x24, 0), "OldFlyingRingLogic"),
    (Section(MAGIC_2, 0x50, 0), "Pulse"),
)


def _create_property_fragment_classes():
    globs = globals()
    for sec, name in PROPERTY_FRAGS:
        typename = name + "Fragment"
        if typename in globs:
            raise ValueError(f"Class {typename} already exists")
        cls = type(typename, (NamedPropertiesFragment,), {
            '_frag_name': name,
        })
        globs[typename] = cls


def add_property_fragments_to_prober(prober):
    globs = globals()
    for sec, name in PROPERTY_FRAGS:
        typename = name + "Fragment"
        cls = globs[typename]
        prober.add_fragment(cls, sec)


_create_property_fragment_classes()
add_property_fragments_to_prober(FRAG_PROBER)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
