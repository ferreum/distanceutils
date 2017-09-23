#!/usr/bin/python

"""Creates a CustomObject from a level."""


import os
import sys
import argparse

from distance.level import Level
from distance.bytes import DstBytes
from distance.printing import PrintContext


def iter_objects(source, recurse=-1):
    for obj in source:
        yield obj
        if recurse != 0 and obj.is_object_group:
            yield from iter_objects(obj.children, recurse=recurse-1)


def select_candidates(source, objnum, maxrecurse):
    res = []
    for i, obj in enumerate(iter_objects(source, maxrecurse)):
        if objnum is None or i == objnum:
            res.append(obj)
    return res


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-f", "--force", action='store_true',
                        help="Allow overwriting OUT file.")
    parser.add_argument("-n", "--objnum", type=int,
                        help="Object number to extract.")
    parser.add_argument("-l", "--maxrecurse", type=int, default=-1,
                        help="Maximum of recursions. 0 only lists layer objects.")
    parser.add_argument("IN",
                        help="Level .bytes filename.")
    parser.add_argument("OUT",
                        help="output .bytes filename.")
    args = parser.parse_args()

    objnum = args.objnum or None

    maxrecurse = args.maxrecurse

    write_mode = 'xb'
    if args.force:
        write_mode = 'wb'

    if not args.force and os.path.exists(args.OUT):
        print("file {args.OUT} exists. pass -f to force.", file=sys.stderr)
        return 1

    with open(args.IN, 'rb') as in_f:
        level = Level(DstBytes(in_f))
        candidates = select_candidates(level.iter_objects(), objnum, maxrecurse)

        tosave = None
        if len(candidates) == 1:
            tosave = candidates[0]
        elif len(candidates) > 1:
            p = PrintContext(file=sys.stdout, flags=('groups', 'subobjects'))
            p(f"Candidates: {len(candidates)}")
            with p.tree_children():
                for i, obj in enumerate(candidates):
                    p.tree_next_child()
                    p(f"Candidate: {i}")
                    p.print_data_of(obj)

        if tosave is not None:
            with open(args.OUT, write_mode) as out_f:
                tosave.print_data(file=sys.stdout, flags=('groups', 'subobjects'))
                dbytes = DstBytes(out_f)
                tosave.write(dbytes)
                print(f"{dbytes.pos} bytes written")
                return 0

    print("no matching object found", file=sys.stderr)
    return 1


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
