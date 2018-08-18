

from distance.bytes import (
    DstBytes, Section, Magic,
    SKIP_BYTES,
    S_BYTE, S_FLOAT, S_UINT, S_FLOAT3,
)
from distance.base import Fragment
from distance._data import NamedPropertyList
from distance.classes import CollectorGroup, RegisterError
from distance._common import classproperty
from . import bases


Classes = CollectorGroup()


class named_property_getter(property):

    """Decorate properties to create a getter for a named property."""

    def __init__(self, propname, default=None):
        self.propname = propname
        self.default = default
        def fget(obj):
            data = self.props.get(self.propname, None)
            if not data or data == SKIP_BYTES:
                return self.default
            db = DstBytes.from_data(data)
            return self.func(obj, db)
        property.__init__(self, fget)

    def __call__(self, func):
        self.func = func
        self.__doc__ = func.__doc__
        return self


class BaseNamedProperty(property):

    """Create a property that translates the named property using `struct1`.

    `propname` - Name of the property.
    `struct1` - A `struct.Struct` object with a single field.

    """

    def __init__(self, propname, default=None):
        doc = f"Named property {propname!r}"
        self.propname = propname
        self.default = default
        def fget(obj, objtype=None):
            data = obj.props.get(propname, None)
            if not data or data == SKIP_BYTES:
                return default
            return self._from_bytes(data)
        def fset(obj, value):
            obj.props[propname] = self._to_bytes(value)
        def fdel(obj):
            del obj.props[propname]
        super().__init__(fget, fset, fdel, doc=doc)


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


@Classes.common.add_info(tag='NamedPropertiesFragment')
class NamedPropertiesFragment(Fragment):

    @classproperty
    def _fields_(cls):
        result = {name: value.default
                  for name, value in cls.__dict__.items()
                  if isinstance(value, (BaseNamedProperty, named_property_getter))}
        try:
            add = cls._add_fields_
        except AttributeError:
            pass
        else:
            result.update(add)
        return result

    @classproperty
    def class_tag(cls):
        tag = super().class_tag
        if tag == 'NamedProperties':
            return None
        return tag

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

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if self.props.old_format:
            p(f"Old properties format")
        if 'allprops' in p.flags and self.props:
            self.props.print(p)


@Classes.fragments.fragment
class RaceEndLogicFragment(NamedPropertiesFragment):

    base_container = Section.base(Magic[2], 0x5d)
    container_versions = 0

    is_interesting = True

    _fields_ = dict(
        delay_before_broadcast = 0.0,
    )

    delay_before_broadcast = StructNamedProperty('DelayBeforeBroadcast', S_FLOAT)

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        delay = self.delay_before_broadcast
        if delay:
            p(f"Delay before broadcast: {delay}")


@Classes.fragments.fragment
class EnableAbilitiesTriggerFragment(NamedPropertiesFragment):

    base_container = Section.base(Magic[2], 0x5e)
    container_versions = 0

    is_interesting = True

    KNOWN_ABILITIES = (
        'EnableFlying', 'EnableJumping',
        'EnableBoosting', 'EnableJetRotating',
    )

    _add_fields_ = dict(
        abilities = None,
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

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        ab_str = ', '.join(k for k, v in self.abilities.items() if v)
        if not ab_str:
            ab_str = "None"
        p(f"Abilities: {ab_str}")
        if self.bloom_out is not None:
            p(f"Bloom out: {self.bloom_out}")


@Classes.fragments.fragment
class OldCarScreenTextDecodeTriggerFragment(bases.BaseCarScreenTextDecodeTrigger, NamedPropertiesFragment):

    container_versions = 0

    text = StringNamedProperty('Text')

    per_char_speed = StructNamedProperty('PerCharSpeed', S_FLOAT)

    clear_on_finish = ByteNamedProperty('ClearOnFinish')

    clear_on_trigger_exit = ByteNamedProperty('ClearOnTriggerExit')

    destroy_on_trigger_exit = ByteNamedProperty('DestroyOnTriggerExit')

    time_text = StringNamedProperty('TimeText')

    static_time_text = ByteNamedProperty('StaticTimeText')

    announcer_action = StructNamedProperty('AnnouncerAction', S_UINT)


@Classes.fragments.fragment
class OldInfoDisplayLogicFragment(bases.BaseInfoDisplayLogic, NamedPropertiesFragment):

    container_versions = 0

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


@Classes.fragments.fragment
class OldTeleporterEntranceFragment(bases.BaseTeleporterEntrance, NamedPropertiesFragment):

    container_versions = 0

    # type guessed - no example available
    destination = StructNamedProperty('LinkID', S_UINT, default=0)


@Classes.fragments.fragment
class OldTeleporterExitFragment(bases.BaseTeleporterExit, NamedPropertiesFragment):

    container_versions = 0

    # type guessed - no example available
    link_id = StructNamedProperty('LinkID', S_UINT, default=0)


@Classes.fragments.fragment
class OldInterpolateToPositionOnTriggerFragment(
        bases.BaseInterpolateToPositiononTrigger, NamedPropertiesFragment):

    container_versions = 0

    relative = 1
    local_movement = 0

    actually_interpolate = ByteNamedProperty('ActuallyInterpolate')

    interp_end_pos = TupleStructNamedProperty('EndPos', S_FLOAT3)

    interp_time = StructNamedProperty('MoveTime', S_FLOAT)


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


def add_property_fragments_to_collector(coll):
    globs = globals()
    for sec, name in PROPERTY_FRAGS:
        if name:
            typename = name + "Fragment"
        else:
            typename = "NamedPropertiesFragment"
        cls = globs[typename]
        try:
            coll.add_fragment(cls, sec)
        except RegisterError as e:
            if not issubclass(e.registered, NamedPropertiesFragment):
                raise ValueError(f"Fragment registered for section {sec} has"
                                 f" incompatible type: {e.registered}")


_create_property_fragment_classes()
add_property_fragments_to_collector(Classes.fragments)


# vim:set sw=4 ts=8 sts=4 et:
