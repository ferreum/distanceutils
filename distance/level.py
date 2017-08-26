#!/usr/bin/python
# File:        level.py
# Description: level
# Created:     2017-06-28


from struct import Struct
import math
from contextlib import contextmanager

from .bytes import (BytesModel, Section, S_FLOAT,
                    SECTION_LEVEL, SECTION_LAYER, SECTION_TYPE,
                    SECTION_UNK_2, SECTION_UNK_3, SECTION_UNK_5,
                    SECTION_LEVEL_INFO, SECTION_UNK_1)
from .constants import Difficulty, Mode, AbilityToggle, ForceType
from .common import format_duration
from .detect import BytesProber


S_ABILITIES = Struct("5b")
FLOAT_SKIP_BYTES = b'\xFD\xFF\xFF\x7F'

S_FLOAT3 = Struct("fff")
S_FLOAT4 = Struct("ffff")


PROBER = BytesProber()

SUBOBJ_PROBER = BytesProber()


@PROBER.func
def _fallback_object(section):
    if section.ident == SECTION_TYPE:
        return LevelObject
    return None


@SUBOBJ_PROBER.func
def _fallback_subobject(section):
    if section.ident == SECTION_TYPE:
        return LevelObject
    return None


def parse_n_floats(dbytes, n, default):
    def read_float():
        return dbytes.read_struct(S_FLOAT)[0]
    f = read_float()
    if math.isnan(f):
        return default
    else:
        return (f, *(read_float() for _ in range(n - 1)))


TRANSFORM_MIN_SIZE = 12


def parse_transform(dbytes):
    def read_float():
        return dbytes.read_struct(S_FLOAT)[0]
    f = dbytes.read_n(4)
    if f == FLOAT_SKIP_BYTES:
        pos = (0.0, 0.0, 0.0)
    else:
        pos = (S_FLOAT.unpack(f)[0], read_float(), read_float())
    f = dbytes.read_n(4)
    if f == FLOAT_SKIP_BYTES:
        rot = (0.0, 0.0, 0.0, 1.0)
    else:
        rot = (S_FLOAT.unpack(f)[0], read_float(), read_float(), read_float())
    f = dbytes.read_n(4)
    if f == FLOAT_SKIP_BYTES:
        scale = (1.0, 1.0, 1.0)
    else:
        scale = (S_FLOAT.unpack(f)[0], read_float(), read_float())
    return pos, rot, scale


def write_transform(dbytes, trans):
    if trans is None:
        trans = ()
    if len(trans) > 0 and len(trans[0]):
        pos = trans[0]
        dbytes.write_bytes(S_FLOAT3.pack(*pos))
    else:
        dbytes.write_bytes(FLOAT_SKIP_BYTES)
    if len(trans) > 1 and len(trans[1]):
        rot = trans[1]
        dbytes.write_bytes(S_FLOAT4.pack(*rot))
    else:
        dbytes.write_bytes(FLOAT_SKIP_BYTES)
    if len(trans) > 2 and len(trans[2]):
        scale = trans[2]
        dbytes.write_bytes(S_FLOAT3.pack(*scale))
    else:
        dbytes.write_bytes(FLOAT_SKIP_BYTES)


class Counters(object):

    num_objects = 0
    num_layers = 0
    layer_objects = 0
    grouped_objects = 0

    def print_data(self, p):
        if 'nolayers' not in p.flags:
            p(f"Total layers: {self.num_layers}")
            p(f"Total objects in layers: {self.layer_objects}")
        if self.grouped_objects:
            p(f"Total objects in groups: {self.grouped_objects}")
        if self.num_objects != self.layer_objects:
            p(f"Total objects: {self.num_objects}")


@contextmanager
def need_counters(p):
    try:
        p.counters
    except AttributeError:
        pass
    else:
        yield None
        return
    c = Counters()
    p.counters = c
    yield c
    del p.counters


def _print_objects(p, gen):
    counters = p.counters
    for obj in gen:
        p.tree_next_child()
        counters.num_objects += 1
        if 'numbers' in p.flags:
            p(f"Level object: {counters.num_objects}")
        p.print_data_of(obj)


class LevelObject(BytesModel):

    subobject_prober = SUBOBJ_PROBER
    is_object_group = False

    version = None
    transform = ((0, 0, 0), (0, 0, 0, 1), (1, 1, 1))
    subobjects = ()
    has_subobjects = False
    subobjects_section = None

    def parse(self, dbytes):
        ts = self.get_start_section()
        self.type = ts.type
        self.report_end_pos(ts.data_start + ts.size)
        with dbytes.limit(ts.data_end):
            while dbytes.pos < ts.data_end:
                sec = Section(dbytes)
                with dbytes.limit(sec.data_end):
                    self._read_section_data(dbytes, sec)
                dbytes.pos = sec.data_end

    def _read_section_data(self, dbytes, sec):
        if sec.ident == SECTION_UNK_3:
            if sec.value_id == 0x01: # base object props
                end = sec.data_end
                if dbytes.pos + TRANSFORM_MIN_SIZE < end:
                    self.transform = parse_transform(dbytes)
                if dbytes.pos + Section.MIN_SIZE < end:
                    self.subobjects_section = s5 = Section(dbytes)
                    if s5.num_objects:
                        self.subobjects = subobjects = []
                        gen = self.subobject_prober.iter_maybe_partial(
                            dbytes, max_pos=s5.data_end)
                        for obj, sane, exc in gen:
                            subobjects.append(obj)
                            if not sane:
                                break
                return True

    def write(self, dbytes):
        dbytes.write_num(4, SECTION_TYPE)
        size_pos = dbytes.pos
        with dbytes.write_size():
            dbytes.write_str(self.type)
            dbytes.write_bytes(b'\x00') # unknown
            dbytes.write_secnum()
            dbytes.write_num(4, self.version or 0)

            dbytes.write_num(4, SECTION_UNK_3)
            with dbytes.write_size():
                dbytes.write_num(4, 1) # type
                dbytes.write_bytes(b'\x00' * 4) # unknown
                dbytes.write_secnum()
                write_transform(dbytes, self.transform)
                if (self.has_subobjects or self.subobjects
                        or self.get_section(SECTION_UNK_5)):
                    dbytes.write_num(4, SECTION_UNK_5)
                    with dbytes.write_size():
                        dbytes.write_num(4, len(self.subobjects))
                        for obj in self.subobjects:
                            obj.write(dbytes)

            self._write_sub(dbytes)

    def _write_sub(self, dbytes):
        pass

    def iter_subobjects(self, ty=None, name=None):
        for obj in self.subobjects:
            if ty is None or isinstance(obj, ty):
                if name is None or obj.type == name:
                    yield obj

    def _print_data(self, p):
        p(f"Object type: {self.type!r}")
        if 'transform' in p.flags:
            p(f"Transform: {self.transform}")
        self._print_pre_data(p)
        if self.subobjects:
            self._print_subobjects(p)

    def _print_subobjects(self, p):
        num = len(self.subobjects)
        p(f"Subobjects: {num}")
        with p.tree_children(num):
            for obj in self.subobjects:
                p.tree_next_child()
                p.print_data_of(obj)

    def _print_pre_data(self, p):
        pass


@PROBER.for_type('LevelSettings')
class LevelSettings(LevelObject):

    type = None
    version = None
    name = None
    skybox_name = None
    modes = ()
    medal_times = ()
    medal_scores = ()
    abilities = ()
    difficulty = None

    def parse(self, dbytes):
        next_section = dbytes.read_fixed_number(4)
        dbytes.pos -= 4
        sec = self.get_start_section()
        if sec.ident == SECTION_LEVEL_INFO:
            # Levelinfo section only found in old (v1) maps
            self.type = 'Section 88888888'
            self.report_end_pos(sec.data_start + sec.size)
            self.add_unknown(4)
            self.skybox_name = dbytes.read_string()
            self.add_unknown(143)
            self.name = dbytes.read_string()
            return
        LevelObject.parse(self, dbytes)

    def _read_section_data(self, dbytes, sec):
        if LevelObject._read_section_data(self, dbytes, sec):
            return True
        if sec.ident == SECTION_UNK_2:
            if sec.value_id == 0x52:
                self.levelinfo_section = sec
                self.version = version = sec.version

                self.add_unknown(12)
                self.name = dbytes.read_string()
                self.add_unknown(4)
                self.modes = modes = {}
                num_modes = dbytes.read_fixed_number(4)
                for i in range(num_modes):
                    mode = dbytes.read_fixed_number(4)
                    modes[mode] = dbytes.read_byte()
                self.music_id = dbytes.read_fixed_number(4)
                if version <= 3:
                    self.skybox_name = dbytes.read_string()
                    self.add_unknown(57)
                elif version == 4:
                    self.add_unknown(141)
                elif version == 5:
                    self.add_unknown(172) # confirmed only for v5
                elif 6 <= version:
                    # confirmed only for v6..v9
                    self.add_unknown(176)
                self.medal_times = times = []
                self.medal_scores = scores = []
                for i in range(4):
                    times.append(dbytes.read_struct(S_FLOAT)[0])
                    scores.append(dbytes.read_fixed_number(4, signed=True))
                if version >= 1:
                    self.abilities = dbytes.read_struct(S_ABILITIES)
                if version >= 2:
                    self.difficulty = dbytes.read_fixed_number(4)

    def _print_data(self, p):
        p(f"Object type: {self.type!r}")
        if self.version is not None:
            p(f"Object version: {self.version!r}")
        if self.name is not None:
            p(f"Level name: {self.name!r}")
        if self.skybox_name is not None:
            p(f"Skybox name: {self.skybox_name!r}")
        if self.medal_times:
            medal_str = ', '.join(format_duration(t) for t in self.medal_times)
            p(f"Medal times: {medal_str}")
        if self.medal_scores:
            medal_str = ', '.join(str(s) for s in self.medal_scores)
            p(f"Medal scores: {medal_str}")
        if self.modes:
            modes_str = ', '.join(Mode.to_name(mode)
                                  for mode, value in sorted(self.modes.items())
                                  if value)
            p(f"Level modes: {modes_str}")
        if self.abilities:
            ab_str = ', '.join(AbilityToggle.to_name_for_value(toggle, value)
                               for toggle, value in enumerate(self.abilities)
                               if value != 0)
            if not ab_str:
                ab_str = "All"
            p(f"Abilities: {ab_str}")
        if self.difficulty is not None:
            p(f"Difficulty: {Difficulty.to_name(self.difficulty)}")


@PROBER.for_type('Group')
class Group(LevelObject):

    subobject_prober = PROBER
    is_object_group = True
    has_subobjects = True
    version = 3
    type = 'Group'

    group_name = None

    def _read_section_data(self, dbytes, sec):
        if LevelObject._read_section_data(self, dbytes, sec):
            return True
        if sec.ident == SECTION_UNK_2:
            if sec.value_id == 0x1d: # Group / inspect Children
                return True
            elif sec.value_id == 0x63: # Group name
                if sec.size > 12:
                    dbytes.pos += 4 # secnum
                    self.group_name = dbytes.read_string()
                return True

    def _write_sub(self, dbytes):
        dbytes.write_num(4, SECTION_UNK_2)
        with dbytes.write_size():
            dbytes.write_num(4, 0x1d) # value id
            dbytes.write_num(4, 1) # version
            dbytes.write_secnum()
            dbytes.write_num(4, SECTION_UNK_1)
            dbytes.write_num(4, 0) # num values
            dbytes.write_num(4, 0) # inspect Children: None
        dbytes.write_num(4, SECTION_UNK_2)
        with dbytes.write_size():
            dbytes.write_num(4, 0x63) # value id
            dbytes.write_num(4, 0) # version
            dbytes.write_secnum()
            if self.group_name is not None:
                dbytes.write_str(self.group_name)

    def _print_subobjects(self, p):
        with need_counters(p) as counters:
            num = len(self.subobjects)
            p(f"Grouped objects: {num}")
            if 'groups' in p.flags:
                p.counters.grouped_objects += num
                with p.tree_children(num):
                    _print_objects(p, self.subobjects)
            if counters:
                counters.print_data(p)

    def _print_pre_data(self, p):
        LevelObject._print_pre_data(self, p)
        if self.group_name is not None:
            p(f"Custom name: {self.group_name!r}")

    def recenter(self, center):
        pos, rot, scale = self.transform
        self.transform = center, rot, scale
        diff = tuple(c - o for c, o in zip(pos, center))
        for obj in self.subobjects:
            pos, rot, scale = obj.transform
            pos = tuple(o + d for o, d in zip(pos, diff))
            obj.transform = pos, rot, scale


@SUBOBJ_PROBER.for_type('Teleporter')
class SubTeleporter(LevelObject):

    destination = None
    link_id = None
    trigger_checkpoint = None

    def _read_section_data(self, dbytes, sec):
        if LevelObject._read_section_data(self, dbytes, sec):
            return True
        if sec.ident == SECTION_UNK_2:
            if sec.value_id == 0x3E:
                dbytes.pos = sec.data_start + 12
                value = dbytes.read_fixed_number(4)
                self.destination = value
                return True
            elif sec.value_id == 0x3F:
                dbytes.pos = sec.data_start + 12
                value = dbytes.read_fixed_number(4)
                self.link_id = value
                return True
            elif sec.value_id == 0x51:
                if sec.size > 12:
                    dbytes.pos = sec.data_start + 12
                    check = dbytes.read_byte()
                else:
                    # if section is too short, the checkpoint is enabled
                    check = 1
                self.trigger_checkpoint = check
                return True

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        if self.destination is not None:
            p(f"Teleports to: {self.destination}")
        if self.link_id is not None:
            p(f"Link ID: {self.link_id}")
        if self.trigger_checkpoint is not None:
            p(f"Trigger checkpoint: {self.trigger_checkpoint and 'yes' or 'no'}")


@PROBER.for_type('WorldText')
class WorldText(LevelObject):

    text = None

    def _read_section_data(self, dbytes, sec):
        if LevelObject._read_section_data(self, dbytes, sec):
            return True
        if sec.ident == SECTION_UNK_3:
            if sec.value_id == 0x07:
                pos = sec.data_start + 12
                if pos < sec.data_end:
                    dbytes.pos = pos
                    self.text = dbytes.read_string()
                    for i in range((sec.data_end - dbytes.pos) // 4):
                        self.add_unknown(value=dbytes.read_struct(S_FLOAT)[0])
                else:
                    self.text = f"Hello World"
                return True

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        if self.text is not None:
            p(f"World text: {self.text!r}")


@PROBER.for_type('InfoDisplayBox')
class InfoDisplayBox(LevelObject):

    version = None
    texts = ()

    def _read_section_data(self, dbytes, sec):
        if LevelObject._read_section_data(self, dbytes, sec):
            return True
        if sec.ident == SECTION_UNK_2:
            if sec.value_id == 0x4A:
                texts = self.texts
                self.version = version = sec.version
                if version == 0:
                    self.add_unknown(4)
                    num_props = dbytes.read_fixed_number(4)
                    self.texts = texts = [None] * 5
                    for i in range(num_props):
                        propname = dbytes.read_string()
                        if propname.startswith("InfoText"):
                            dbytes.pos = value_start = dbytes.pos + 8
                            if not math.isnan(dbytes.read_struct(S_FLOAT)[0]):
                                dbytes.pos = value_start
                                index = int(propname[-1])
                                texts[index] = dbytes.read_string()
                        else:
                            dbytes.pos += 12
                else:
                    # only verified in v2
                    self.add_unknown(4)
                    self.fadeout_time = dbytes.read_struct(S_FLOAT)
                    for i in range(5):
                        self.add_unknown(4) # f32 delay
                        if texts is ():
                            self.texts = texts = []
                        texts.append(dbytes.read_string())
                return True

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        p(f"Version: {self.version}")
        for i, text in enumerate(self.texts):
            if text:
                p(f"Text {i}: {text!r}")


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
        if LevelObject._read_section_data(self, dbytes, sec):
            return True
        if sec.ident == SECTION_UNK_3:
            if sec.value_id == 0x0e:
                # SphereCollider
                self.trigger_center = (0.0, 0.0, 0.0)
                self.trigger_radius = 50.0
                with dbytes.limit(sec.data_end, True):
                    self.trigger_center = parse_n_floats(dbytes, 3, (0.0, 0.0, 0.0))
                    self.trigger_radius = dbytes.read_struct(S_FLOAT)[0]
                return True
        elif sec.ident == SECTION_UNK_2:
            if sec.value_id == 0x45:
                # GravityTrigger
                self.add_unknown(4)
                self.disable_gravity = 1
                self.drag_scale = 1.0
                self.drag_scale_angular = 1.0
                with dbytes.limit(sec.data_end, True):
                    self.disable_gravity = dbytes.read_byte()
                    self.drag_scale = dbytes.read_struct(S_FLOAT)[0]
                    self.drag_scale_angular = dbytes.read_struct(S_FLOAT)[0]
                return True
            elif sec.value_id == 0x4b:
                # MusicTrigger
                self.add_unknown(4)
                self.music_id = 19
                self.one_time_trigger = 1
                self.reset_before_trigger = 0
                self.disable_music_trigger = 0
                with dbytes.limit(sec.data_end, True):
                    self.music_id = dbytes.read_fixed_number(4)
                    self.one_time_trigger = dbytes.read_byte()
                    self.reset_before_trigger = dbytes.read_byte()
                    self.disable_music_trigger = dbytes.read_byte()
                return True

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
        if LevelObject._read_section_data(self, dbytes, sec):
            return True
        if sec.ident == SECTION_UNK_3:
            if sec.value_id == 0x0f:
                # collider
                return True
        elif sec.ident == SECTION_UNK_2:
            if sec.value_id == 0x63:
                # CustomName
                self.add_unknown(4) # 0x36=wind 0x3b=gravity
                if dbytes.pos < sec.data_end:
                    with dbytes.limit(sec.data_end):
                        self.custom_name = dbytes.read_string()
                return True
            elif sec.value_id == 0xa0:
                self.add_unknown(4) # 0x37=wind, 0x3c=gravity
                self.force_direction = (0.0, 0.0, 1.0)
                self.global_force = 0
                self.force_type = ForceType.WIND
                self.gravity_magnitude = 25.0
                self.disable_global_gravity = 0
                self.wind_speed = 300.0
                self.drag_multiplier = 1.0
                with dbytes.limit(sec.data_end, True):
                    self.force_direction = parse_n_floats(dbytes, 3, (0.0, 0.0, 1.0))
                    self.global_force = dbytes.read_byte()
                    self.force_type = dbytes.read_fixed_number(4)
                    self.gravity_magnitude = dbytes.read_struct(S_FLOAT)[0]
                    self.disable_global_gravity = dbytes.read_byte()
                    self.wind_speed = dbytes.read_struct(S_FLOAT)[0]
                    self.drag_multiplier = dbytes.read_struct(S_FLOAT)[0]
                return True

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

    def _read_section_data(self, dbytes, sec):
        if LevelObject._read_section_data(self, dbytes, sec):
            return True
        if sec.ident == SECTION_UNK_3:
            if sec.value_id == 0x0f:
                # BoxCollider
                return True
        elif sec.ident == SECTION_UNK_2:
            if sec.value_id == 0x5e:
                # Abilities
                if sec.size > 16:
                    self.add_unknown(4)
                    self.abilities = abilities = {}
                    num_props = dbytes.read_fixed_number(4)
                    for i in range(num_props):
                        propname = dbytes.read_string()
                        dbytes.pos = value_start = dbytes.pos + 8
                        byte = dbytes.read_byte()
                        if byte not in (0, 1): # probably NaN
                            value = 0
                            dbytes.pos = value_start + 4
                        else:
                            value = byte
                        if propname in self.KNOWN_ABILITIES:
                            abilities[propname] = value
                return True

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        ab_str = ', '.join(k for k, v in self.abilities.items() if v)
        if not ab_str:
            ab_str = "None"
        p(f"Abilities: {ab_str}")


@PROBER.for_type("WedgeGS")
class WedgeGS(LevelObject):

    type = "WedgeGS"
    version = 3
    has_subobjects = True

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
        if LevelObject._read_section_data(self, dbytes, sec):
            return True
        if sec.ident == SECTION_UNK_3:
            if sec.value_id == 3:
                # Material
                return True
        elif sec.ident == SECTION_UNK_2:
            if sec.value_id == 0x83:
                # GoldenSimples
                return True

    def _write_sub(self, dbytes):
        dbytes.write_num(4, SECTION_UNK_3)
        with dbytes.write_size():
            dbytes.write_num(4, 3) # type
            dbytes.write_num(4, 2) # num s1
            dbytes.write_secnum()
            dbytes.write_num(4, SECTION_UNK_1)
            dbytes.write_num(4, 1) # num values?
            dbytes.write_str("SimplesMaterial")
            dbytes.write_num(4, SECTION_UNK_1)
            dbytes.write_num(4, 4) # num values?
            dbytes.write_str("_Color")
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_color))
            dbytes.write_str("_EmitColor")
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_emit))
            dbytes.write_str("_ReflectColor")
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_reflect))
            dbytes.write_str("_SpecColor")
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_spec))

        dbytes.write_num(4, SECTION_UNK_2)
        with dbytes.write_size():
            dbytes.write_num(4, 0x83) # type
            dbytes.write_num(4, 3) # version
            dbytes.write_secnum()
            dbytes.write_num(4, self.image_index)
            dbytes.write_num(4, self.emit_index)
            dbytes.write_num(4, 0) # preset
            dbytes.write_bytes(S_FLOAT3.pack(*self.tex_scale))
            dbytes.write_bytes(S_FLOAT3.pack(*self.tex_offset))
            dbytes.write_num(1, self.flip_tex_uv and 1 or 0)
            dbytes.write_num(1, self.world_mapped and 1 or 0)
            dbytes.write_num(1, self.disable_diffuse and 1 or 0)
            dbytes.write_num(1, self.disable_bump and 1 or 0)
            dbytes.write_bytes(S_FLOAT.pack(self.bump_strength))
            dbytes.write_num(1, self.disable_reflect)
            dbytes.write_num(1, self.disable_collision)
            dbytes.write_num(1, self.additive_transp)
            dbytes.write_num(1, self.multip_transp)
            dbytes.write_num(1, self.invert_emit)


class Level(BytesModel):

    settings = None

    def parse(self, dbytes):
        ls = self.require_section(SECTION_LEVEL, 0)
        if not ls:
            raise IOError("No level section")
        self.level_name = ls.level_name

    def get_settings(self):
        s = self.settings
        if not s:
            s, sane, exc = LevelSettings.maybe_partial(self.dbytes)
            self.settings = s
        return s

    def move_to_first_layer(self):
        settings = self.get_settings()
        if settings.sane_end_pos:
            self.dbytes.pos = settings.reported_end_pos
        else:
            raise settings.exception

    def iter_objects(self, with_layers=False, with_objects=True):
        dbytes = self.dbytes
        self.move_to_first_layer()
        for layer, sane, exc in Section.iter_maybe_partial(dbytes):
            layer_end = layer.size + layer.data_start
            if with_layers:
                yield layer, sane, exc
            if not sane:
                return
            if with_objects:
                for obj, sane, exc in PROBER.iter_maybe_partial(dbytes, max_pos=layer_end):
                    yield obj, True, exc
                    if not sane:
                        break
            dbytes.pos = layer_end

    def iter_layers(self):
        dbytes = self.dbytes
        self.move_to_first_layer()
        for layer, sane, exc in Section.iter_maybe_partial(dbytes):
            layer_end = layer.size + layer.data_start
            yield layer
            if not sane:
                return
            dbytes.pos = layer_end

    def iter_layer_objects(self, layer):
        dbytes = self.dbytes
        dbytes.pos = layer.objects_start
        layer_end = layer.data_end
        for obj, sane, exc in PROBER.iter_maybe_partial(self.dbytes, max_pos=layer_end):
            yield obj
            if not sane:
                break

    def _print_data(self, p):
        p(f"Level name: {self.level_name!r}")
        try:
            settings = self.get_settings()
            p.print_data_of(settings)
            if not settings.sane_end_pos:
                return
            with need_counters(p) as counters:
                for layer in self.iter_layers():
                    p(f"Layer: {p.counters.num_layers}")
                    p.counters.num_layers += 1
                    p.counters.layer_objects += layer.num_objects
                    p.print_data_of(layer)
                    with p.tree_children(layer.num_objects):
                        _print_objects(p, self.iter_layer_objects(layer))
                if counters:
                    counters.print_data(p)
        except Exception as e:
            p.print_exception(e)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
