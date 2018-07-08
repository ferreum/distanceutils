"""Level objects."""


from .bytes import Section, Magic
from .base import Transform, BaseObject, Fragment, fragment_attrs
from .levelfragments import (
    material_attrs,
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
from .printing import need_counters
from .prober import BytesProber


class Probers(object):
    file = BytesProber()
    level_like = BytesProber()
    level_objects = BytesProber()
    level_subobjects = BytesProber()


class LevelObject(BaseObject):

    __slots__ = ()

    child_prober_name = 'level_subobjects'

    has_children = True

    def _print_children(self, p):
        if 'subobjects' in p.flags and self.children:
            num = len(self.children)
            p(f"Subobjects: {num}")
            with p.tree_children():
                for obj in self.children:
                    p.tree_next_child()
                    p.print_data_of(obj)


class SubObject(LevelObject):

    __slots__ = ()

    def _print_type(self, p):
        container = self.container
        if container and container.magic == Magic[6]:
            type_str = container.type
            p(f"Subobject type: {type_str!r}")


def print_objects(p, gen):
    counters = p.counters
    for obj in gen:
        p.tree_next_child()
        counters.num_objects += 1
        if 'numbers' in p.flags:
            p(f"Level object: {counters.num_objects}")
        p.print_data_of(obj)


@Probers.level_objects.for_type
@fragment_attrs(GroupFragment, **GroupFragment.value_attrs)
@fragment_attrs(CustomNameFragment, **CustomNameFragment.value_attrs)
class Group(LevelObject):

    child_prober_name = 'level_objects'
    is_object_group = True
    type = 'Group'

    default_transform = Transform.fill()

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
        import numpy as np, quaternion
        from distance.transform import rotpointrev
        quaternion # suppress warning

        pos, rot, scale = self.transform
        self.transform = self.transform.set(pos=center)

        diff = tuple(c - o for c, o in zip(pos, center))
        qrot = np.quaternion(rot[3], *rot[:3])
        diff = rotpointrev(qrot, diff)

        for obj in self.children:
            pos = obj.transform.pos + diff
            obj.transform = obj.transform.set(pos=pos)

    def rerotate(self, rot):
        import numpy as np, quaternion
        from distance.transform import rotpoint
        quaternion # suppress warning

        orot = self.transform.rot
        self.transform = self.transform.set(rot=rot)

        qrot = np.quaternion(rot[3], *rot[:3])
        qorot = np.quaternion(orot[3], *orot[:3])

        diff = qorot / qrot
        for obj in self.children:
            pos, orot, scale = obj.transform
            qorot = diff * np.quaternion(orot[3], *orot[:3])
            nrot = (*qorot.imag, qorot.real)
            if pos:
                pos = rotpoint(diff, pos)
            obj.transform = Transform(pos, nrot, scale)

    def rescale(self, scale):
        import numpy as np

        old = self.transform
        self.transform = old.set(scale=scale)

        inverse = np.array(old.scale) / scale
        invtr = Transform.fill(scale=inverse)
        for obj in self.children:
            obj.transform = invtr.apply(*obj.transform)


@Probers.level_objects.for_type('Teleporter', 'TeleporterVirus',
                                'TeleporterAndAmbientChangeTrigger', 'TeleporterExit')
class Teleporter(LevelObject):

    default_transform = Transform.fill()


@Probers.level_subobjects.for_type
@fragment_attrs(BaseTeleporterEntrance, destination=None)
@fragment_attrs(BaseTeleporterExit, link_id=None)
@fragment_attrs(TeleporterExitCheckpointFragment, trigger_checkpoint=None)
class SubTeleporter(SubObject):
    type = 'Teleporter'


@Probers.level_subobjects.for_type
@fragment_attrs(RaceEndLogicFragment, delay_before_broadcast=None)
class WinLogic(SubObject):
    type = 'WinLogic'


@Probers.level_objects.for_type
@fragment_attrs(TextMeshFragment, **TextMeshFragment._fields_map)
class WorldText(LevelObject):
    type = 'WorldText'


@Probers.level_objects.for_type
@fragment_attrs(BaseInfoDisplayLogic,
    fadeout_time = None,
    texts = (),
    per_char_speed = None,
    destroy_on_trigger_exit = None,
    random_char_count = None,
)
class InfoDisplayBox(LevelObject):

    type = 'InfoDisplayBox'


@Probers.level_objects.for_type
@fragment_attrs(BaseCarScreenTextDecodeTrigger,
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

    type = 'CarScreenTextDecodeTrigger'


@Probers.level_objects.for_type
@fragment_attrs(SphereColliderFragment,
    trigger_center = None,
    trigger_radius = None,
)
@fragment_attrs(GravityToggleFragment,
    disable_gravity = None,
    drag_scale = None,
    drag_scale_angular = None,
)
@fragment_attrs(MusicTriggerFragment,
    music_id = None,
    one_time_trigger = None,
    reset_before_trigger = None,
    disable_music_trigger = None,
)
class GravityTrigger(LevelObject):

    type = 'GravityTrigger'
    default_transform = Transform.fill()


@Probers.level_objects.for_type
@fragment_attrs(CustomNameFragment, **CustomNameFragment.value_attrs)
@fragment_attrs(ForceZoneFragment, **ForceZoneFragment._fields_map)
class ForceZoneBox(LevelObject):

    type = 'ForceZoneBox'
    default_transform = Transform.fill(scale=(35, 35, 35))


@Probers.level_objects.for_type
@fragment_attrs(EnableAbilitiesTriggerFragment, abilities=None, bloom_out=None,
                      enable_boosting=0, enable_jumping=0, enable_jets=0, enable_flying=0)
class EnableAbilitiesBox(LevelObject):

    type = 'EnableAbilitiesBox'
    default_transform = Transform.fill(scale=(100, 100, 100))


@Probers.level_objects.for_type
class EvenTriggerBox(LevelObject):

    type = 'EventTriggerBox'
    default_transform = Transform.fill(scale=(35, 35, 35))


@Probers.level_objects.for_type
class EvenTriggerSphere(LevelObject):

    type = 'EventTriggerSphere'
    default_transform = Transform.fill(scale=(35, 35, 35))


@Probers.level_objects.for_type
class WingCorruptionZone(LevelObject):

    type = 'WingCorruptionZone'
    default_transform = Transform.fill(scale=(100, 100, 100))


@Probers.level_objects.for_type
class WingCorruptionZoneLarge(LevelObject):

    type = 'WingCorruptionZoneLarge'
    default_transform = Transform.fill(scale=(1000, 1000, 1000))


@Probers.level_objects.for_type
class VirusSpiritSpawner(LevelObject):

    type = 'VirusSpiritSpawner'
    default_transform = Transform.fill()


@Probers.level_objects.for_type
class KillGridBox(LevelObject):

    type = 'KillGridBox'
    default_transform = Transform.fill(scale=(50, 50, 50))


@Probers.level_objects.for_type
class KillGridCylinder(LevelObject):

    type = 'KillGridCylinder'
    default_transform = Transform.fill(scale=(50, 50, 50))


@Probers.level_objects.for_type('CheckpointNoVisual', 'EmpireCheckpoint',
                                'EmpireCheckpointHalf')
class Checkpoint(LevelObject):

    default_transform = Transform.fill(rot=(0, 1, 0, 0), scale=14)


@Probers.level_objects.for_type('AbilityCheckpoint', 'AbilityCheckpointOLD')
class AbilityCheckpoint(LevelObject):

    default_transform = Transform.fill()


@Probers.level_objects.for_type
class NitronicCheckpoint(LevelObject):

    type = 'NitronicCheckpoint'
    default_transform = Transform.fill(scale=1.097)


@Probers.level_objects.for_type
class EmpirePowerFlyingRing(LevelObject):

    type = 'EmpirePowerFlyingRing'
    default_transform = Transform.fill(scale=1.5)


@Probers.level_objects.for_type
class EmpirePowerRoadRing(LevelObject):

    type = 'EmpirePowerRoadRing'
    default_transform = Transform.fill()


@Probers.level_objects.for_type
class CooldownTriggerNoVisual(LevelObject):

    type = 'CooldownTriggerNoVisual'
    default_transform = Transform.fill()


@Probers.level_objects.for_type(
    'VirusMazeTowerFat',
    'VirusMazeCeiling001',
    'VirusMazeTowerFat002',
    'VirusMazeTowerFat003',
    'EmpireMovingPillar',
)
class VirusMazeBuilding(LevelObject):

    default_transform = Transform.fill()


@Probers.level_objects.for_type
class PlanetWithSphericalGravity(LevelObject):

    type = 'PlanetWithSphericalGravity'
    default_transform = Transform.fill(scale=2.5)


BASIC_GOLDEN_SIMPLES_NAMES = (
    'AppleGS',
    'ArchGS',
    'ArchQuarterGS',
    'CapsuleGS',
    'CheeseGS',
    'CircleFrustumGS',
    'ConeGS',
    'CubeGS',
    'CylinderGS',
    'CylinderHDGS',
    'DodecahedronGS',
    'FrustumGS',
    'HemisphereGS',
    'HexagonGS',
    'IcosahedronGS',
    'IrregularCapsule1GS',
    'IrregularCapsule2GS',
    'IrregularConeGS',
    'IrregularCubeGS',
    'IrregularCylinderGS',
    'IrregularDodecahedronGS',
    'IrregularFlatDropGS 1',
    'IrregularHexagonGS',
    'IrregularIcosahedronGS',
    'IrregularOctahedronGS',
    'IrregularPlaneGS',
    'IrregularPyramid001GS',
    'IrregularPyramid002GS',
    'IrregularRectangle001GS',
    'IrregularRectangle002GS',
    'IrregularRectangle003GS',
    'IrregularRectangle004GS',
    'IrregularRingGS',
    'IrregularSphere001GS',
    'IrregularSphere002GS',
    'IrregularTeardropGS',
    'IrregularTube001GS',
    'IrregularTube002GS',
    'OctahedronGS',
    'PeanutGS',
    'PentagonGS',
    'PlaneGS',
    'PlaneOneSidedGS',
    'PointyGS',
    'PyramidGS',
    'QuadGS',
    'RingGS',
    'RingHalfGS',
    'Rock1GS',
    'Rock2GS',
    'Rock3GS',
    'SphereGS',
    'SphereHDGS',
    'TeardropGS',
    'TetrahedronGS',
    'TrapezoidGS',
    'TubeGS',
    'WedgeGS',
)


@fragment_attrs(GoldenSimplesFragment, **GoldenSimplesFragment._fields_map)
@material_attrs(
    mat_color = ('SimplesMaterial', '_Color', (.3, .3, .3, 1)),
    mat_emit = ('SimplesMaterial', '_EmitColor', (.8, .8, .8, .5)),
    mat_reflect = ('SimplesMaterial', '_ReflectColor', (.3, .3, .3, .9)),
    mat_spec = ('SimplesMaterial', '_SpecColor', (1, 1, 1, 1)),
)
class GoldenSimple(LevelObject):

    default_transform = Transform.fill()

    def _init_defaults(self):
        super()._init_defaults()
        material_attrs.reset_colors(self)


for name in BASIC_GOLDEN_SIMPLES_NAMES:
    Probers.level_objects.add_type(name, GoldenSimple)
del name


class WedgeGS(GoldenSimple):
    type = 'WedgeGS'


@material_attrs(
    color_diffuse = ('Default-Diffuse', '_Color', (0.3, 0.3, 0.3, 1)),
    color_cone = ('Cone', '_Color', (0.3, 0.3, 0.3, 1)),
    color_emit = ('EmitDetail__ArchGrid', '_EmitColor', (0.2, 0.2, 0.2, 0.5))
)
class OldSimple(LevelObject):

    default_cone_transform = Transform.fill(rot=(2**.5 / 2, 0, 0, 2**.5 / -2),
                                            scale=(.5, .5, .5))
    default_other_transform = Transform.fill()

    @property
    def default_transform(self):
        if self.shape in ('Cone', 'TrueCone'):
            return self.default_cone_transform
        return self.default_other_transform

    def _after_init(self):
        super()._after_init()
        if self.emissive:
            del self.color_diffuse
            del self.color_cone
        else:
            del self.color_emit
            if self.shape != 'Cone':
                del self.color_cone
        if self.with_collision:
            sec = Section(Magic[3], 0x0f, 2)
            frag = Fragment(container=sec)
            # box collider fragment seems to be empty for simples
            frag.raw_data = b''
            self.fragments.append(frag)

    def _init_defaults(self):
        super()._init_defaults()
        material_attrs.reset_colors(self)
        self.type = 'Cube'

    @property
    def split_type(self):
        emit, coll = "", ""
        typ = self.type
        if typ.startswith('Emissive'):
            emit = 'Emissive'
            typ = typ[8:]
        if typ.endswith('WithCollision'):
            coll = 'WithCollision'
            typ = typ[:-13]
        return emit, typ, coll

    @split_type.setter
    def split_type(self, split):
        self.type = ''.join(split)

    @property
    def emissive(self):
        return self.type.startswith('Emissive')

    @emissive.setter
    def emissive(self, value):
        old, typ, coll = self.split_type
        self.split_type = value and 'Emissive' or '', typ, coll

    @property
    def with_collision(self):
        return self.type.endswith("WithCollision")

    @with_collision.setter
    def with_collision(self, value):
        emit, typ, old = self.split_type
        self.split_type = emit, typ, value and 'WithCollision' or ''

    @property
    def shape(self):
        return self.split_type[1]

    @shape.setter
    def shape(self, value):
        emit, old, coll = self.split_type
        self.split_type = emit, value, coll

    @property
    def color_fixed_diffuse(self):
        """Get the diffuse color, but for opaque Cones return the 'Cone' color."""
        if self.shape == 'Cone':
            return self.color_cone
        else:
            return self.color_diffuse

    @color_fixed_diffuse.setter
    def color_fixed_diffuse(self, value):
        if self.shape == 'Cone':
            self.color_cone = value
        else:
            self.color_diffuse = value

    @color_fixed_diffuse.deleter
    def color_fixed_diffuse(self):
        if self.shape == 'Cone':
            del self.color_cone
        else:
            del self.color_diffuse


OLD_SIMPLES_SHAPES = (
    'Capsule',
    'Cone',
    'Cube',
    'Cylinder',
    'CylinderTapered',
    'Dodecahedron',
    'FlatDrop',
    'Hexagon',
    'Icosahedron',
    'IrregularCapsule001',
    'IrregularCapsule002',
    'IrregularFlatDrop',
    'Octahedron',
    'Plane',
    'Pyramid',
    'Ring',
    'RingHalf',
    'Sphere',
    'Teardrop',
    'TrueCone',
    'Tube',
    'Wedge',
)

for shape in OLD_SIMPLES_SHAPES:
    Probers.level_objects.add_type(shape, OldSimple)
    Probers.level_objects.add_type('Emissive' + shape, OldSimple)
    Probers.level_objects.add_type(shape + 'WithCollision', OldSimple)
    Probers.level_objects.add_type('Emissive' + shape + 'WithCollision', OldSimple)
del shape


Probers.level_like.baseclass = LevelObject
Probers.level_objects.baseclass = LevelObject
Probers.level_subobjects.baseclass = SubObject

# Add everything to level_like and file prober too.
Probers.level_like.extend_from(Probers.level_objects)
Probers.file.extend_from(Probers.level_objects)


# vim:set sw=4 ts=8 sts=4 et:
