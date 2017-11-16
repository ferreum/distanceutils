"""Filter for removing objects."""


import re

from distance.bytes import (
    MAGIC_2, MAGIC_3, MAGIC_32,
    Section,
)
from .base import ObjectFilter
from distance.printing import PrintContext


MAGICMAP = {2: MAGIC_2, 3: MAGIC_3, 32: MAGIC_32}


FILTERS = {}


def parse_section(arg):
    parts = arg.split(",")
    magic = MAGICMAP[int(parts[0])]
    return Section(magic, *(int(p, base=0) for p in parts[1:]))


def print_candidates(candidates):
    p = PrintContext(flags=('groups', 'subobjects'))
    p(f"Candidates: {len(candidates)}")
    with p.tree_children():
        for i, obj in enumerate(candidates):
            p.tree_next_child()
            p(f"Candidate: {i}")
            p.print_data_of(obj)
    p(f"Use -n to specify candidate.")


class RemoveFilter(ObjectFilter):

    @classmethod
    def add_args(cls, parser):
        super().add_args(parser)
        parser.add_argument(":type", action='append', default=[],
                            help="Match object type (regex).")
        parser.add_argument(":section", action='append', default=[],
                            help="Match sections.")
        parser.add_argument(":print", action='store_true', dest='print_',
                            help="Print matching candidates and abort filter.")
        parser.add_argument(":all", action='store_true',
                            help="This is now the default and has been removed.")
        parser.add_argument(":number", dest='numbers', action='append',
                            type=int, default=[],
                            help="Select by candidate number.")
        parser.add_argument(":invert", action='store_true',
                            help="Remove unmatched objects.")

    def __init__(self, args):
        super().__init__(args)
        self.print_ = args.print_
        self.numbers = args.numbers
        self.type_patterns = [re.compile(r) for r in args.type]
        self.sections = {parse_section(arg).to_key() for arg in args.section}
        self.invert = args.invert
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
            if not self.numbers or num in self.numbers:
                return True
        return False

    def filter_any_object(self, obj, levels):
        remove = self.match(obj)
        if self.invert:
            remove = not remove
        res = super().filter_any_object(obj, levels)
        if remove:
            self.removed.append(obj)
            return ()
        return res

    def post_filter(self, content):
        if self.print_:
            print_candidates(self.matches)
            return False
        return True

    def print_summary(self, p):
        p(f"Removed matches: {len(self.removed)}")
        num_objs, num_groups = count_objects(self.removed)
        if num_objs != len(self.removed):
            p(f"Removed objects: {num_objs}")
            p(f"Removed groups: {num_groups}")


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


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
