"""Level fragment implementations."""


import math

from .bytes import (
    Section,
    S_FLOAT, S_FLOAT3, S_BYTE, S_UINT,
    Magic,
    SKIP_BYTES,
    DstBytes,
)
from .base import Fragment
from .prober import RegisterError
from ._data import NamedPropertyList, MaterialSet
from .constants import ForceType
from ._common import set_default_attrs
from ._default_probers import DefaultProbers
from .construct import BaseConstructFragment, C


PROBER = DefaultProbers.fragments


def read_n_floats(dbytes, n, default=None):
    def read_float():
        return dbytes.read_struct(S_FLOAT)[0]
    fdata = dbytes.read_bytes(4)
    if fdata == SKIP_BYTES:
        return default
    else:
        f = S_FLOAT.unpack(fdata)[0]
        return (f, *(read_float() for _ in range(n - 1)))


class NamedPropertiesFragment(Fragment):

    def __init__(self, *args, **kw):
        self.props = NamedPropertyList()
        Fragment.__init__(self, *args, **kw)

    def _clone_data(self, new):
        new.props.update(self.props)

    def _read_section_data(self, dbytes, sec):
        if sec.content_size >= 4:
            self.props.read(dbytes, max_pos=sec.end_pos,
                            detect_old=True)

    def _write_section_data(self, dbytes, sec):
        if self.props:
            self.props.write(dbytes)

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.props.old_format:
            p(f"Old properties format")
        if 'allprops' in p.flags and self.props:
            self.props.print_data(p)


def named_property_getter(propname, default=None):

    """Decorate properties to create a getter for a named property."""

    def decorate(func):

        def fget(self):
            data = self.props.get(propname, None)
            if not data or data == SKIP_BYTES:
                return default
            db = DstBytes.from_data(data)
            return func(self, db)
        return property(fget, None, None, doc=func.__doc__)

    return decorate


class BaseNamedProperty(property):

    """Create a property that translates the named property using `struct1`.

    `propname` - Name of the property.
    `struct1` - A `struct.Struct` object with a single field.

    """

    def __init__(self, propname, default=None):
        self.__doc__ = f"Named property {propname!r}"
        self.propname = propname
        self.default = default

    def __get__(self, inst, objtype=None):
        data = inst.props.get(self.propname, None)
        if not data or data == SKIP_BYTES:
            return self.default
        return self._from_bytes(data)

    def __set__(self, inst, value):
        inst.props[self.propname] = self._to_bytes(value)

    def __delete__(self, inst):
        del inst.props[self.propname]


class TupleStructNamedProperty(BaseNamedProperty):

    def __init__(self, propname, struct, default=None):
        super().__init__(propname, default=default)
        self.__doc__ = f"Named property {propname!r} of type {struct.format}"
        self.struct = struct

    def _from_bytes(self, data):
        if len(data) < self.struct.size:
            return self.default
        return self.struct.unpack(data)

    def _to_bytes(self, value):
        return self.struct.pack(*value)


class StructNamedProperty(TupleStructNamedProperty):

    def _from_bytes(self, data):
        if len(data) < self.struct.size:
            return self.default
        return self.struct.unpack(data)[0]

    def _to_bytes(self, value):
        return self.struct.pack(value)


class ByteNamedProperty(StructNamedProperty):

    def __init__(self, propname, default=None):
        super().__init__(propname, S_BYTE, default=default)


class StringNamedProperty(BaseNamedProperty):

    def __init__(self, propname, default=None):
        super().__init__(propname, default=default)
        self.__doc__ = f"Named property {propname!r} of type string"

    def _from_bytes(self, data):
        return DstBytes.from_data(data).read_str()

    def _to_bytes(self, inst, value):
        db = DstBytes.in_memory()
        db.write_str(value)
        return db.file.getvalue()

    def __delete__(self, inst):
        del inst.props[self.propname]


@PROBER.fragment
class GroupFragment(Fragment):

    base_section = Section.base(Magic[2], 0x1d)
    section_versions = 1

    value_attrs = dict(
        inspect_children = None, # None
    )

    _has_more_data = False

    def _init_defaults(self):
        super()._init_defaults()
        for name, value in self.value_attrs.items():
            setattr(self, name, value)

    def _read_section_data(self, dbytes, sec):
        if sec.content_size < 12:
            self.inspect_children = None
        else:
            dbytes.require_equal_uint4(Magic[1])
            num_values = dbytes.read_uint4()
            self.inspect_children = dbytes.read_uint4()
            # do save raw_data if there are unexpected values following
            self._has_more_data = num_values > 0

    def _write_section_data(self, dbytes, sec):
        if not self._has_more_data:
            if self.inspect_children is not None:
                dbytes.write_int(4, Magic[1])
                dbytes.write_int(4, 0) # num values
                dbytes.write_int(4, self.inspect_children)
        else:
            dbytes.write_bytes(self.raw_data)


@PROBER.fragment
class CustomNameFragment(Fragment):

    base_section = Section.base(Magic[2], 0x63)
    section_versions = 0

    value_attrs = dict(custom_name=None)

    is_interesting = True

    custom_name = None

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            self.custom_name = dbytes.read_str()

    def _write_section_data(self, dbytes, sec):
        if self.custom_name is not None:
            dbytes.write_str(self.custom_name)

    def _print_type(self, p):
        p(f"Fragment: CustomName")

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.custom_name is not None:
            p(f"Custom name: {self.custom_name!r}")


@PROBER.fragment
class GoldenSimplesFragment(BaseConstructFragment):

    base_section = Section.base(Magic[2], 0x83)
    section_versions = 3
    default_section = Section(base_section, version=3)

    _construct = C.struct(
        image_index = C.default(C.uint, 17),
        emit_index = C.default(C.uint, 17),
        preset = C.default(C.uint, 0),
        tex_scale = C.default(C.float[3], (1, 1, 1)),
        tex_offset = C.default(C.float[3], (0, 0, 0)),
        flip_tex_uv = C.default(C.byte, 0),
        world_mapped = C.default(C.byte, 0),
        disable_diffuse = C.default(C.byte, 0),
        disable_bump = C.default(C.byte, 0),
        bump_strength = C.default(C.float, 0),
        disable_reflect = C.default(C.byte, 0),
        disable_collision = C.default(C.byte, 0),
        additive_transp = C.default(C.byte, 0),
        multip_transp = C.default(C.byte, 0),
        invert_emit = C.default(C.byte, 0),
    )

    def _print_type(self, p):
        p(f"Fragment: GoldenSimples")


class BaseTeleporterEntrance(object):

    base_section = Section.base(Magic[2], 0x3e)

    is_interesting = True

    def _print_data(self, p):
        super()._print_data(p)
        if self.destination is not None:
            p(f"Teleports to: {self.destination}")


@PROBER.fragment
class OldTeleporterEntranceFragment(BaseTeleporterEntrance, NamedPropertiesFragment):

    section_versions = 0

    # type guessed - no example available
    destination = StructNamedProperty('LinkID', S_UINT, default=0)


@PROBER.fragment
class TeleporterEntranceFragment(BaseTeleporterEntrance, Fragment):

    section_versions = 1, 2, 3

    destination = None

    def _read_section_data(self, dbytes, sec):
        self.destination = dbytes.read_uint4()

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.destination is not None:
            p(f"Teleports to: {self.destination}")


class BaseTeleporterExit(object):

    base_section = Section.base(Magic[2], 0x3f)

    is_interesting = True

    def _print_data(self, p):
        super()._print_data(p)
        if self.link_id is not None:
            p(f"Link ID: {self.link_id}")


@PROBER.fragment
class TeleporterExitFragment(BaseTeleporterExit, Fragment):

    section_versions = 1

    link_id = None

    def _read_section_data(self, dbytes, sec):
        self.link_id = dbytes.read_uint4()


@PROBER.fragment
class OldTeleporterExitFragment(BaseTeleporterExit, NamedPropertiesFragment):

    section_versions = 0

    # type guessed - no example available
    link_id = StructNamedProperty('LinkID', S_UINT, default=0)


@PROBER.fragment
class TeleporterExitCheckpointFragment(Fragment):

    base_section = Section.base(Magic[2], 0x51)
    section_versions = 0

    trigger_checkpoint = 1

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            self.trigger_checkpoint = dbytes.read_byte()
        else:
            # if section is too short, the checkpoint is enabled
            self.trigger_checkpoint = 1

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.trigger_checkpoint is not None:
            p(f"Trigger checkpoint: {self.trigger_checkpoint}")


@PROBER.fragment
class SphereColliderFragment(Fragment):

    base_section = Section.base(Magic[3], 0x0e)
    section_versions = 1

    trigger_center = None
    trigger_radius = None

    def _read_section_data(self, dbytes, sec):
        if sec.content_size >= 8:
            self.trigger_center = read_n_floats(dbytes, 3)
            radius = dbytes.read_struct(S_FLOAT)[0]
            if math.isnan(radius):
                radius = None
            self.trigger_radius = radius


@PROBER.fragment
class BoxColliderFragment(Fragment):

    base_section = Section.base(Magic[3], 0xf)
    section_versions = 2

    trigger_center = None
    trigger_size = None

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            self.trigger_center = read_n_floats(dbytes, 3)
            self.trigger_size = read_n_floats(dbytes, 3)


@PROBER.fragment
class GravityToggleFragment(Fragment):

    base_section = Section.base(Magic[2], 0x45)
    section_versions = 1

    is_interesting = True

    disable_gravity = 1
    drag_scale = 1.0
    drag_scale_angular = 1.0

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            self.disable_gravity = dbytes.read_byte()
            self.drag_scale = dbytes.read_struct(S_FLOAT)[0]
            self.drag_scale_angular = dbytes.read_struct(S_FLOAT)[0]

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.disable_gravity is not None:
            p(f"Disable gravity: {self.disable_gravity and 'yes' or 'no'}")
        if self.drag_scale is not None:
            p(f"Drag scale: {self.drag_scale}")
        if self.drag_scale_angular is not None:
            p(f"Angular drag scale: {self.drag_scale_angular}")


@PROBER.fragment
class MusicTriggerFragment(Fragment):

    base_section = Section.base(Magic[2], 0x4b)
    section_versions = 1

    is_interesting = True

    music_id = 19
    one_time_trigger = 1
    reset_before_trigger = 0
    disable_music_trigger = 0

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            self.music_id = dbytes.read_uint4()
            self.one_time_trigger = dbytes.read_byte()
            self.reset_before_trigger = dbytes.read_byte()
            self.disable_music_trigger = dbytes.read_byte()

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.music_id is not None:
            p(f"Music ID: {self.music_id}")
        if self.one_time_trigger is not None:
            p(f"One time trigger: {self.one_time_trigger and 'yes' or 'no'}")
        if self.reset_before_trigger is not None:
            p(f"Reset before trigger: {self.reset_before_trigger and 'yes' or 'no'}")
        if self.disable_music_trigger is not None:
            p(f"Disable music trigger: {self.disable_music_trigger and 'yes' or 'no'}")


_forcezone_value_attrs = dict(
    force_direction = (0.0, 0.0, 1.0),
    global_force = 0,
    force_type = ForceType.WIND,
    gravity_magnitude = 25.0,
    disable_global_gravity = 0,
    wind_speed = 300.0,
    drag_multiplier = 1.0,
)


@PROBER.fragment
@set_default_attrs(_forcezone_value_attrs)
class ForceZoneFragment(Fragment):

    base_section = Section.base(Magic[2], 0xa0)
    section_versions = 0

    is_interesting = True

    value_attrs = _forcezone_value_attrs

    def _read_section_data(self, dbytes, sec):
        self.__dict__.update(self.value_attrs)
        if sec.content_size:
            self.force_direction = read_n_floats(dbytes, 3, (0.0, 0.0, 1.0))
            self.global_force = dbytes.read_byte()
            self.force_type = dbytes.read_uint4()
            self.gravity_magnitude = dbytes.read_struct(S_FLOAT)[0]
            self.disable_global_gravity = dbytes.read_byte()
            self.wind_speed = dbytes.read_struct(S_FLOAT)[0]
            self.drag_multiplier = dbytes.read_struct(S_FLOAT)[0]

    def _print_data(self, p):
        Fragment._print_data(self, p)
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


@PROBER.fragment
class TextMeshFragment(Fragment):

    base_section = Section.base(Magic[3], 0x7)
    section_versions = 1, 2

    is_interesting = True

    have_content = False

    text = None
    font_style = None
    font = None
    _unknown = b''

    def _init_defaults(self):
        super()._init_defaults()
        self.have_content = True

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:

            def skip_or(func, *args):
                with dbytes:
                    try:
                        skip = dbytes.read_bytes(4) == SKIP_BYTES
                    except EOFError:
                        pass
                if skip:
                    dbytes.read_bytes(4)
                    return None
                return func(*args)

            self.have_content = True
            self.text = skip_or(dbytes.read_str)
            self.font_style = skip_or(dbytes.read_uint4)
            if sec.version >= 2:
                self.font = skip_or(dbytes.read_uint4)
            rem = sec.end_pos - dbytes.tell()
            if rem:
                self._unknown = dbytes.read_bytes(rem)

    def _write_section_data(self, dbytes, sec):
        if self.have_content:
            if self.text is None:
                dbytes.write_bytes(SKIP_BYTES)
            else:
                dbytes.write_str(self.text)
            if self.font_style is None:
                dbytes.write_bytes(SKIP_BYTES)
            else:
                dbytes.write_int(4, self.font_style)
            if sec.version >= 2:
                if self.font is None:
                    dbytes.write_bytes(SKIP_BYTES)
                else:
                    dbytes.write_int(4, self.font)
            dbytes.write_bytes(self._unknown)

    def _print_data(self, p):
        Fragment._print_data(self, p)
        p(f"World text: {self.text!r}")


@PROBER.fragment
class TrackNodeFragment(Fragment):

    base_section = Section.base(Magic[2], 0x16)
    section_versions = 2
    default_section = Section(Magic[2], 0x16, 2)

    parent_id = 0
    snap_id = 0
    conn_id = 0
    primary = 0

    def _clone_data(self, new):
        new.parent_id = self.parent_id
        new.snap_id = self.snap_id
        new.conn_id = self.conn_id
        new.primary = self.primary

    def _read_section_data(self, dbytes, sec):
        self.parent_id = dbytes.read_uint4()
        self.snap_id = dbytes.read_uint4()
        self.conn_id = dbytes.read_uint4()
        self.primary = dbytes.read_byte()

    def _write_section_data(self, dbytes, sec):
        dbytes.write_int(4, self.parent_id)
        dbytes.write_int(4, self.snap_id)
        dbytes.write_int(4, self.conn_id)
        dbytes.write_int(1, self.primary)

    def _print_type(self, p):
        p(f"Fragment: TrackNode")

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if 'sections' in p.flags or 'track' in p.flags:
            p(f"Parent ID: {self.parent_id}")
            p(f"Snapped to: {self.snap_id}")
            p(f"Connection ID: {self.conn_id}")
            p(f"Primary: {self.primary and 'yes' or 'no'}")


@PROBER.fragment
class MaterialFragment(Fragment):

    base_section = Section.base(Magic[3], 0x3)
    section_versions = 1, 2

    have_content = False

    def __init__(self, *args, **kw):
        self.materials = MaterialSet()
        Fragment.__init__(self, *args, **kw)

    def _clone_data(self, new):
        dest = new.materials
        for matname, mat in self.materials.items():
            destmat = dest.get_or_add(matname)
            for colname, col in mat.items():
                destmat[colname] = col

    def _read_section_data(self, dbytes, sec):
        if sec.content_size >= 4:
            self.have_content = True
            self.materials.read(dbytes)

    def _write_section_data(self, dbytes, sec):
        if self.materials or self.have_content:
            self.materials.write(dbytes)

    def _print_type(self, p):
        p(f"Fragment: Material")

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if 'allprops' in p.flags and self.materials:
            self.materials.print_data(p)


@PROBER.fragment
class RaceEndLogicFragment(NamedPropertiesFragment):

    base_section = Section.base(Magic[2], 0x5d)
    section_versions = 0

    is_interesting = True

    delay_before_broadcast = StructNamedProperty('DelayBeforeBroadcast', S_FLOAT)

    def _print_data(self, p):
        NamedPropertiesFragment._print_data(self, p)
        delay = self.delay_before_broadcast
        if delay:
            p(f"Delay before broadcast: {delay}")


@PROBER.fragment
class EnableAbilitiesTriggerFragment(NamedPropertiesFragment):

    base_section = Section.base(Magic[2], 0x5e)
    section_versions = 0

    is_interesting = True

    KNOWN_ABILITIES = (
        'EnableFlying', 'EnableJumping',
        'EnableBoosting', 'EnableJetRotating',
    )

    @property
    def abilities(self):
        abilities = {}
        props = self.props
        for k in self.KNOWN_ABILITIES:
            data = props.get(k, SKIP_BYTES)
            if data and data != SKIP_BYTES:
                value = data[0]
            else:
                value = 0
            abilities[k] = value
        return abilities

    enable_boosting = ByteNamedProperty('EnableBoosting', default=0)

    enable_jumping = ByteNamedProperty('EnableJumping', default=0)

    enable_jets = ByteNamedProperty('EnableJetRotating', default=0)

    enable_flying = ByteNamedProperty('EnableFlying', default=0)

    bloom_out = ByteNamedProperty('BloomOut', default=1)

    def _print_data(self, p):
        Fragment._print_data(self, p)
        ab_str = ', '.join(k for k, v in self.abilities.items() if v)
        if not ab_str:
            ab_str = "None"
        p(f"Abilities: {ab_str}")
        if self.bloom_out is not None:
            p(f"Bloom out: {self.bloom_out}")


class BaseCarScreenTextDecodeTrigger(object):

    base_section = Section.base(Magic[2], 0x57)

    is_interesting = True

    per_char_speed = None
    clear_on_finish = None
    clear_on_trigger_exit = None
    destroy_on_trigger_exit = None
    static_time_text = None
    delay = None
    announcer_action = None
    announcer_phrases = ()

    def _print_data(self, p):
        super()._print_data(p)
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


@PROBER.fragment
class OldCarScreenTextDecodeTriggerFragment(BaseCarScreenTextDecodeTrigger, NamedPropertiesFragment):

    section_versions = 0

    text = StringNamedProperty('Text')

    per_char_speed = StructNamedProperty('PerCharSpeed', S_FLOAT)

    clear_on_finish = ByteNamedProperty('ClearOnFinish')

    clear_on_trigger_exit = ByteNamedProperty('ClearOnTriggerExit')

    destroy_on_trigger_exit = ByteNamedProperty('DestroyOnTriggerExit')

    time_text = StringNamedProperty('TimeText')

    static_time_text = ByteNamedProperty('StaticTimeText')

    announcer_action = StructNamedProperty('AnnouncerAction', S_UINT)

    @named_property_getter('AnnouncerPhrases', default=())
    def announcer_phrases(self, db):
        db.require_equal_uint4(Magic[1])
        num_phrases = db.read_uint4()
        phrases = []
        for _ in range(num_phrases):
            phrases.append(db.read_str())
        return phrases


@PROBER.fragment
class CarScreenTextDecodeTriggerFragment(BaseCarScreenTextDecodeTrigger, BaseConstructFragment):

    section_versions = 1

    _construct = C.struct(
        text = C.default(C.str, ""),
        per_char_speed = C.default(C.float, 0),
        clear_on_finish = C.default(C.byte, 0),
        clear_on_trigger_exit = C.default(C.byte, 0),
        destroy_on_trigger_exit = C.default(C.byte, 0),
        time_text = C.default(C.str, ""),
        static_time_text = C.default(C.byte, 1),
        delay = C.default(C.float, 0),
        announcer_action = C.default(C.uint, 0),
    )


class BaseInfoDisplayLogic(object):

    base_section = Section.base(Magic[2], 0x4a)

    is_interesting = True

    fadeout_time = None
    texts = ()
    per_char_speed = None
    destroy_on_trigger_exit = None
    random_char_count = None

    def _print_data(self, p):
        super()._print_data(p)
        for i, text in enumerate(self.texts):
            if text:
                p(f"Text {i}: {text!r}")
        if self.per_char_speed is not None:
            p(f"Per char speed: {self.per_char_speed}")
        if self.destroy_on_trigger_exit is not None:
            p(f"Destroy on trigger exit: {self.destroy_on_trigger_exit and 'yes' or 'no'}")
        if self.random_char_count is not None:
            p(f"Fade out time: {self.fadeout_time}")
        if self.random_char_count is not None:
            p(f"Random char count: {self.random_char_count}")


@PROBER.fragment
class OldInfoDisplayLogicFragment(BaseInfoDisplayLogic, NamedPropertiesFragment):

    section_versions = 0

    @property
    def texts(self):
        texts = [None] * 5
        props = self.props
        for i in range(5):
            propname = 'InfoText' + str(i)
            data = props.get(propname, None)
            if data and data != SKIP_BYTES:
                texts[i] = DstBytes.from_data(data).read_str()
        return texts

    fadeout_time = StructNamedProperty('FadeOutTime', S_FLOAT)

    per_char_speed = StructNamedProperty('PerCharSpeed', S_FLOAT)

    clear_on_trigger_exit = StructNamedProperty('RandomCharCount', S_UINT)

    destroy_on_trigger_exit = ByteNamedProperty('DestroyOnTriggerExit')


@PROBER.fragment
class InfoDisplayLogicFragment(BaseInfoDisplayLogic, Fragment):

    section_versions = 2

    def _read_section_data(self, dbytes, sec):
        # only verified in v2
        if sec.content_size:
            self.fadeout_time = dbytes.read_struct(S_FLOAT)
            self.texts = texts = []
            for i in range(5):
                dbytes.read_bytes(4) # f32 delay
                texts.append(dbytes.read_str())


@PROBER.fragment
class AnimatorFragment(BaseConstructFragment):

    base_section = Section.base(Magic[2], 0x9a)
    section_versions = 7
    default_section = Section(base_section, version=7)

    _construct = C.struct(
        # 2: hinge
        motion_mode = C.default(C.uint, 2),
        do_scale = C.default(C.byte, 0),
        scale_exponents = C.default(C.float[3], (0, 1, 0)),
        do_rotate = C.default(C.byte, 1),
        rotate_axis = C.default(C.float[3], (0, 1, 0)),
        rotate_global = C.default(C.byte, 0),
        rotate_magnitude = C.default(C.float, 90),
        centerpoint = C.default(C.float[3], (0, 0, 0)),
        # 0: none
        translate_type = C.default(C.uint, 0),
        translate_vector = C.default(C.float[3], (0, 10, 0)),
        follow_track_distance = C.default(C.float, 25),
        projectile_gravity = C.default(C.float[3], (0, -25, 0)),
        delay = C.default(C.float, 1),
        duration = C.default(C.float, 1),
        time_offset = C.default(C.float, 0),
        do_loop = C.default(C.byte, 1),
        # 1: pingpong
        extrapolation_type = C.default(C.uint, 1),
        # 3: ease in out
        curve_type = C.default(C.uint, 3),
        editor_anim_time = C.default(C.float, 0),
        use_custom_pong_values = C.default(C.byte, 0),
        pong_delay = C.default(C.float, 1),
        pong_duration = C.default(C.float, 1),
        # 2: ease in out
        pong_curve_type = C.default(C.uint, 2),
        anim_physics = C.default(C.byte, 1),
        always_animate = C.default(C.byte, 0),
        # 1: play
        trigger_default_action = C.default(C.uint, 1),
        # 1: play
        trigger_on_action = C.default(C.uint, 1),
        trigger_wait_for_anim_finish = C.default(C.byte, 0),
        trigger_on_reset = C.default(C.byte, 0),
        # 2: play reverse
        trigger_off_action = C.default(C.uint, 2),
        trigger_off_wait_for_anim_finish = C.default(C.byte, 0),
        trigger_off_reset = C.default(C.byte, 0),
    )


@PROBER.fragment
class EventListenerFragment(Fragment):

    base_section = Section.base(Magic[2], 0x8a)
    section_versions = 0, 1


@PROBER.fragment
class TrackAttachmentFragment(Fragment):

    base_section = Section.base(Magic[2], 0x68)
    section_versions = 0


@PROBER.fragment
class TurnLightOnNearCarFragment(Fragment):

    base_section = Section.base(Magic[2], 0x70)
    section_versions = 1, 2, 3


class BaseInterpolateToPositiononTrigger(object):

    base_section = Section.base(Magic[2], 0x43)


@PROBER.fragment
class OldInterpolateToPositionOnTriggerFragment(
        BaseInterpolateToPositiononTrigger, NamedPropertiesFragment):

    section_versions = 0

    relative = 1
    local_movement = 0

    actually_interpolate = ByteNamedProperty('ActuallyInterpolate')

    interp_end_pos = TupleStructNamedProperty('EndPos', S_FLOAT3)

    interp_time = StructNamedProperty('MoveTime', S_FLOAT)


@PROBER.fragment
class InterpolateToPositionOnTriggerFragment(
        BaseInterpolateToPositiononTrigger, Fragment):

    section_versions = 1, 2

    actually_interpolate = 0
    relative = 1
    interp_end_pos = None
    interp_time = None
    local_movement = 0

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            self.actually_interpolate = dbytes.read_byte()
            self.relative = dbytes.read_byte()
            self.interp_end_pos = read_n_floats(dbytes, 3)
            self.interp_time = dbytes.read_struct(S_FLOAT)[0]
            if sec.version >= 2:
                self.local_movement = dbytes.read_byte()


@PROBER.fragment
class RigidbodyAxisRotationLogicFragment(Fragment):

    base_section = Section.base(Magic[2], 0x17)
    section_versions = 1

    angular_speed = None
    rotation_axis = None
    limit_rotation = None
    rotation_bounds = None
    starting_angle_offset = None

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            self.angular_speed = dbytes.read_struct(S_FLOAT)[0]
            self.rotation_axis = dbytes.read_uint4()
            self.limit_rotation = dbytes.read_byte()
            self.rotation_bounds = dbytes.read_struct(S_FLOAT)[0]
            self.starting_angle_offset = dbytes.read_struct(S_FLOAT)[0]

    def _print_data(self, p):
        if 'allprops' in p.flags:
            p(f"Angular speed: {self.angular_speed}")
            p(f"Rotation axis: {self.rotation_axis}")
            p(f"Limit rotation: {self.limit_rotation}")
            p(f"Rotation bounds: {self.rotation_bounds}")
            p(f"Starting angle offset: {self.starting_angle_offset}")


PROPERTY_FRAGS = (
    (Section(Magic[2], 0x25, 0), "PopupBlockerLogic"),
    (Section(Magic[2], 0x42, 0), "ObjectSpawnCircle"),
    (Section(Magic[2], 0x39, 0), "ParticleEmitLogic"),
    (Section(Magic[2], 0x26, 0), "Light"),
    (Section(Magic[2], 0x28, 0), "SmoothRandomPosition"),
    (Section(Magic[2], 0x45, 0), None),
    (Section(Magic[2], 0x24, 0), "OldFlyingRingLogic"),
    (Section(Magic[2], 0x50, 0), "Pulse"),
    # found on Damnation
    (Section(Magic[2], 0x59, 0), None),
    (Section(Magic[2], 0x4b, 0), None),
    (Section(Magic[2], 0x4e, 0), None),
    (Section(Magic[2], 0x3a, 0), None),
    (Section(Magic[2], 0x58, 0), None),
    (Section(Magic[2], 0x2c, 0), None),
    # found on Hextreme
    (Section(Magic[2], 0x1b, 0), None),
    # found on "Brief Chaos" object EmpireBrokenBuilding006_PiecesSeparated
    (Section(Magic[2], 0x44, 0), None),
    # from v5 AudioEventTrigger
    (Section(Magic[2], 0x74, 0), None),
    # from v5 CubeMIDI
    (Section(Magic[2], 0x3d, 0), None),
    # from v9 RumbleZone
    (Section(Magic[2], 0x66, 0), None),
    # from v8 PulseCore
    (Section(Magic[2], 0x4f, 0), None),
    # from v8 KillGridBox
    (Section(Magic[2], 0x82, 0), None),
    # from v5 WarpAnchor
    (Section(Magic[2], 0x6e, 0), None),
    # from v7 PlanetWithSphericalGravity
    (Section(Magic[2], 0x5f, 0), None),
    # from v5 VirusSpiritShard
    (Section(Magic[2], 0x67, 0), None),
    # from v9 WingCorruptionZone
    (Section(Magic[2], 0x53, 0), None),
    # from v8 IntroCutsceneLight
    (Section(Magic[2], 0x55, 0), None),
    # from v9 CutsceneLightning
    (Section(Magic[2], 0x6f, 0), None),
    # from s8 (map "The Matrix Arena")
    (Section(Magic[2], 0x17, 0), None), # from EmpireCircle
    (Section(Magic[2], 0x1f, 0), None), # from Teleporter
    # from v3 WarningPulseLight
    (Section(Magic[2], 0x65, 0), None),
    # from v1 LaserMid (sub of VirusLaserTriCircleRotating)
    (Section(Magic[2], 0x1a, 0), None),
    # from v5 EmpireProximityDoor
    (Section(Magic[2], 0x76, 0), None),
    # from v5 VirusSpiritWarpTeaser
    (Section(Magic[2], 0x7e, 0), None),
    # from v1 GlobalFog
    (Section(Magic[2], 0x60, 0), None),
    # from v8 DisableLocalCarWarnings
    (Section(Magic[2], 0x62, 0), None),
    # from v7 AdventureAbilitySettings
    (Section(Magic[2], 0x4d, 0), None),
    # from v3 VirusBase
    # very old versions (map "birthday bash court") don't use offsets
    (Section(Magic[2], 0x27, 0), None),
    # from s8 (map "The Pumpkin Patch")
    (Section(Magic[2], 0x38, 0), None),
    # from SoccerGoalLogic
    (Section(Magic[2], 0x29, 0), None),
    (Section(Magic[2], 0x3e, 0), "OldTeleporterEntrance"),
    (Section(Magic[2], 0x3f, 0), "OldTeleporterExit"),
    (Section(Magic[2], 0x5d, 0), "RaceEndLogic"),
    (Section(Magic[2], 0x5e, 0), "EnableAbilitiesTrigger"),
    (Section(Magic[2], 0x57, 0), "OldCarScreenTextDecodeTrigger"),
    (Section(Magic[2], 0x4a, 0), "OldInfoDisplayLogic"),
    (Section(Magic[2], 0x43, 0), "OldInterpolateToPositionOnTrigger"),
)


def _create_property_fragment_classes():
    globs = globals()
    created = set()
    sections = set()
    for sec, name in PROPERTY_FRAGS:
        key = sec.to_key()
        if key in sections:
            raise ValueError(f"Duplicate section: {sec}")
        sections.add(key)
        if name:
            if name in created:
                raise ValueError(f"Duplicate fragment name: {name}")
            typename = name + "Fragment"
            defined = globs.get(typename, None)
            if defined is not None:
                if not issubclass(defined, NamedPropertiesFragment):
                    raise ValueError(f"Fragment defined with incompatible"
                                     f" type: {typename}")
            else:
                globs[typename] = type(typename, (NamedPropertiesFragment,), {})
            created.add(name)


def add_property_fragments_to_prober(prober):
    globs = globals()
    for sec, name in PROPERTY_FRAGS:
        if name:
            typename = name + "Fragment"
        else:
            typename = "NamedPropertiesFragment"
        cls = globs[typename]
        try:
            prober.add_fragment(cls, sec)
        except RegisterError as e:
            if not issubclass(e.registered, NamedPropertiesFragment):
                raise ValueError(f"Fragment registered for section {sec} has"
                                 f" incompatible type: {e.registered}")


_create_property_fragment_classes()
add_property_fragments_to_prober(PROBER)


def material_property(matname, colname):
    doc = f"property forwarded to material color {matname!r}/{colname!r}"
    def fget(self):
        frag = self.fragment_by_type(MaterialFragment)
        try:
            return frag.materials[matname][colname]
        except KeyError as e:
            raise AttributeError(f"color {matname!r}/{colname!r}") from e
    def fset(self, value):
        frag = self.fragment_by_type(MaterialFragment)
        frag.materials.get_or_add(matname)[colname] = value
    def fdel(self):
        frag = self.fragment_by_type(MaterialFragment)
        mats = frag.materials
        try:
            mat = mats[matname]
            del mat[colname]
        except KeyError as e:
            raise AttributeError(f"color {matname!r}/{colname!r}") from e
        if not mat:
            del mats[matname]
    return property(fget, fset, fdel, doc=doc)


class ForwardMaterialColors(object):

    """Decorator to forward attributes to colors of MaterialFragment."""

    def __init__(self, **colors):
        self.colors = colors

    def __call__(self, target):
        for attrname, (matname, colname, default) in self.colors.items():
            setattr(target, attrname, material_property(matname, colname))

        try:
            clsdefaults = target.__default_colors
        except AttributeError:
            target.__default_colors = clsdefaults = {}
        clsdefaults.update(self.colors)

        return target

    @staticmethod
    def reset_colors(obj):
        mats = obj.fragment_by_type(MaterialFragment).materials
        for matname, colname, value in obj.__default_colors.values():
            mats.get_or_add(matname)[colname] = value


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
