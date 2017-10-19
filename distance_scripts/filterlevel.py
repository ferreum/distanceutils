"""Filter objects from a level or CustomObject."""


import os
import sys
import argparse
import re
import collections

from distance.level import Level
from distance.levelobjects import Group, GoldenSimple, OldSimple
from distance.base import BaseObject
from distance.bytes import (
    DstBytes,
    MAGIC_2, MAGIC_3, MAGIC_32, MAGIC_9,
    Section,
)
from distance.printing import PrintContext
from distance.prober import BytesProber


PROBER = BytesProber()


PROBER.add_type('Group', Group)
PROBER.add_fragment(Level, MAGIC_9)

@PROBER.func
def _detect_other(section):
    return BaseObject


MAGICMAP = {2: MAGIC_2, 3: MAGIC_3, 32: MAGIC_32}


FILTERS = {}


class ObjectFilter(object):

    @classmethod
    def add_args(cls, parser):
        parser.add_argument("--maxrecurse", type=int, default=-1,
                            help="Maximum of recursions.")

    def __init__(self, name, args):
        self.name = name
        self.maxrecurse = args.maxrecurse

    def filter_object(self, obj):
        return obj,

    def filter_group(self, grp, levels):
        orig_empty = not grp.children
        grp.children = self.filter_objects(grp.children, levels)
        if not orig_empty and not grp.children:
            # remove empty group
            return ()
        return grp,

    def filter_any_object(self, obj, levels):
        if obj.is_object_group:
            if levels == 0:
                return obj,
            return self.filter_group(obj, levels - 1)
        else:
            return self.filter_object(obj)

    def filter_objects(self, objects, levels):
        res = []
        for obj in objects:
            res.extend(self.filter_any_object(obj, levels))
        return res

    def apply_level(self, level):
        for layer in level.layers:
            layer.objects = self.filter_objects(layer.objects, self.maxrecurse)

    def apply_group(self, grp):
        # not using filter_group, because we never want to remove the root
        # group object
        grp.children = self.filter_objects(grp.children, self.maxrecurse)

    def apply(self, content):
        if isinstance(content, Level):
            self.apply_level(content)
        elif isinstance(content, Group):
            self.apply_group(content)
        else:
            raise TypeError(f'Unknown object type: {type(content).__name__!r}')

    def post_filter(self, content):
        return True

    def print_summary(self, p):
        pass


class DoNotReplace(Exception):
    pass


class OldToGsMapper(object):

    def __init__(self, type, size_factor=1, offset=None, collision_only=False,
                 post_transform=None):
        self.type = type
        if not isinstance(size_factor, collections.Sequence):
            size_factor = (size_factor, size_factor, size_factor)
        self.size_factor = size_factor
        self.collision_only = collision_only
        self.offset = offset
        self.post_transform = post_transform

    def apply(self, obj):
        return self._apply_default(obj)

    def _apply_default(self, obj):
        collision = obj.type.endswith('WithCollision')
        emissive = obj.type.startswith('Emissive')
        if self.collision_only and not collision:
            raise DoNotReplace
        pos, rot, scale = obj.transform or ((), (), ())
        if not scale:
            scale = (1, 1, 1)
        if self.offset:
            if not pos:
                pos = (0, 0, 0)
            pos = tuple(p + q for p, q in zip(pos, self.offset(scale)))
        scale = tuple(s * f for s, f in zip(scale, self.size_factor))
        transform = pos, rot, scale
        if self.post_transform:
            transform = self.post_transform(transform)
        gs = GoldenSimple(type=self.type, transform=transform)
        if emissive:
            gs.mat_emit =  obj.color_emit
            gs.mat_reflect = (0, 0, 0, 0)
            gs.emit_index = 59
        else:
            gs.mat_color = obj.color_fixed_diffuse
            gs.image_index = 17
            gs.emit_index = 17
            gs.disable_bump = True
            gs.disable_diffuse = True
            gs.disable_reflect = True
        gs.mat_spec = (0, 0, 0, 0)
        gs.additive_transp = emissive
        gs.disable_collision = not collision
        return gs,


def create_simples_mappers():
    bugs = {
        'Cube': OldToGsMapper('CubeGS', size_factor=1/64, collision_only=True),
    }
    safe = {
        'Cube': OldToGsMapper('CubeGS', size_factor=1/64),
        'Plane': OldToGsMapper('PlaneOneSidedGS', size_factor=1/6.4),
        'Hexagon': OldToGsMapper('HexagonGS', size_factor=(1/32, .03, 1/32)),
        'Octahedron': OldToGsMapper('OctahedronGS', size_factor=1/32),
    }

    def make_post_rotate_x(alpha):
        def post_transform(transform):
            import numpy as np, quaternion
            from math import isclose, radians

            pos, rot, scale = transform
            if scale and not isclose(scale[1], scale[2]):
                # Cannot scale on these axes independently, because we need to
                # rotate our new object differently.
                raise DoNotReplace

            if not rot:
                rot = (0, 0, 0, 1)
            angle = radians(alpha)
            qrot = np.quaternion(rot[3], *rot[0:3])
            qrot *= np.quaternion(np.cos(angle/2), np.sin(angle/2), 0, 0)
            rot = (qrot.x, qrot.y, qrot.z, qrot.w)

            return pos, rot, scale
        return post_transform

    def make_transform_offset(offset, rotate, size_factor):
        def post_transform(transform):
            import numpy as np, quaternion
            from math import isclose, radians
            from distance.transform import rotpoint

            pos, rot, scale = transform
            if not rot:
                rot = (0, 0, 0, 1)
            if not pos:
                pos = (0, 0, 0)

            qrot = np.quaternion(rot[3], *rot[0:3])
            pos += rotpoint(qrot, offset(scale))

            qrot *= np.quaternion(*rotate)
            rot = (qrot.x, qrot.y, qrot.z, qrot.w)

            scale *= np.array(size_factor)

            return pos, rot, scale
        return post_transform

    from math import sin, cos, pi

    transform_pyramid = make_transform_offset(offset=(lambda scale: (0, scale[1] * 1.23914, 0)),
                                              rotate=(1, 0, 0, 0),
                                              size_factor=(.025898, .03867, .025898))

    transform_cone = make_transform_offset(offset=(lambda scale: (0, 0, 1.409 * scale[2])),
                                           rotate=(cos(pi/4), sin(pi/4), 0, 0),
                                           size_factor=(1/32, 1/21.33333, 1/32))

    inexact = {
        **safe,
        'Pyramid': OldToGsMapper('PyramidGS', post_transform=transform_pyramid),
        'Dodecahedron': OldToGsMapper('DodecahedronGS', size_factor=1/31.5412, # 1/31.5415..1/31.541
                                      post_transform=make_post_rotate_x(301.717)), # 301.715..301.72
        'Icosahedron': OldToGsMapper('IcosahedronGS', size_factor=.0312505, # 0.031250..0.031251
                                     post_transform=make_post_rotate_x(301.717)),
        'Ring': OldToGsMapper('RingGS', size_factor=.018679666), # 0.01867966..0.01867967
        'Tube': OldToGsMapper('TubeGS', size_factor=.02342865), # 0.0234286..0.0234287
    }
    pending = {
    }
    unsafe = {
        **inexact,
        **pending,
        'Sphere': OldToGsMapper('SphereGS', size_factor=1/63.5),
        'Cone': OldToGsMapper('ConeGS', post_transform=transform_cone),
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

    def __init__(self, name, args):
        super().__init__(name, args)
        self.mappers = OLD_TO_GOLD_SIMPLES_MAPPERS[args.mode]
        self.debug = args.debug
        self.num_replaced = 0

    def filter_object(self, obj):
        if isinstance(obj, OldSimple):
            typ = re.sub(r"^Emissive", '', obj.type)
            typ = re.sub(r"WithCollision$", '', typ)
            try:
                mapper = self.mappers[typ]
            except KeyError:
                # object not mapped in this mode
                return obj,
            try:
                result = mapper.apply(obj)
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

    def print_summary(self, p):
        p(f"Goldified simples: {self.num_replaced}")


FILTERS['goldify'] = GoldifyFilter


def parse_section(arg):
    parts = arg.split(",")
    magic = MAGICMAP[int(parts[0])]
    return Section(magic, *(int(p, base=0) for p in parts[1:]))


class RemoveFilter(ObjectFilter):

    @classmethod
    def add_args(cls, parser):
        super().add_args(parser)
        parser.add_argument("--type", action='append', default=[],
                            help="Match object type (regex).")
        parser.add_argument("--section", action='append', default=[],
                            help="Match sections.")
        parser.add_argument("--all", action='store_true',
                            help="Filter out all matching objects.")
        parser.add_argument("--number", dest='numbers', action='append',
                            type=int, default=[],
                            help="Select by candidate number.")

    def __init__(self, name, args):
        super().__init__(name, args)
        self.all = args.all
        self.numbers = args.numbers
        self.type_patterns = [re.compile(r) for r in args.type]
        self.sections = {parse_section(arg).to_key() for arg in args.section}
        self.num_matches = 0
        self.matches = []
        self.removed = []

    def _match_sections(self, obj):
        for sec in obj.sections:
            if sec.to_key() in self.sections:
                return True
        for child in obj.children:
            if self._match_sections(child):
                return True
        return False

    def match_props(self, obj):
        if not self.type_patterns and not self.sections:
            return True
        if self.type_patterns:
            typename = obj.type
            if any(r.search(typename) for r in self.type_patterns):
                return True
        if self.sections:
            if not obj.is_object_group and self._match_sections(obj):
                return True
        return False

    def match(self, obj):
        if self.match_props(obj):
            num = self.num_matches
            self.num_matches = num + 1
            self.matches.append(obj)
            if self.all:
                return True
            if num in self.numbers:
                return True
        return False

    def filter_any_object(self, obj, levels):
        remove = self.match(obj)
        res = super().filter_any_object(obj, levels)
        if remove:
            self.removed.append(obj)
            return ()
        return res

    def post_filter(self, content):
        if self.all or (self.numbers and self.matches):
            return True
        from .mkcustomobject import print_candidates
        print_candidates(self.matches)
        return False

    def print_summary(self, p):
        p(f"Removed matches: {len(self.removed)}")
        num_objs, num_groups = count_objects(self.removed)
        if num_objs != len(self.removed):
            p(f"Removed objects: {num_objs}")
            p(f"Removed groups: {num_groups}")


FILTERS['rm'] = RemoveFilter


def count_objects(objs):
    n_obj = 0
    n_grp = 0
    for obj in objs:
        n_obj += 1
        if obj.is_object_group:
            n_grp += 1
            no, ng = count_objects(obj.children)
            n_obj += no
            n_grp += ng
    return n_obj, n_grp


def make_arglist(s):

    def iter_tokens(source):
        if not source:
            return
        token = []
        escape = False
        for char in source:
            if escape:
                escape = False
                token.append(char)
            elif char == '\\':
                escape = True
            elif char == ':':
                yield token
                token = []
            else:
                token.append(char)
        yield token

    return ["--" + ''.join(token) for token in iter_tokens(s)]


def create_filter(option, defaults):
    name, sep, argstr = option.partition(':')
    cls = FILTERS[name]

    parser = argparse.ArgumentParser(prog=name)
    parser.set_defaults(**defaults)
    cls.add_args(parser)
    args = parser.parse_args(make_arglist(argstr))

    return cls(name, args)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-f", "--force", action='store_true',
                        help="Allow overwriting OUT file.")
    parser.add_argument("-l", "--maxrecurse", type=int, default=-1,
                        help="Maximum of recursions. 0 only lists layer objects.")
    parser.add_argument("-o", "--of", "--objfilter", dest='objfilters',
                        action='append', default=[],
                        help="Specify a filter option.")
    parser.add_argument("--list", action='store_true',
                        help="Dump result listing.")
    parser.add_argument("IN",
                        help="Level .bytes filename.")
    parser.add_argument("OUT",
                        help="output .bytes filename.")
    args = parser.parse_args()

    defaults = dict(maxrecurse=args.maxrecurse)
    filters = [create_filter(f, defaults) for f in args.objfilters]

    write_mode = 'xb'
    if args.force:
        write_mode = 'wb'
    elif os.path.exists(args.OUT):
        print(f"file {args.OUT} exists. pass -f to force.", file=sys.stderr)
        return 1

    content = PROBER.read(args.IN)

    p = PrintContext(flags=('groups', 'subobjects'))

    for f in filters:
        f.apply(content)
        if not f.post_filter(content):
            return 1
        f.print_summary(p)

    if args.list:
        p.print_data_of(content)

    print("generating...")
    dbytes = DstBytes.in_memory()
    content.write(dbytes)

    print("writing...")
    with open(args.OUT, write_mode) as out_f:
        n = out_f.write(dbytes.file.getbuffer())

    print(f"{n} bytes written")
    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
