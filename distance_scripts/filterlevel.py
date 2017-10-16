"""Filter objects from a level or CustomObject."""


import os
import sys
import argparse
import re

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

    def __init__(self, name):
        self.name = name

    def filter_object(self, obj):
        return obj,

    def filter_group(self, grp):
        grp.children = self.filter_objects(grp.children)
        if not grp.children:
            # remove empty group
            return ()
        return grp,

    def filter_objects(self, objects):
        res = []
        for obj in objects:
            if obj.is_object_group:
                res.extend(self.filter_group(obj))
            else:
                res.extend(self.filter_object(obj))
        return res

    def apply_level(self, level):
        for layer in level.layers:
            layer.objects = self.filter_objects(layer.objects)

    def apply_group(self, grp):
        # not using filter_group, because we never want to remove the root
        # group object
        grp.children = self.filter_objects(grp.children)

    def apply(self, content):
        if isinstance(content, Level):
            self.apply_level(content)
        elif isinstance(content, Group):
            self.apply_group(grp)
        else:
            raise TypeError(f'Unknown object type: {type(content).__name__!r}')


OLD_TO_GOLD_SIMPLES_MAP = {

    # 'Capsule': 'CapsuleGS',

    # 'Cone': 'ConeGS',

    'Cube': 'CubeGS',

    # 'Cylinder': 'CylinderGS',

    # # # center point is different
    # # 'CylinderTapered': 'CircleFrustumGS',

    # # different rotation
    # 'Dodecahedron': 'DodecahedronGS',

    # # # no match
    # # 'FlatDrop': 'CheeseGS',

    # 'Hexagon': 'HexagonGS',

    # # different rotation
    # 'Icosahedron': 'IcosahedronGS',

    # # # different scale
    # # 'IrregularCapsule002': 'IrregularCapsule2GS',

    # # # differnt rotation/scale
    # # 'IrregularFlatDrop': 'IrregularDodecahedronGS',

    # 'Octahedron': 'OctahedronGS',

    # 'Plane': 'PlaneGS',

    # # different center, distorted
    # 'Pyramid': 'PyramidGS',

    # 'Ring': 'RingGS',

    # # 'RingHalf': 'RingHalfGS',

    # # different rotation
    # 'Sphere': 'SphereGS',

    # # 'Teardrop': 'TeardropGS',

    # # 'TrueCone',

    # 'Tube': 'TubeGS',

    # # different rotation/shape
    # 'Wedge': 'WedgeGS',

}


class GoldifyFilter(ObjectFilter):

    def __init__(self, name, args=''):
        super().__init__(name)

    def filter_object(self, obj):
        if isinstance(obj, OldSimple):
            pos, rot, scale = obj.transform
            if not scale:
                scale = (1, 1, 1)
            scale = tuple(s / 64 for s in scale)
            transform = pos, rot, scale
            typ = re.sub(r"^Emissive", '', obj.type)
            typ = re.sub(r"WithCollision$", '', typ)
            try:
                typ = OLD_TO_GOLD_SIMPLES_MAP[typ]
            except KeyError:
                # leave unimplemented alone
                return obj,
            gs = GoldenSimple(type=typ, transform=transform)
            emissive = obj.type.startswith('Emissive')
            if emissive:
                # gs.mat_emit = (.8, .1, .6, .3) # obj.color_emit
                gs.mat_emit =  obj.color_emit
                gs.mat_reflect = (0, 0, 0, 0)
                gs.emit_index = 59
            else:
                gs.mat_color = obj.color_diffuse
                gs.image_index = 17
                gs.emit_index = 17
                gs.disable_bump = True
                gs.disable_diffuse = True
                gs.disable_reflect = True
            gs.mat_spec = (0, 0, 0, 0)
            gs.additive_transp = emissive
            gs.disable_collision = not obj.type.endswith('WithCollision')
            return gs,
        return obj,

FILTERS['goldify'] = GoldifyFilter


def parse_section(arg):
    parts = arg.split(",")
    magic = MAGICMAP[int(parts[0])]
    return Section(magic, *(int(p, base=0) for p in parts[1:]))


class ObjectMatcher(object):

    def __init__(self, args):
        self.all = args.all
        self.numbers = args.numbers
        self.type_patterns = [re.compile(r) for r in args.type]
        self.maxrecurse = args.maxrecurse
        self.num_matches = 0
        self.matches = []
        self.sections = {parse_section(arg).to_key() for arg in args.section}

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

    def _filter_objects(self, objs, recurse):
        result = []
        for obj in objs:
            remove = False
            if self.match(obj):
                remove  = True
            if obj.is_object_group and recurse != 0:
                obj.children = self._filter_objects(obj.children, recurse - 1)
                if not obj.children:
                    # remove empty group
                    self.matches.append(obj)
                    remove = True
            if not remove:
                result.append(obj)
        return result

    def filter_objects(self, objs):
        return self._filter_objects(objs, self.maxrecurse)

    def filter_level(self, level):
        for layer in level.layers:
            layer.objects = self.filter_objects(layer.objects)
        return level


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


def create_filter(option):
    typ, sep, rem = option.partition(':')
    cls = FILTERS[typ]
    return cls(typ, args=rem)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-f", "--force", action='store_true',
                        help="Allow overwriting OUT file.")
    parser.add_argument("-n", "--number", dest='numbers', action='append',
                        type=int, default=[],
                        help="Select by candidate number.")
    parser.add_argument("-a", "--all", action='store_true',
                        help="Filter out all matching objects.")
    parser.add_argument("-l", "--maxrecurse", type=int, default=-1,
                        help="Maximum of recursions. 0 only lists layer objects.")
    parser.add_argument("-t", "--type", action='append', default=[],
                        help="Match object type (regex).")
    parser.add_argument("-s", "--section", action='append', default=[],
                        help="Match sections.")
    parser.add_argument("-o", "--of", "--objfilter", dest='objfilters',
                        action='append', default=[],
                        help="Specify a filter option.")
    parser.add_argument("--list", action='store_true',
                        help="Print list of written objects.")
    parser.add_argument("IN",
                        help="Level .bytes filename.")
    parser.add_argument("OUT",
                        help="output .bytes filename.")
    args = parser.parse_args()

    filters = [create_filter(f) for f in args.objfilters]

    do_write = filters or args.force or args.all or bool(args.numbers)
    if do_write:
        write_mode = 'xb'
        if args.force:
            write_mode = 'wb'

        if not args.force and os.path.exists(args.OUT):
            print(f"file {args.OUT} exists. pass -f to force.", file=sys.stderr)
            return 1

    content = PROBER.read(args.IN)
    do_match = args.type or args.numbers
    if do_match:
        matcher = ObjectMatcher(args)
        if isinstance(content, Level):
            content = matcher.filter_level(content)
        else:
            if not content.is_object_group:
                print(f"CustomObject is a {content.type!r}, but"
                        f" CustomObject filtering is only supported for"
                        f" object Groups.", file=sys.stderr)
                return 1
            content.children = matcher.filter_objects(content.children)

    if not do_write:
        from .mkcustomobject import print_candidates
        print_candidates(matcher.matches)
        return 1

    if filters:
        for f in filters:
            f.apply(content)

    p = PrintContext(flags=('groups', 'subobjects'))
    if args.list:
        p.print_data_of(content)

    if do_match:
        p(f"Removed matches: {len(matcher.matches)}")
        num_objs, num_groups = count_objects(matcher.matches)
        if num_objs != len(matcher.matches):
            p(f"Removed objects: {num_objs}")
            p(f"Removed groups: {num_groups}")

    print("writing...")
    dbytes = DstBytes.in_memory()
    content.write(dbytes)

    with open(args.OUT, write_mode) as out_f:
        n = out_f.write(dbytes.file.getbuffer())

    print(f"{n} bytes written")
    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
