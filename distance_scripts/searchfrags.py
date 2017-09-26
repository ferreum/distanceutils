"""Sandbox, try to find certain fragments."""


import os
import sys
import argparse
import re
from io import BytesIO

from distance.level import Level
from distance.levelobjects import (
    LevelObject,
    FRAG_PROBER as LEVEL_FRAG_PROBER,
)
from distance.bytes import DstBytes, MAGIC_9
from distance.printing import PrintContext
from distance.prober import BytesProber
from distance.base import Fragment


STR_EXCLUDE_PATTERN = re.compile(r"[^ -~]")


PROBER = BytesProber()

FRAG_PROBER = BytesProber(baseclass=Fragment)

LEVEL_PROBER = BytesProber(baseclass=LevelObject)


@PROBER.func
def _detect_other(section):
    if section.magic == MAGIC_9:
        return Level
    return None


@PROBER.func
def _fallback_levelobject(section):
    return LevelObject


class DetectFragment(Fragment):
    pass


@FRAG_PROBER.func
def _fallback_fragment(section):
    return DetectFragment


FRAG_PROBER.extend(LEVEL_FRAG_PROBER)
PROBER.extend(LEVEL_PROBER)


def iter_objects(source, recurse=-1):
    for obj in source:
        yield obj
        if recurse != 0:
            yield from iter_objects(obj.children, recurse=recurse-1)


def find_strings(data):
    strs = []
    pos = 0
    buf = BytesIO(data)
    db = DstBytes(buf)
    while pos < len(data):
        db.pos = pos
        try:
            s = db.read_str()
        except Exception:
            pos += 1
        else:
            if s and len(list(STR_EXCLUDE_PATTERN.findall(s))) < len(s) // 3:
                strs.append(s)
                pos = db.pos
            else:
                pos += 1
    return strs


def visit_object(obj, p):
    frags = []
    for frag in obj.fragments:
        if isinstance(frag, DetectFragment):
            strs = find_strings(frag.raw_data)
            if strs:
                frags.append((frag, strs))

    if frags:
        p(f"Object: {obj.type!r}")
        p(f"Offset: 0x{obj.start_pos:08x}")
        p(f"Candidates: {len(frags)}")
        with p.tree_children():
            for frag, strs in frags:
                p.tree_next_child()
                p(f"Section: {frag.start_section}")
                p(f"Strings: {len(strs)}")
                with p.tree_children():
                    for s in strs:
                        p.tree_next_child()
                        p(f"String: {s!r}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-l", "--maxrecurse", type=int, default=-1,
                        help="Maximum of recursions. 0 only lists layer objects.")
    parser.add_argument("IN",
                        help="Level .bytes filename.")
    args = parser.parse_args()

    opts = dict(
        level_frag_prober=FRAG_PROBER,
        level_obj_prober=LEVEL_PROBER,
    )

    with open(args.IN, 'rb') as in_f:
        content = PROBER.read(DstBytes(in_f), opts=opts)
        if isinstance(content, Level):
            object_source = content.iter_objects()
        else:
            # CustomObject
            object_source = [content]
        p = PrintContext(file=sys.stdout, flags=('subobjects'))
        for obj in object_source:
            visit_object(obj, p)

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
