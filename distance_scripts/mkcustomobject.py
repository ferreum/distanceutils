"""Create a CustomObject from a level."""


import os
import sys
import argparse
import re

from distance.level import Level
from distance.levelobjects import PROBER as LEVELOBJ_PROBER
from distance.bytes import MAGIC_9
from distance.printing import PrintContext
from distance.prober import BytesProber


PROBER = BytesProber()


@PROBER.func
def _detect_other(section):
    if section.magic == MAGIC_9:
        return Level
    return None


PROBER.extend(LEVELOBJ_PROBER)


def iter_objects(source, recurse=-1):
    for obj in source:
        yield obj
        if recurse != 0 and obj.is_object_group:
            yield from iter_objects(obj.children, recurse=recurse-1)


def select_candidates(source, args):
    numbers = args.numbers

    maxrecurse = args.maxrecurse

    type_patterns = [re.compile(r) for r in args.type]

    def match_object(obj):
        if type_patterns:
            typename = obj.type
            if not any(r.search(typename) for r in type_patterns):
                return False
        return True

    res = []
    for i, obj in enumerate(obj for obj in iter_objects(source, maxrecurse)
                            if match_object(obj)):
        if numbers is None or i == numbers:
            res.append(obj)
    return res


def print_candidates(candidates):
    p = PrintContext(flags=('groups', 'subobjects'))
    p(f"Candidates: {len(candidates)}")
    with p.tree_children():
        for i, obj in enumerate(candidates):
            p.tree_next_child()
            p(f"Candidate: {i}")
            p.print_data_of(obj)
    p(f"Use -n to specify candidate.")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-f", "--force", action='store_true',
                        help="Allow overwriting OUT file.")
    parser.add_argument("-n", "--number", dest='numbers', type=int, default=None,
                        help="Select by candidate number.")
    parser.add_argument("-l", "--maxrecurse", type=int, default=-1,
                        help="Maximum of recursions. 0 only lists layer objects.")
    parser.add_argument("-t", "--type", action='append', default=[],
                        help="Match object type (regex).")
    parser.add_argument("IN",
                        help="Level .bytes filename.")
    parser.add_argument("OUT",
                        help="output .bytes filename.")
    args = parser.parse_args()

    write_mode = 'xb'
    if args.force:
        write_mode = 'wb'

    if not args.force and os.path.exists(args.OUT):
        print(f"file {args.OUT} exists. pass -f to force.", file=sys.stderr)
        return 1

    content = PROBER.read(args.IN)
    if isinstance(content, Level):
        object_source = content.iter_objects()
    else:
        # CustomObject
        object_source = [content]
    candidates = select_candidates(object_source, args)

    tosave = None
    if len(candidates) == 1:
        tosave = candidates[0]
    elif len(candidates) > 1:
        print_candidates(candidates)
    else:
        print("no matching object found", file=sys.stderr)

    if tosave is None:
        return 1

    tosave.print_data(file=sys.stdout, flags=('groups', 'subobjects'))

    print("writing...")
    n = tosave.write(args.OUT, write_mode=write_mode)
    print(f"{n} bytes written")
    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
