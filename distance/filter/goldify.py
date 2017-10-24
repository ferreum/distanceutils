"""Filter for replacing old simples with golden simples"""


from distance.levelobjects import GoldenSimple, OldSimple
from .base import ObjectFilter, ObjectMapper, DoNotReplace


class OldToGsMapper(ObjectMapper):

    def __init__(self, type, **kw):
        super().__init__(**kw)
        self.type = type

    def create_result(self, old, transform):
        gs = GoldenSimple(type=self.type, transform=transform)
        if old.emissive:
            gs.mat_emit =  old.color_emit
            gs.mat_reflect = (0, 0, 0, 0)
            gs.emit_index = 42
            gs.tex_scale = (-.175, .5, 1)
            gs.tex_offset = (0, .125, 0)
        else:
            gs.mat_color = old.color_fixed_diffuse
            gs.image_index = 17
            gs.emit_index = 17
            gs.disable_bump = True
            gs.disable_diffuse = True
            gs.disable_reflect = True
        gs.mat_spec = (0, 0, 0, 0)
        gs.additive_transp = old.emissive
        gs.disable_collision = not old.with_collision
        return gs,


def create_simples_mappers():
    from math import sin, cos, sqrt, radians
    def mkrotx(degrees):
        rads = radians(degrees)
        return (cos(rads/2), sin(rads/2), 0, 0)
    def factor_ringhalf(scale):
        s = .0161605
        return (scale[2] * s, scale[1] * s, scale[0] * s)
    rot_y90 = (cos(radians(90)/2), 0, sin(radians(90)/2), 0)

    bugs = {
        'Cube': OldToGsMapper('CubeGS', size_factor=1/64, collision_only=True),
    }
    safe = {
        'Cube': OldToGsMapper('CubeGS', size_factor=1/64),
        'Hexagon': OldToGsMapper('HexagonGS', size_factor=(1/32, .03, 1/32)),
        'Octahedron': OldToGsMapper('OctahedronGS', size_factor=1/32),
    }
    inexact = {
        **safe,
        'Pyramid': OldToGsMapper('PyramidGS',
                                 offset=(0, 1.2391397, 0), # 1.2391395..1.2391398
                                 # x,z: 0.0258984..0.02589845
                                 size_factor=(.02589842, 7/128/sqrt(2), .02589842)),
        'Dodecahedron': OldToGsMapper('DodecahedronGS',
                                      rotate=mkrotx(301.7171), # 301.717..301.7172
                                      size_factor=0.0317045, # 0.0317042..0.0317047
                                      locked_scale_axes=(1, 2)),
        'Icosahedron': OldToGsMapper('IcosahedronGS',
                                     rotate=mkrotx(301.7171),
                                     size_factor=.0312505, # 0.031250..0.031251
                                     locked_scale_axes=(1, 2)),
        'Ring': OldToGsMapper('RingGS', size_factor=.018679666), # 0.01867966..0.01867967
        'RingHalf': OldToGsMapper('RingHalfGS',
                                  offset=(0, 0.29891, 0),
                                  rotate=rot_y90,
                                  size_factor=factor_ringhalf),
        'Teardrop': OldToGsMapper('TeardropGS',
                                  size_factor=0.0140161),
        'Tube': OldToGsMapper('TubeGS', size_factor=.02342865), # 0.0234286..0.0234287
        'IrregularCapsule001': OldToGsMapper('IrregularCapsule1GS',
                                             size_factor=0.01410507), #0.01410506..0.01410508
        'IrregularCapsule002': OldToGsMapper('IrregularCapsule2GS',
                                             size_factor=0.01410507), #0.01410506..0.01410508
    }

    def factor_wedge(scale):
        xz = 3/160
        y = .016141797 # 0.016141795..0.016141798
        return (scale[2] * xz, scale[1] * y, scale[0] * xz)

    def factor_cone(scale):
        return (scale[0] * 1/32, scale[2] * 3/64, scale[1] * 1/32)

    def factor_truecone(scale):
        s = .03125
        return (scale[0] * s, scale[2] * s, scale[1] * s)

    pending = {
    }
    unsafe = {
        **inexact,
        **pending,
        'Sphere': OldToGsMapper('SphereGS', size_factor=1/63.5),
        'Cone': OldToGsMapper('ConeGS',
                              offset=(0, 0, 1.409),
                              rotate=mkrotx(90),
                              size_factor=factor_cone,
                              default_rotation=mkrotx(270),
                              default_scale=(.5, .5, .5)),
        'Cylinder': OldToGsMapper('CylinderGS',
                                  size_factor=(.014, 3/128, .014)),
        'Wedge': OldToGsMapper('WedgeGS',
                               rotate=rot_y90,
                               size_factor=factor_wedge),
        'TrueCone': OldToGsMapper('ConeGS',
                                  rotate=mkrotx(90),
                                  size_factor=factor_truecone,
                                  default_rotation=mkrotx(270),
                                  default_scale=(.5, .5, .5)),
        'Plane': OldToGsMapper('PlaneGS', size_factor=1/6.4),
    }
    return dict(bugs=bugs, safe=safe, pending=pending, inexact=inexact, unsafe=unsafe)

OLD_TO_GOLD_SIMPLES_MAPPERS = create_simples_mappers()


class GoldifyFilter(ObjectFilter):

    @classmethod
    def add_args(cls, parser):
        super().add_args(parser)
        parser.add_argument("--debug", action='store_true')
        grp = parser.add_mutually_exclusive_group()
        grp.add_argument("--bugs", action='store_const', const="bugs", dest='mode',
                         help="Replace glitched simples (CubeWithCollision).")
        grp.add_argument("--safe", action='store_const', const="safe", dest='mode',
                         help="Do all safe (exact) replacements (default).")
        grp.add_argument("--inexact", action='store_const', const="inexact", dest='mode',
                         help="Include replacements with imperfect precision.")
        grp.add_argument("--pending", action='store_const', const="pending", dest='mode',
                         help="Only use unfinished implementations (debug).")
        grp.add_argument("--unsafe", action='store_const', const="unsafe", dest='mode',
                         help="Do all replacements.")
        grp.set_defaults(mode='safe')

    def __init__(self, args):
        super().__init__("goldify", args)
        self.mappers = OLD_TO_GOLD_SIMPLES_MAPPERS[args.mode]
        self.debug = args.debug
        self.num_replaced = 0

    def filter_object(self, obj, scaled_group=False):
        if isinstance(obj, OldSimple):
            try:
                mapper = self.mappers[obj.shape]
            except KeyError:
                # object not mapped in this mode
                return obj,
            try:
                result = mapper.apply(obj, scaled_group=scaled_group)
            except DoNotReplace:
                return obj,
            self.num_replaced += 1
            if self.debug:
                for res in result:
                    if res.additive_transp:
                        res.mat_emit = (1, .3, .3, .4)
                    else:
                        res.mat_color = (1, .3, .3, 1)
                return result + (obj,)
            return result
        return obj,

    def filter_group(self, grp, level, **kw):
        if not kw.get('scaled_group', False):
            pos, rot, scale = grp.transform or ((), (), ())
            if scale:
                from math import isclose
                v1 = scale[0]
                for v in scale[1:]:
                    if not isclose(v, v1):
                        kw['scaled_group'] = True
                        break
        return super().filter_group(grp, level, **kw)

    def print_summary(self, p):
        p(f"Goldified simples: {self.num_replaced}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
