

from distance.levelobjects import LevelObject, SubObject
from distance.bytes import Section, Magic
from distance.base import Transform, Fragment
from distance.classes import CollectorGroup, DefaultClasses
from distance.levelobjects import material_attrs


Classes = CollectorGroup()

fragment_attrs = DefaultClasses.fragments.fragment_attrs


@Classes.level_objects.object(
    'Teleporter',
    'TeleporterVirus',
    'TeleporterAndAmbientChangeTrigger',
    'TeleporterExit',
)
class Teleporter(LevelObject):

    default_transform = Transform.fill()


@Classes.level_subobjects.object
@fragment_attrs(
    'TeleporterEntrance',
    'TeleporterExit',
    'TeleporterExitCheckpoint',
)
class SubTeleporter(SubObject):

    type = 'Teleporter'


@Classes.level_subobjects.object
@fragment_attrs('RaceEndLogic')
class WinLogic(SubObject):

    type = 'WinLogic'


@Classes.level_objects.object
@fragment_attrs('TextMesh')
class WorldText(LevelObject):

    type = 'WorldText'


@Classes.level_objects.object
@fragment_attrs('InfoDisplayLogic')
class InfoDisplayBox(LevelObject):

    type = 'InfoDisplayBox'


@Classes.level_objects.object
@fragment_attrs('CarScreenTextDecodeTrigger')
class CarScreenTextDecodeTrigger(LevelObject):

    type = 'CarScreenTextDecodeTrigger'


@Classes.level_objects.object
@fragment_attrs('SphereCollider', 'GravityToggle', 'MusicTrigger')
class GravityTrigger(LevelObject):

    type = 'GravityTrigger'
    default_transform = Transform.fill()


@Classes.level_objects.object
@fragment_attrs('CustomName', 'ForceZone')
class ForceZoneBox(LevelObject):

    type = 'ForceZoneBox'
    default_transform = Transform.fill(scale=(35, 35, 35))


@Classes.level_objects.object
@fragment_attrs('EnableAbilitiesTrigger')
class EnableAbilitiesBox(LevelObject):

    type = 'EnableAbilitiesBox'
    default_transform = Transform.fill(scale=(100, 100, 100))


@Classes.level_objects.object('EventTriggerBox', 'EventTriggerSphere')
@fragment_attrs('EventTrigger')
class EventTrigger(LevelObject):

    default_transform = Transform.fill(scale=(35, 35, 35))


@Classes.level_objects.object
class WingCorruptionZone(LevelObject):

    type = 'WingCorruptionZone'
    default_transform = Transform.fill(scale=(100, 100, 100))


@Classes.level_objects.object
class WingCorruptionZoneLarge(LevelObject):

    type = 'WingCorruptionZoneLarge'
    default_transform = Transform.fill(scale=(1000, 1000, 1000))


@Classes.level_objects.object
class VirusSpiritSpawner(LevelObject):

    type = 'VirusSpiritSpawner'
    default_transform = Transform.fill()


@Classes.level_objects.object
class KillGridBox(LevelObject):

    type = 'KillGridBox'
    default_transform = Transform.fill(scale=(50, 50, 50))


@Classes.level_objects.object
class KillGridCylinder(LevelObject):

    type = 'KillGridCylinder'
    default_transform = Transform.fill(scale=(50, 50, 50))


@Classes.level_objects.object('CheckpointNoVisual', 'EmpireCheckpoint',
                              'EmpireCheckpointHalf')
class Checkpoint(LevelObject):

    default_transform = Transform.fill(rot=(0, 1, 0, 0), scale=14)


@Classes.level_objects.object('AbilityCheckpoint', 'AbilityCheckpointOLD')
class AbilityCheckpoint(LevelObject):

    default_transform = Transform.fill()


@Classes.level_objects.object
class NitronicCheckpoint(LevelObject):

    type = 'NitronicCheckpoint'
    default_transform = Transform.fill(scale=1.097)


@Classes.level_objects.object
class EmpirePowerFlyingRing(LevelObject):

    type = 'EmpirePowerFlyingRing'
    default_transform = Transform.fill(scale=1.5)


@Classes.level_objects.object
class EmpirePowerRoadRing(LevelObject):

    type = 'EmpirePowerRoadRing'
    default_transform = Transform.fill()


@Classes.level_objects.object
class CooldownTriggerNoVisual(LevelObject):

    type = 'CooldownTriggerNoVisual'
    default_transform = Transform.fill()


@Classes.level_objects.object(
    'VirusMazeTowerFat',
    'VirusMazeCeiling001',
    'VirusMazeTowerFat002',
    'VirusMazeTowerFat003',
    'EmpireMovingPillar',
)
class VirusMazeBuilding(LevelObject):

    default_transform = Transform.fill()


@Classes.level_objects.object
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


@fragment_attrs('GoldenSimples')
@material_attrs(
    mat_color = ('SimplesMaterial', '_Color', (.3, .3, .3, 1)),
    mat_emit = ('SimplesMaterial', '_EmitColor', (.8, .8, .8, .5)),
    mat_reflect = ('SimplesMaterial', '_ReflectColor', (.3, .3, .3, .9)),
    mat_spec = ('SimplesMaterial', '_SpecColor', (1, 1, 1, 1)),
)
@Classes.common.add_info(tag='GoldenSimple')
class GoldenSimple(LevelObject):

    default_transform = Transform.fill()

    def _init_defaults(self):
        super()._init_defaults()
        material_attrs.reset_colors(self)


for name in BASIC_GOLDEN_SIMPLES_NAMES:
    Classes.level_objects.add_object(name, GoldenSimple)
del name


class WedgeGS(GoldenSimple):
    type = 'WedgeGS'


@material_attrs(
    color_diffuse = ('Default-Diffuse', '_Color', (0.3, 0.3, 0.3, 1)),
    color_cone = ('Cone', '_Color', (0.3, 0.3, 0.3, 1)),
    color_emit = ('EmitDetail__ArchGrid', '_EmitColor', (0.2, 0.2, 0.2, 0.5))
)
@Classes.common.add_info(tag='OldSimple')
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
    Classes.level_objects.add_object(shape, OldSimple)
    Classes.level_objects.add_object('Emissive' + shape, OldSimple)
    Classes.level_objects.add_object(shape + 'WithCollision', OldSimple)
    Classes.level_objects.add_object('Emissive' + shape + 'WithCollision', OldSimple)
del shape



# vim:set sw=4 ts=8 sts=4 et:
