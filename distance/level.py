# File:        level.py
# Description: level
# Created:     2017-06-28


from struct import Struct
import math
from contextlib import contextmanager

from .bytes import (BytesModel, Section, S_FLOAT,
                    MAGIC_9, MAGIC_7, MAGIC_6,
                    MAGIC_2, MAGIC_3, MAGIC_5,
                    MAGIC_8, MAGIC_1)
from .constants import (Difficulty, Mode, AbilityToggle, ForceType,
                        LAYER_FLAG_NAMES)
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
    if section.magic == MAGIC_6:
        return LevelObject
    return None


@SUBOBJ_PROBER.func
def _fallback_subobject(section):
    if section.magic == MAGIC_6:
        return SubObject
    return None


def read_n_floats(dbytes, n, default):
    def read_float():
        return dbytes.read_struct(S_FLOAT)[0]
    f = read_float()
    if math.isnan(f):
        return default
    else:
        return (f, *(read_float() for _ in range(n - 1)))


def obj_only(gen):
    for obj, sane, exc in gen:
        yield obj


def format_flags(gen):
    for flag, names in gen:
        name = names.get(flag, f"Unknown({flag})")
        if name:
            yield name


def read_weird_bool(dbytes):
    b = dbytes.read_byte()
    if b == 0xfd:
        # value == FLOAT_SKIP_BYTES
        dbytes.read_n(3)
        return 0
    else:
        return b

TRANSFORM_MIN_SIZE = 12


def read_transform(dbytes):
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


def format_transform(trans):
    def format_floats(floats):
        return ', '.join(format(f, '.3f') for f in floats)
    return ', '.join(f"({format_floats(f)})" for f in trans)


class Counters(object):

    num_objects = 0
    num_layers = 0
    layer_objects = 0
    grouped_objects = 0

    def print_data(self, p):
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

    child_prober = SUBOBJ_PROBER
    is_object_group = False

    transform = ((0, 0, 0), (0, 0, 0, 1), (1, 1, 1))
    _children = None
    has_children = False
    children_section = None

    def _read(self, dbytes):
        ts = self._get_start_section()
        self.type = ts.type
        self._report_end_pos(ts.data_end)
        self._read_sections(ts.data_end)

    def _read_section_data(self, dbytes, sec):
        if sec.magic == MAGIC_3:
            if sec.ident == 0x01: # base object props
                end = sec.data_end
                if dbytes.pos + TRANSFORM_MIN_SIZE < end:
                    self.transform = read_transform(dbytes)
                if dbytes.pos + Section.MIN_SIZE < end:
                    self.children_section = Section(dbytes)
                    self.has_children = True
                return True
        return BytesModel._read_section_data(self, dbytes, sec)

    @property
    def children(self):
        objs = self._children
        if objs is None:
            s5 = self.children_section
            if s5 and s5.num_objects:
                self._children = objs = []
                dbytes = self.dbytes
                old_pos = dbytes.pos
                try:
                    dbytes.pos = s5.children_start
                    gen = self.child_prober.iter_maybe(
                        dbytes, max_pos=s5.data_end)
                    for obj, sane, exc in gen:
                        objs.append(obj)
                        if not sane:
                            break
                finally:
                    dbytes.pos = old_pos
            else:
                self._children = objs = ()
        return objs

    @children.setter
    def children(self, objs):
        self._children = objs

    def write(self, dbytes):
        with dbytes.write_section(MAGIC_6, self.type):
            with dbytes.write_section(MAGIC_3, ident=1, version=0):
                write_transform(dbytes, self.transform)
                if self.has_children or self.children:
                    dbytes.write_int(4, MAGIC_5)
                    with dbytes.write_size():
                        dbytes.write_int(4, len(self.children))
                        for obj in self.children:
                            obj.write(dbytes)

            self._write_sub(dbytes)

    def _write_sub(self, dbytes):
        pass

    def iter_children(self, ty=None, name=None):
        for obj in self.children:
            if ty is None or isinstance(obj, ty):
                if name is None or obj.type == name:
                    yield obj

    def _print_data(self, p):
        if 'transform' in p.flags:
            p(f"Transform: {format_transform(self.transform)}")

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

    def _read(self, dbytes):
        sec = self._get_start_section()
        if sec.magic == MAGIC_8:
            # Levelinfo section only found in old (v1) maps
            self.type = 'Section 88888888'
            self._report_end_pos(sec.data_start + sec.data_size)
            self._add_unknown(4)
            self.skybox_name = dbytes.read_str()
            self._add_unknown(143)
            self.name = dbytes.read_str()
            return
        LevelObject._read(self, dbytes)

    def _read_section_data(self, dbytes, sec):
        if sec.magic == MAGIC_2:
            if sec.ident == 0x52:
                self.version = version = sec.version

                self._add_unknown(8)
                self.name = dbytes.read_str()
                self._add_unknown(4)
                self.modes = modes = {}
                num_modes = dbytes.read_int(4)
                for i in range(num_modes):
                    mode = dbytes.read_int(4)
                    modes[mode] = dbytes.read_byte()
                self.music_id = dbytes.read_int(4)
                if version <= 3:
                    self.skybox_name = dbytes.read_str()
                    self._add_unknown(57)
                elif version == 4:
                    self._add_unknown(141)
                elif version == 5:
                    self._add_unknown(172)
                elif 6 <= version:
                    # confirmed only for v6..v9
                    self._add_unknown(176)
                self.medal_times = times = []
                self.medal_scores = scores = []
                for i in range(4):
                    times.append(dbytes.read_struct(S_FLOAT)[0])
                    scores.append(dbytes.read_int(4, signed=True))
                if version >= 1:
                    self.abilities = dbytes.read_struct(S_ABILITIES)
                if version >= 2:
                    self.difficulty = dbytes.read_int(4)
                return True
        return BytesModel._read_section_data(self, dbytes, sec)

    def _print_type(self, p):
        LevelObject._print_type(self, p)
        if self.version is not None:
            p(f"Object version: {self.version}")

    def _print_data(self, p):
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
            p(f"Level modes: {modes_str or 'None'}")
        if self.abilities:
            ab_str = ', '.join(AbilityToggle.to_name_for_value(toggle, value)
                               for toggle, value in enumerate(self.abilities)
                               if value != 0)
            if not ab_str:
                ab_str = "All"
            p(f"Abilities: {ab_str}")
        if self.difficulty is not None:
            p(f"Difficulty: {Difficulty.to_name(self.difficulty)}")


class Layer(BytesModel):

    layer_name = None
    num_objects = 0
    objects_start = None
    layer_flags = (0, 0, 0)

    def _read(self, dbytes):
        s7 = self._get_start_section()
        if s7.magic != MAGIC_7:
            raise ValueError(f"Invalid layer section: {s7.magic}")
        self._report_end_pos(s7.data_end)

        self.layer_name = s7.layer_name
        self.num_objects = s7.num_objects

        pos = dbytes.pos
        if pos + 4 >= s7.data_end:
            # Happens with empty old layer sections, this prevents error
            # with empty layer at end of file.
            return
        tmp = dbytes.read_int(4)
        dbytes.pos = pos
        if tmp == 0 or tmp == 1:
            self._add_unknown(4)
            flags = dbytes.read_struct("bbb")
            if tmp == 0:
                frozen = 1 if flags[0] == 0 else 0
                self.layer_flags = (flags[1], frozen, flags[2])
            else:
                self.layer_flags = flags
                self._add_unknown(1)

        self.objects_start = dbytes.pos

    def iter_objects(self):
        if not self.num_objects:
            return
        dbytes = self.dbytes
        dbytes.pos = self.objects_start
        for obj, sane, exc in PROBER.iter_maybe(dbytes, max_pos=self.end_pos):
            yield obj, sane, exc
            if not sane:
                break

    def _print_data(self, p):
        with need_counters(p) as counters:
            p(f"Layer: {self.layer_name!r}")
            p(f"Layer object count: {self.num_objects}")
            if self.layer_flags:
                flag_str = ', '.join(
                    format_flags(zip(self.layer_flags, LAYER_FLAG_NAMES)))
                if not flag_str:
                    flag_str = "None"
                p(f"Layer flags: {flag_str}")
            p.counters.num_layers += 1
            p.counters.layer_objects += self.num_objects
            with p.tree_children():
                _print_objects(p, obj_only(self.iter_objects()))
            if counters:
                counters.print_data(p)


@PROBER.for_type('Group')
class Group(LevelObject):

    child_prober = PROBER
    is_object_group = True
    has_children = True
    type = 'Group'

    custom_name = None

    def _read_section_data(self, dbytes, sec):
        if sec.magic == MAGIC_2:
            if sec.ident == 0x1d: # Group / inspect Children
                return True
            elif sec.ident == 0x63: # Group name
                if sec.data_size > 12:
                    self.custom_name = dbytes.read_str()
                return True
        return LevelObject._read_section_data(self, dbytes, sec)

    def _write_sub(self, dbytes):
        with dbytes.write_section(MAGIC_2, ident=0x1d, version=1):
            dbytes.write_int(4, MAGIC_1)
            dbytes.write_int(4, 0) # num values
            dbytes.write_int(4, 0) # inspect Children: None
        with dbytes.write_section(MAGIC_2, ident=0x63, version=0):
            if self.custom_name is not None:
                dbytes.write_str(self.custom_name)

    def _print_children(self, p):
        with need_counters(p) as counters:
            num = len(self.children)
            if num:
                p(f"Grouped objects: {num}")
                if 'groups' in p.flags:
                    p.counters.grouped_objects += num
                    with p.tree_children():
                        _print_objects(p, self.children)
            if counters:
                counters.print_data(p)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        if self.custom_name is not None:
            p(f"Custom name: {self.custom_name!r}")

    def recenter(self, center):
        pos, rot, scale = self.transform
        self.transform = center, rot, scale
        diff = tuple(c - o for c, o in zip(pos, center))
        for obj in self.children:
            pos, rot, scale = obj.transform
            pos = tuple(o + d for o, d in zip(pos, diff))
            obj.transform = pos, rot, scale


@SUBOBJ_PROBER.for_type('Teleporter')
class SubTeleporter(SubObject):

    destination = None
    link_id = None
    trigger_checkpoint = None

    def _read_section_data(self, dbytes, sec):
        if sec.magic == MAGIC_2:
            if sec.ident == 0x3E:
                value = dbytes.read_int(4)
                self.destination = value
                return True
            elif sec.ident == 0x3F:
                value = dbytes.read_int(4)
                self.link_id = value
                return True
            elif sec.ident == 0x51:
                if sec.data_size > 12:
                    check = dbytes.read_byte()
                else:
                    # if section is too short, the checkpoint is enabled
                    check = 1
                self.trigger_checkpoint = check
                return True
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
        if sec.magic == MAGIC_2:
            if sec.ident == 0x5d:
                if sec.data_size >= 16:
                    num_props = dbytes.read_int(4)
                    for _ in range(num_props):
                        propname = dbytes.read_str()
                        self._add_unknown(8)
                        if propname == "DelayBeforeBroadcast":
                            value = dbytes.read_struct(S_FLOAT)[0]
                            self.delay_before_broadcast = value
                        else:
                            # don't know format/length of other properties
                            break
                return True
        return SubObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        if self.delay_before_broadcast is not None:
            p(f"Delay before broadcast: {self.delay_before_broadcast}")


@PROBER.for_type('WorldText')
class WorldText(LevelObject):

    text = None

    def _read_section_data(self, dbytes, sec):
        if sec.magic == MAGIC_3:
            if sec.ident == 0x07:
                pos = sec.data_start + 12
                if pos < sec.data_end:
                    dbytes.pos = pos
                    self.text = dbytes.read_str()
                    for i in range((sec.data_end - dbytes.pos) // 4):
                        self._add_unknown(value=dbytes.read_struct(S_FLOAT)[0])
                else:
                    self.text = f"Hello World"
                return True
        return LevelObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        if self.text is not None:
            p(f"World text: {self.text!r}")


@PROBER.for_type('InfoDisplayBox')
class InfoDisplayBox(LevelObject):

    version = None
    texts = ()

    def _read_section_data(self, dbytes, sec):
        if sec.magic == MAGIC_2:
            if sec.ident == 0x4A:
                texts = self.texts
                self.version = version = sec.version
                if version == 0:
                    num_props = dbytes.read_int(4)
                    self.texts = texts = [None] * 5
                    for i in range(num_props):
                        propname = dbytes.read_str()
                        if propname.startswith("InfoText"):
                            dbytes.pos = value_start = dbytes.pos + 8
                            if not math.isnan(dbytes.read_struct(S_FLOAT)[0]):
                                dbytes.pos = value_start
                                index = int(propname[-1])
                                texts[index] = dbytes.read_str()
                        else:
                            dbytes.pos += 12
                else:
                    # only verified in v2
                    self.fadeout_time = dbytes.read_struct(S_FLOAT)
                    for i in range(5):
                        self._add_unknown(4) # f32 delay
                        if texts is ():
                            self.texts = texts = []
                        texts.append(dbytes.read_str())
                return True
        return LevelObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        p(f"Version: {self.version}")
        for i, text in enumerate(self.texts):
            if text:
                p(f"Text {i}: {text!r}")


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
        if sec.magic == MAGIC_2:
            if sec.ident == 0x57:
                if sec.version == 0:
                    num_props = dbytes.read_int(4)
                    for _ in range(num_props):
                        propname = dbytes.read_str()
                        self._add_unknown(8)
                        spos = dbytes.pos
                        if spos + 4 <= sec.data_end:
                            peek = dbytes.read_n(4)
                            # this is weird
                            if peek == FLOAT_SKIP_BYTES:
                                continue
                        dbytes.pos = spos
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
                            # unknown property, don't know length
                            return True
                    return True
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
                    return True
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
        if sec.magic == MAGIC_3:
            if sec.ident == 0x0e:
                # SphereCollider
                self.trigger_center = (0.0, 0.0, 0.0)
                self.trigger_radius = 50.0
                with dbytes.limit(sec.data_end, True):
                    self.trigger_center = read_n_floats(dbytes, 3, (0.0, 0.0, 0.0))
                    self.trigger_radius = dbytes.read_struct(S_FLOAT)[0]
                return True
        elif sec.magic == MAGIC_2:
            if sec.ident == 0x45:
                # GravityTrigger
                self.disable_gravity = 1
                self.drag_scale = 1.0
                self.drag_scale_angular = 1.0
                with dbytes.limit(sec.data_end, True):
                    self.disable_gravity = dbytes.read_byte()
                    self.drag_scale = dbytes.read_struct(S_FLOAT)[0]
                    self.drag_scale_angular = dbytes.read_struct(S_FLOAT)[0]
                return True
            elif sec.ident == 0x4b:
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
                return True
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
        if sec.magic == MAGIC_3:
            if sec.ident == 0x0f:
                # collider
                return True
        elif sec.magic == MAGIC_2:
            if sec.ident == 0x63:
                # CustomName
                if dbytes.pos < sec.data_end:
                    with dbytes.limit(sec.data_end):
                        self.custom_name = dbytes.read_str()
                return True
            elif sec.ident == 0xa0:
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
                return True
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

    def _read_section_data(self, dbytes, sec):
        if sec.magic == MAGIC_3:
            if sec.ident == 0x0f:
                # BoxCollider
                return True
        elif sec.magic == MAGIC_2:
            if sec.ident == 0x5e:
                # Abilities
                if sec.data_size > 16:
                    self.abilities = abilities = {}
                    num_props = dbytes.read_int(4)
                    for i in range(num_props):
                        propname = dbytes.read_str()
                        dbytes.pos = value_start = dbytes.pos + 8
                        value = read_weird_bool(dbytes)
                        if propname in self.KNOWN_ABILITIES:
                            abilities[propname] = value
                return True
        return LevelObject._read_section_data(self, dbytes, sec)

    def _print_data(self, p):
        LevelObject._print_data(self, p)
        ab_str = ', '.join(k for k, v in self.abilities.items() if v)
        if not ab_str:
            ab_str = "None"
        p(f"Abilities: {ab_str}")


@PROBER.for_type("WedgeGS")
class WedgeGS(LevelObject):

    type = "WedgeGS"
    has_children = True

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
        if sec.magic == MAGIC_3:
            if sec.ident == 3:
                # Material
                return True
        elif sec.magic == MAGIC_2:
            if sec.ident == 0x83:
                # GoldenSimples
                return True
        return LevelObject._read_section_data(self, dbytes, sec)

    def _write_sub(self, dbytes):
        with dbytes.write_section(MAGIC_3, ident=3, version=2):
            dbytes.write_int(4, MAGIC_1)
            dbytes.write_int(4, 1) # num values?
            dbytes.write_str("SimplesMaterial")
            dbytes.write_int(4, MAGIC_1)
            dbytes.write_int(4, 4) # num values?
            dbytes.write_str("_Color")
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_color))
            dbytes.write_str("_EmitColor")
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_emit))
            dbytes.write_str("_ReflectColor")
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_reflect))
            dbytes.write_str("_SpecColor")
            dbytes.write_bytes(S_FLOAT4.pack(*self.mat_spec))

        with dbytes.write_section(MAGIC_2, ident=0x83, version=3):
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


class Level(BytesModel):

    settings = None

    def _read(self, dbytes):
        sec = self._get_start_section()
        if sec.magic != MAGIC_9:
            raise IOError("Unexcpected section: {sec.magic}")
        self.level_name = sec.level_name

    def get_settings(self):
        s = self.settings
        if not s:
            s, sane, exc = LevelSettings.maybe(self.dbytes)
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
        for layer, layer_sane, exc in Layer.iter_maybe(dbytes):
            sane = layer_sane or layer.objects_start is not None
            if with_layers:
                yield layer, sane, exc
            if with_objects:
                for obj, sane, exc in layer.iter_objects():
                    yield obj, sane, exc
            if not layer_sane:
                return
            dbytes.pos = layer.end_pos

    def iter_layers(self):
        dbytes = self.dbytes
        self.move_to_first_layer()
        for layer, sane, exc in Layer.iter_maybe(dbytes):
            yield layer
            if not sane:
                return
            dbytes.pos = layer.end_pos

    def _print_data(self, p):
        p(f"Level name: {self.level_name!r}")
        try:
            settings = self.get_settings()
            p.print_data_of(settings)
            if not settings.sane_end_pos:
                return
            with need_counters(p) as counters:
                for layer in self.iter_layers():
                    p.print_data_of(layer)
                if counters:
                    counters.print_data(p)
        except Exception as e:
            p.print_exception(e)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
