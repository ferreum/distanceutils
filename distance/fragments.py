"""Fragment implementations."""


import math

from .bytes import (
    Section,
    S_FLOAT, S_FLOAT3,
    MAGIC_1, MAGIC_2, MAGIC_3,
    SKIP_BYTES,
)
from .base import Fragment
from .prober import BytesProber
from .data import NamedPropertyList, MaterialSet


PROBER = BytesProber(baseclass=Fragment)


def read_n_floats(dbytes, n, default):
    def read_float():
        return dbytes.read_struct(S_FLOAT)[0]
    f = read_float()
    if math.isnan(f):
        return default
    else:
        return (f, *(read_float() for _ in range(n - 1)))


@PROBER.fragment(MAGIC_2, 0x1d, 1)
class GroupFragment(Fragment):

    value_attrs = dict(
        inspect_children = 0, # None
    )

    def _init_defaults(self):
        Fragment._init_defaults(self)
        for name, value in self.value_attrs.items():
            setattr(self, name, value)

    def _read_section_data(self, dbytes, sec):
        if sec.data_size < 24:
            self.inspect_children = 0
            return True
        self._require_equal(MAGIC_1, 4)
        num_values = dbytes.read_int(4)
        self.inspect_children = dbytes.read_int(4)
        # do save raw_data if there are unexpected values following
        return num_values == 0

    def _write_section_data(self, dbytes, sec):
        if self.raw_data is None:
            if self.inspect_children != 0:
                dbytes.write_int(4, MAGIC_1)
                dbytes.write_int(4, 0) # num values
                dbytes.write_int(4, self.inspect_children)
            return True
        return False


@PROBER.fragment(MAGIC_2, 0x63, 0)
class CustomNameFragment(Fragment):

    value_attrs = ('custom_name',)

    custom_name = None

    def _read_section_data(self, dbytes, sec):
        if sec.data_size > 12:
            self.custom_name = dbytes.read_str()
        else:
            self.custom_name = None
        return True

    def _write_section_data(self, dbytes, sec):
        if self.custom_name is not None:
            dbytes.write_str(self.custom_name)
        return True

    def _print_type(self, p):
        p(f"Fragment: CustomName")

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.custom_name is not None:
            p(f"Custom name: {self.custom_name!r}")


@PROBER.fragment(MAGIC_2, 0x83, 3)
class GoldenSimplesFragment(Fragment):

    value_attrs = dict(
        tex_scale = (1, 1, 1),
        tex_offset = (0, 0, 0),
        image_index = 17,
        emit_index = 17,
        flip_tex_uv = 0,
        world_mapped = 0,
        disable_diffuse = 0,
        disable_bump = 0,
        bump_strength = 0,
        disable_reflect = 0,
        disable_collision = 0,
        additive_transp = 0,
        multip_transp = 0,
        invert_emit = 0,
    )

    def _init_defaults(self):
        Fragment._init_defaults(self)
        for name, value in self.value_attrs.items():
            setattr(self, name, value)

    def _read_section_data(self, dbytes, sec):
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

    def _write_section_data(self, dbytes, sec):
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

    def _print_type(self, p):
        p(f"Fragment: GoldenSimples")


@PROBER.fragment(MAGIC_2, 0x3e, 1)
@PROBER.fragment(MAGIC_2, 0x3e, 2)
@PROBER.fragment(MAGIC_2, 0x3e, 3)
class TeleporterEntranceFragment(Fragment):

    destination = None

    def _read_section_data(self, dbytes, sec):
        self.destination = dbytes.read_int(4)
        return False

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.destination is not None:
            p(f"Teleports to: {self.destination}")


@PROBER.fragment(MAGIC_2, 0x3f, 1)
class TeleporterExitFragment(Fragment):

    link_id = None

    def _read_section_data(self, dbytes, sec):
        self.link_id = dbytes.read_int(4)
        return False

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.link_id is not None:
            p(f"Link ID: {self.link_id}")


@PROBER.fragment(MAGIC_2, 0x51, 0)
class TeleporterExitCheckpointFragment(Fragment):

    trigger_checkpoint = 1

    def _read_section_data(self, dbytes, sec):
        if sec.data_size > 12:
            self.trigger_checkpoint = dbytes.read_byte()
        else:
            # if section is too short, the checkpoint is enabled
            self.trigger_checkpoint = 1
        return False

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.trigger_checkpoint is not None:
            p(f"Trigger checkpoint: {self.trigger_checkpoint}")


@PROBER.fragment(MAGIC_3, 0x0e, 1)
class SphereColliderFragment(Fragment):

    trigger_center = None
    trigger_radius = None

    def _read_section_data(self, dbytes, sec):
        self.trigger_center = (0.0, 0.0, 0.0)
        self.trigger_radius = 50.0
        with dbytes.limit(sec.data_end, True):
            self.trigger_center = read_n_floats(dbytes, 3, (0.0, 0.0, 0.0))
            self.trigger_radius = dbytes.read_struct(S_FLOAT)[0]
        return False


@PROBER.fragment(MAGIC_2, 0x45, 1)
class GravityToggleFragment(Fragment):

    disable_gravity = 1
    drag_scale = 1.0
    drag_scale_angular = 1.0

    def _read_section_data(self, dbytes, sec):
        with dbytes.limit(sec.data_end, True):
            self.disable_gravity = dbytes.read_byte()
            self.drag_scale = dbytes.read_struct(S_FLOAT)[0]
            self.drag_scale_angular = dbytes.read_struct(S_FLOAT)[0]
        return False

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if self.disable_gravity is not None:
            p(f"Disable gravity: {self.disable_gravity and 'yes' or 'no'}")
        if self.drag_scale is not None:
            p(f"Drag scale: {self.drag_scale}")
        if self.drag_scale_angular is not None:
            p(f"Angular drag scale: {self.drag_scale_angular}")


@PROBER.fragment(MAGIC_2, 0x16, 2)
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
        Fragment._print_data(self, p)
        if 'sections' in p.flags or 'track' in p.flags:
            p(f"Parent ID: {self.parent_id}")
            p(f"Snapped to: {self.snap_id}")
            p(f"Connection ID: {self.conn_id}")
            p(f"Primary: {self.primary and 'yes' or 'no'}")


@PROBER.fragment(MAGIC_3, 0x3, 1)
@PROBER.fragment(MAGIC_3, 0x3, 2)
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
        Fragment._print_data(self, p)
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
        Fragment._print_data(self, p)
        if 'allprops' in p.flags and self.props:
            self.props.print_data(p)


@PROBER.fragment(MAGIC_2, 0x5d, 0)
class RaceEndLogicFragment(NamedPropertiesFragment):

    @property
    def delay_before_broadcast(self):
        data = self.props.get('DelayBeforeBroadcast', SKIP_BYTES)
        if data != SKIP_BYTES:
            return S_FLOAT.unpack(data)[0]
        return None

    def _print_data(self, p):
        NamedPropertiesFragment._print_data(self, p)
        delay = self.delay_before_broadcast
        if delay:
            p(f"Delay before broadcast: {delay}")


@PROBER.fragment(MAGIC_2, 0x5e, 0)
class EnableAbilitiesTriggerFragment(NamedPropertiesFragment):

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

    @property
    def bloom_out(self):
        data = self.props.get('BloomOut', SKIP_BYTES)
        if not data or data == SKIP_BYTES:
            return 1
        return data[0]

    def _print_data(self, p):
        Fragment._print_data(self, p)
        ab_str = ', '.join(k for k, v in self.abilities.items() if v)
        if not ab_str:
            ab_str = "None"
        p(f"Abilities: {ab_str}")
        if self.bloom_out is not None:
            p(f"Bloom out: {self.bloom_out}")


PROPERTY_FRAGS = (
    (Section(MAGIC_2, 0x25, 0), "PopupBlockerLogic"),
    (Section(MAGIC_2, 0x42, 0), "ObjectSpawnCircle"),
    (Section(MAGIC_2, 0x39, 0), "ParticleEmitLogic"),
    (Section(MAGIC_2, 0x26, 0), "Light"),
    (Section(MAGIC_2, 0x27, 0), "PulseMaterial"),
    (Section(MAGIC_2, 0x28, 0), "SmoothRandomPosition"),
    (Section(MAGIC_2, 0x43, 0), "InterpolateToPositionOnTrigger"),
    (Section(MAGIC_2, 0x45, 0), None),
    (Section(MAGIC_2, 0x24, 0), "OldFlyingRingLogic"),
    (Section(MAGIC_2, 0x50, 0), "Pulse"),
    # found on Damnation
    (Section(22222222, 0x59, 0), None),
    (Section(22222222, 0x4b, 0), None),
    (Section(22222222, 0x4a, 0), None),
    (Section(22222222, 0x4e, 0), None),
    (Section(22222222, 0x57, 0), None),
    (Section(22222222, 0x3a, 0), None),
    (Section(22222222, 0x58, 0), None),
    (Section(22222222, 0x2c, 0), None),
    # found on Hextreme
    (Section(22222222, 0x1b, 0), None),
    # found on "Brief Chaos" object EmpireBrokenBuilding006_PiecesSeparated
    (Section(22222222, 0x44, 0), None),
    # from v5 AudioEventTrigger
    (Section(22222222, 0x74, 0), None),
    # from v5 CubeMIDI
    (Section(22222222, 0x3d, 0), None),
    # from v9 RumbleZone
    (Section(22222222, 0x66, 0), None),
    # from v8 PulseCore
    (Section(22222222, 0x4f, 0), None),
    # from v8 KillGridBox
    (Section(22222222, 0x82, 0), None),
    # from v5 WarpAnchor
    (Section(22222222, 0x6e, 0), None),
    # from v7 PlanetWithSphericalGravity
    (Section(22222222, 0x5f, 0), None),
    # from s8 (map "Pumpkin Patch")
    (Section(22222222, 0x29, 0), None), # from SoccerGoalLogic
    (Section(22222222, 0x38, 0), None), # from HalloweenSpotlight1, RotatingSpotLight
    # from v5 VirusSpiritShard
    (Section(22222222, 0x67, 0), None),
    # from v9 WingCorruptionZone
    (Section(22222222, 0x53, 0), None),
    # from v8 IntroCutsceneLight
    (Section(22222222, 0x55, 0), None),
    # from v9 CarScreenTextDecodeTrigger
    (Section(22222222, 0x57, 1), None),
    # from v9 CutsceneLightning
    (Section(22222222, 0x6f, 0), None),
    # from s8 (map "The Matrix Arena")
    (Section(22222222, 0x17, 0), None), # from EmpireCircle
    (Section(22222222, 0x1f, 0), None), # from Teleporter
    # from v3 WarningPulseLight
    (Section(22222222, 0x65, 0), None),
    # from v1 LaserMid (sub of VirusLaserTriCircleRotating)
    (Section(22222222, 0x1a, 0), None),
    # from v5 EmpireProximityDoor
    (Section(22222222, 0x76, 0), None),
    # from v5 VirusSpiritWarpTeaser
    (Section(22222222, 0x7e, 0), None),
    # from v1 GlobalFog
    (Section(22222222, 0x60, 0), None),
    # from v8 DisableLocalCarWarnings
    (Section(22222222, 0x62, 0), None),
    # from v7 AdventureAbilitySettings
    (Section(22222222, 0x4d, 0), None),
)


def _create_property_fragment_classes():
    globs = globals()
    created = set()
    sections = set()
    fragments_created = globs.get('_property_fragments_created', False)
    for sec, name in PROPERTY_FRAGS:
        key = sec.to_key()
        if key in sections:
            raise ValueError(f"Duplicate section: {sec}")
        sections.add(key)
        if name and name not in created:
            typename = name + "Fragment"
            if not fragments_created:
                if typename in globs:
                    raise ValueError(f"Fragment is already defined: {typename}")
            cls = type(typename, (NamedPropertiesFragment,), {
                '_frag_name': name,
            })
            created.add(name)
            globs[typename] = cls
    globs['_property_fragments_created'] = True


def add_property_fragments_to_prober(prober):
    globs = globals()
    for sec, name in PROPERTY_FRAGS:
        if name:
            typename = name + "Fragment"
        else:
            typename = "NamedPropertiesFragment"
        cls = globs[typename]
        prober.add_fragment(cls, sec)


_create_property_fragment_classes()
add_property_fragments_to_prober(PROBER)


def raise_attribute_error(obj, name):
    raise AttributeError(
        f"{type(obj).__name__!r} object has no attribute {name!r}")


class ForwardFragmentAttrs(object):

    forward_fragment_attrs = ()

    def __getattr__(self, name):
        for cls, attrs in self.forward_fragment_attrs:
            if name in attrs:
                try:
                    return getattr(self.fragment_by_type(cls), name)
                except AttributeError:
                    try:
                        return attrs[name]
                    except TypeError:
                        raise_attribute_error(self, name)
        try:
            return super().__getattr__(name)
        except AttributeError:
            pass
        raise_attribute_error(self, name)

    def __setattr__(self, name, value):
        for cls, attrs in self.forward_fragment_attrs:
            if name in attrs:
                setattr(self.fragment_by_type(cls), name, value)
                return
        super().__setattr__(name, value)


class ForwardFragmentColors(object):

    forward_fragment_colors = ()

    def _init_defaults(self):
        super()._init_defaults()

        mats = self.material_fragment.materials
        for matname, colname, value in self.forward_fragment_colors.values():
            mats.get_or_add(matname)[colname] = value

    def __getattr__(self, name):
        try:
            matname, colname, default = self.forward_fragment_colors[name]
        except KeyError:
            pass
        else:
            mats = self.material_fragment.materials
            mat = mats.get(matname, None)
            if mat is None:
                return None
            return mat.get(colname, None)

        try:
            return super().__getattr__(name)
        except AttributeError:
            pass
        raise_attribute_error(self, name)

    def __setattr__(self, name, value):
        try:
            matname, colname, default = self.forward_fragment_colors[name]
        except KeyError:
            pass
        else:
            mats = self.material_fragment.materials
            mats.get_or_add(matname)[colname] = value
            return

        super().__setattr__(name, value)

    @property
    def material_fragment(self):
        return self.fragment_by_type(MaterialFragment)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
