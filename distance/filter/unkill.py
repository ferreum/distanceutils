"""Filter for replacing kill grids."""


from distance.levelfragments import MaterialFragment
from distance.levelobjects import GoldenSimple
from .base import ObjectFilter, ObjectMapper, DoNotApply


class KillgridMapper(ObjectMapper):

    def __init__(self, type, **kw):
        super().__init__(**kw)
        self.type = type

    def create_result(self, old, transform, collision=True, copy_color=True):
        gs = GoldenSimple(type=self.type, transform=transform)
        color = (.302, 0, 0, .471)
        if copy_color:
            try:
                matfragment = old.fragment_by_type(MaterialFragment)
                color = matfragment.materials['KillGridFinite']['_Color']
            except AttributeError:
                pass
        color = color[:3] + (color[3] * .5,)
        gs.mat_emit = color
        gs.mat_reflect = (0, 0, 0, 0)
        gs.mat_spec = (0, 0, 0, 0)
        gs.emit_index = 38
        gs.tex_scale = (2, 2, 2)
        gs.world_mapped = True
        gs.additive_transp = True
        gs.disable_reflect = True
        gs.disable_collision = not collision
        return gs,


def create_mappers():
    from math import sin, cos, radians
    def mkrotx(degrees):
        rads = radians(degrees)
        return (cos(rads/2), sin(rads/2), 0, 0)

    def scale_cylinder(scale):
        s = 1/64
        return (scale[0] * s, scale[2] * s, scale[1] * s)

    return {
        'KillGridBox': KillgridMapper('CubeGS', size_factor=1/64,
                                      default_scale=(50, 50, 50)),
        'KillGridCylinder': KillgridMapper('CylinderGS',
                                           size_factor=scale_cylinder,
                                           rotate=mkrotx(90),
                                           default_scale=(50, 50, 50)),
    }

KILLGRID_MAPPERS = create_mappers()


class UnkillFilter(ObjectFilter):

    @classmethod
    def add_args(cls, parser):
        super().add_args(parser)
        parser.add_argument("--debug", action='store_true')
        parser.add_argument("--nocolor", dest='color',
                            action='store_false',
                            help="Use default kill grid color.")
        parser.add_argument("--color", dest='color',
                            action='store_true',
                            help="Copy kill grid color (default).")
        parser.add_argument("--collision", dest='collision',
                            action='store_true', default=True,
                            help="Enable simples collision (default).")
        parser.add_argument("--nocollision", dest='collision',
                            action='store_false',
                            help="Disable simples collision.")

    def __init__(self, args):
        super().__init__("unkill", args)
        self.collision = args.collision
        self.debug = args.debug
        self.color = args.color
        self.num_replaced = 0

    def filter_object(self, obj):
        try:
            mapper = KILLGRID_MAPPERS[obj.type]
        except KeyError:
            return obj,
        try:
            result = mapper.apply(obj, collision=self.collision,
                                  copy_color=self.color)
        except DoNotApply:
            return obj,
        self.num_replaced += 1
        if self.debug:
            return result + (obj,)
        return result

    def print_summary(self, p):
        p(f"Replaced kill grids: {self.num_replaced}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
