"""Filter objects from a level."""


import os
import sys
import argparse
import re

from distance.level import Level
from distance.levelobjects import PROBER as LEVEL_PROBER
from distance.bytes import (
    DstBytes,
    MAGIC_2, MAGIC_3, MAGIC_32, MAGIC_9,
    Section,
)
from distance.printing import PrintContext
from distance.prober import BytesProber


PROBER = BytesProber()


@PROBER.func
def _detect_other(section):
    if section.magic == MAGIC_9:
        return Level
    return None


PROBER.extend(LEVEL_PROBER)


MAGICMAP = {2: MAGIC_2, 3: MAGIC_3, 32: MAGIC_32}


def parse_section(arg):
    parts = arg.split(",")
    magic = MAGICMAP[int(parts[0])]
    return Section(magic, *(int(p, base=0) for p in parts[1:]))


class ObjectMatcher(object):

    def __init__(self, args):
        self.all = args.all
        self.objnum = args.objnum
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
            if num in self.objnum:
                return True
        return False

    def _filter_objects(self, objs, recurse):
        result = []
        for obj in objs:
            if self.match(obj):
                continue
            result.append(obj)
            if obj.is_object_group and recurse != 0:
                obj.children = self._filter_objects(obj.children, recurse - 1)
        return result

    def filter_objects(self, objs):
        return self._filter_objects(objs, self.maxrecurse)

    def filter_level(self, level):
        for layer in level.layers:
            layer.objects = self.filter_objects(layer.objects)
        return level


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-f", "--force", action='store_true',
                        help="Allow overwriting OUT file.")
    parser.add_argument("-n", "--objnum", action='append',
                        type=int, default=[],
                        help="Object number to extract.")
    parser.add_argument("-a", "--all", action='store_true',
                        help="Filter out all matching objects.")
    parser.add_argument("-l", "--maxrecurse", type=int, default=-1,
                        help="Maximum of recursions. 0 only lists layer objects.")
    parser.add_argument("-t", "--type", action='append', default=[],
                        help="Match object type (regex).")
    parser.add_argument("-s", "--section", action='append', default=[],
                        help="Match sections.")
    parser.add_argument("IN",
                        help="Level .bytes filename.")
    parser.add_argument("OUT",
                        help="output .bytes filename.")
    args = parser.parse_args()

    do_write = args.all or bool(args.objnum)
    if do_write:
        write_mode = 'xb'
        if args.force:
            write_mode = 'wb'

        if not args.force and os.path.exists(args.OUT):
            print(f"file {args.OUT} exists. pass -f to force.", file=sys.stderr)
            return 1

    with open(args.IN, 'rb') as in_f:
        content = PROBER.read(DstBytes(in_f))
        matcher = ObjectMatcher(args)
        if isinstance(content, Level):
            result = matcher.filter_level(content)
        else:
            result.children = matcher.filter_objects(result.children)

        if not do_write:
            from .mkcustomobject import print_candidates
            print_candidates(matcher.matches)
            return 1
        else:
            with open(args.OUT, write_mode) as out_f:
                result.print_data(file=sys.stdout, flags=('groups', 'subobjects'))
                dbytes = DstBytes(out_f)
                result.write(dbytes)
                print(f"{dbytes.pos} bytes written")
                return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0: