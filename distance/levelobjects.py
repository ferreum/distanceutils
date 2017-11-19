"""Level objects."""


from .bytes import (
    Section,
    MAGIC_2, MAGIC_3, MAGIC_6
)
from .base import Transform, BaseObject, Fragment, ForwardFragmentAttrs
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

    __slots__ = ()

    child_prober = SUBOBJ_PROBER
    fragment_prober = FRAG_PROBER

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
        if container and container.magic == MAGIC_6:
            type_str = container.type
            p(f"Subobject type: {type_str!r}")


@PROBER.for_type('Group')
@ForwardFragmentAttrs(GroupFragment, **GroupFragment.value_attrs)
@ForwardFragmentAttrs(CustomNameFragment, **CustomNameFragment.value_attrs)
class Group(LevelObject):

    child_prober = PROBER
    is_object_group = True
    type = 'Group'

    default_sections = (
        *LevelObject.default_sections,
        Section(MAGIC_2, 0x1d, version=1),
        Section(MAGIC_2, 0x63, version=0),
    )
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


@PROBER.for_type('Teleporter', 'TeleporterVirus',
                 'TeleporterAndAmbientChangeTrigger', 'TeleporterExit')
class Teleporter(LevelObject):

    default_transform = Transform.fill()


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
    default_transform = Transform.fill()


@PROBER.for_type('ForceZoneBox')
@ForwardFragmentAttrs(CustomNameFragment, **CustomNameFragment.value_attrs)
@ForwardFragmentAttrs(ForceZoneFragment, **ForceZoneFragment.value_attrs)
class ForceZoneBox(LevelObject):

    default_transform = Transform.fill(scale=(35, 35, 35))


@PROBER.for_type('EnableAbilitiesBox')
@ForwardFragmentAttrs(EnableAbilitiesTriggerFragment, abilities=None, bloom_out=None)
class EnableAbilitiesBox(LevelObject):

    default_transform = Transform.fill(scale=(100, 100, 100))


@PROBER.for_type('EventTriggerBox')
class EvenTriggerBox(LevelObject):

    default_transform = Transform.fill(scale=(35, 35, 35))


@PROBER.for_type('EventTriggerSphere')
class EvenTriggerSphere(LevelObject):

    default_transform = Transform.fill(scale=(35, 35, 35))


@PROBER.for_type('WingCorruptionZone')
class WingCorruptionZone(LevelObject):

    default_transform = Transform.fill(scale=(100, 100, 100))


@PROBER.for_type('WingCorruptionZoneLarge')
class WingCorruptionZoneLarge(LevelObject):

    default_transform = Transform.fill(scale=(1000, 1000, 1000))


@PROBER.for_type('VirusSpiritSpawner')
class VirusSpiritSpawner(LevelObject):

    default_transform = Transform.fill()


@PROBER.for_type('KillGridBox')
class KillGridBox(LevelObject):

    default_transform = Transform.fill(scale=(50, 50, 50))


@PROBER.for_type('KillGridCylinder')
class KillGridCylinder(LevelObject):

    default_transform = Transform.fill(scale=(50, 50, 50))


@PROBER.for_type('CheckpointNoVisual', 'EmpireCheckpoint',
                 'EmpireCheckpointHalf')
class Checkpoint(LevelObject):

    default_transform = Transform.fill(rot=(0, 1, 0, 0), scale=14)


@PROBER.for_type('AbilityCheckpoint', 'AbilityCheckpointOLD')
class AbilityCheckpoint(LevelObject):

    default_transform = Transform.fill()


@PROBER.for_type('NitronicCheckpoint')
class NitronicCheckpoint(LevelObject):

    default_transform = Transform.fill(scale=1.097)


@PROBER.for_type('EmpirePowerFlyingRing')
class EmpirePowerFlyingRing(LevelObject):

    default_transform = Transform.fill(scale=1.5)


@PROBER.for_type('EmpirePowerRoadRing')
class EmpirePowerRoadRing(LevelObject):

    default_transform = Transform.fill()


@PROBER.for_type('CooldownTriggerNoVisual')
class CooldownTriggerNoVisual(LevelObject):

    default_transform = Transform.fill()


@PROBER.for_type('VirusMazeTowerFat')
@PROBER.for_type('VirusMazeCeiling001')
@PROBER.for_type('VirusMazeTowerFat002')
@PROBER.for_type('VirusMazeTowerFat003')
@PROBER.for_type('EmpireMovingPillar')
class VirusMazeBuilding(LevelObject):

    default_transform = Transform.fill()


@PROBER.for_type('PlanetWithSphericalGravity')
class PlanetWithSphericalGravity(LevelObject):

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


@ForwardFragmentAttrs(GoldenSimplesFragment, **GoldenSimplesFragment.value_attrs)
@ForwardMaterialColors(
    mat_color = ('SimplesMaterial', '_Color', (.3, .3, .3, 1)),
    mat_emit = ('SimplesMaterial', '_EmitColor', (.8, .8, .8, .5)),
    mat_reflect = ('SimplesMaterial', '_ReflectColor', (.3, .3, .3, .9)),
    mat_spec = ('SimplesMaterial', '_SpecColor', (1, 1, 1, 1)),
)
class GoldenSimple(LevelObject):

    default_sections = (
        *LevelObject.default_sections,
        Section(MAGIC_3, 3, 2),
        Section(MAGIC_2, 0x83, 3),
    )
    default_transform = Transform.fill()

    def _init_defaults(self):
        super()._init_defaults()
        ForwardMaterialColors.reset_colors(self)


for name in BASIC_GOLDEN_SIMPLES_NAMES:
    PROBER.add_type(name, GoldenSimple)
del name


class WedgeGS(GoldenSimple):
    type = 'WedgeGS'


@ForwardMaterialColors(
    color_diffuse = ('Default-Diffuse', '_Color', (0.3, 0.3, 0.3, 1)),
    color_cone = ('Cone', '_Color', (0.3, 0.3, 0.3, 1)),
    color_emit = ('EmitDetail__ArchGrid', '_EmitColor', (0.2, 0.2, 0.2, 0.5))
)
class OldSimple(LevelObject):

    default_sections = (
        *LevelObject.default_sections,
        Section(MAGIC_3, 3, 2), # material
    )
    default_cone_transform = Transform.fill(rot=(2**.5/2, 0, 0, 2**.5/-2),
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
            sec = Section(MAGIC_3, 0x0f, 2)
            frag = Fragment(container=sec)
            # box collider fragment seems to be empty for simples
            frag.raw_data = b''
            self.fragments.append(frag)

    def _init_defaults(self):
        super()._init_defaults()
        ForwardMaterialColors.reset_colors(self)
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
    PROBER.add_type(shape, OldSimple)
    PROBER.add_type('Emissive' + shape, OldSimple)
    PROBER.add_type(shape + 'WithCollision', OldSimple)
    PROBER.add_type('Emissive' + shape + 'WithCollision', OldSimple)
del shape


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
