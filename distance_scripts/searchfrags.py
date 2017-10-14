"""Try to find properties of fragments."""


import argparse
import re
from io import BytesIO

from distance.level import Level
from distance.levelfragments import PROBER as LEVEL_FRAG_PROBER
from distance.levelobjects import PROBER as LEVELOBJ_PROBER
from distance.bytes import (
    DstBytes, Section,
    MAGIC_2, MAGIC_3, MAGIC_9
)
from distance.printing import PrintContext
from distance.prober import BytesProber, ProbeError
from distance.base import Fragment, ObjectFragment
from distance.levelfragments import NamedPropertiesFragment, MaterialFragment


STR_EXCLUDE_PATTERN = re.compile(r"[^ -~]")


KNOWN_GOOD_SECTIONS = [
    # contains a string
    Section(22222222, type=0x65, version=1), # from v9 WarningPulseLight (shader property name)
    Section(22222222, type=0x9f, version=1), # from v9 DiscoverableStuntArea (area name)
    Section(22222222, type=0x61, version=1), # from v3 CreditsNameOrb (text)
    Section(22222222, type=0x4a, version=2), # InfoDisplayLogic from v9 InfoDisplayBox (text)
    Section(22222222, type=0x77, version=4), # v9 Biodome (background name)
    Section(33333333, type=0x7, version=1), # WorldText v1 (text)
    Section(33333333, type=0x7, version=2), # WorldText v2 (text)
    Section(33333333, type=0x2, version=0), # from s8 (map The Virus Begins) VirusBuilding004 (its object name)
    Section(22222222, type=0x63, version=0), # custom name (the name)
    Section(22222222, type=0x8a, version=1), # v9 EventListener (custom name)
    Section(22222222, type=0x89, version=2), # v9 EventTriggerBox (custom name)
    Section(22222222, type=0x57, version=1), # v9 CarScreenTextDecodeTrigger (text)
]


KNOWN_GOOD_SECTIONS = {s.to_key() for s in KNOWN_GOOD_SECTIONS}


def setup_prober(args):
    prober = BytesProber()
    prober.add_fragment(Level, MAGIC_9)
    prober.extend(LEVELOBJ_PROBER)

    return prober


def iter_objects(source, recurse=-1):
    for obj in source:
        yield obj
        if recurse != 0:
            yield from iter_objects(obj.children, recurse=recurse-1)


class FragmentMatcher(object):

    def __init__(self, real_frag_prober, args):
        self.real_frag_prober = real_frag_prober
        self.all = args.all
        self.closeversions = not args.noversion
        self.sections = {}

    def find_matches(self, frag):
        sec = frag.container
        offset = sec.content_start
        data = frag.raw_data
        matches = []

        if self.closeversions and type(frag) is Fragment and sec.magic in (MAGIC_2, MAGIC_3):
            ver = sec.version
            versions = []
            versions.extend(range(ver))
            versions.extend(range(ver + 1, ver + 3))
            for ver in versions:
                probe_sec = Section(sec.magic, sec.type, ver)
                try:
                    cls = self.real_frag_prober.probe_section(probe_sec)
                except ProbeError:
                    pass
                else:
                    if not cls is Fragment:
                        matches.append(("Other version", None, repr(probe_sec)))

        pos = 0
        buf = BytesIO(data)
        db = DstBytes(buf)
        while pos < len(data):
            db.seek(pos)
            try:
                s = db.read_str()
            except Exception:
                pass
            else:
                if s and sum(1 for _ in STR_EXCLUDE_PATTERN.findall(s)) < len(s) // 3:
                    matches.append(("String", pos, repr(s)))
            db.seek(pos)
            try:
                i = db.read_uint8()
            except Exception:
                pass
            else:
                if offset <= i <= offset + len(data):
                    relative = i - offset - pos
                    matches.append(("Offset", pos, f"0x{i:08x} (pos{relative:+}/end{relative-8:+})"))
            pos += 1
        return matches

    def filter_fragments(self, sec, prober):
        if not self.all and sec.to_key() in KNOWN_GOOD_SECTIONS:
            return False
        if issubclass(prober.probe_section(sec), (ObjectFragment, NamedPropertiesFragment, MaterialFragment)):
            return False
        return True

    def visit_object(self, obj, p):
        frags = []
        for frag in obj.filtered_fragments(self.filter_fragments):
            matches = self.find_matches(frag)
            if matches:
                frags.append((frag, matches))
                self.sections[frag.container.to_key()] = frag.container

        if frags:
            p(f"Object: {obj.type!r}")
            p(f"Offset: 0x{obj.start_pos:08x}")
            p(f"Candidates: {len(frags)}")
            with p.tree_children():
                for frag, matches in frags:
                    p.tree_next_child()
                    p(f"Section: {frag.container}")
                    start = frag.start_pos
                    end = frag.end_pos
                    sec = frag.container
                    p(f"Offset: 0x{start:08x} to 0x{end:08x}"
                      f" (0x{end - start:x} bytes, content 0x{sec.content_size:x} bytes)")
                    p(f"Matches: {len(matches)}")
                    with p.tree_children():
                        for name, offset, text in matches:
                            p.tree_next_child()
                            offset = "" if offset is None else f"0x{offset:x} "
                            p(f"{name}: {offset}{text}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-l", "--maxrecurse", type=int, default=-1,
                        help="Maximum of recursions. 0 only lists layer objects.")
    parser.add_argument("-a", "--all", action='store_true',
                        help="Also include known fragments.")
    parser.add_argument("--noversion", action='store_true',
                        help="Do not detect close versions.")
    parser.add_argument("IN",
                        help="Level .bytes filename.")
    args = parser.parse_args()

    prober = setup_prober(args)

    matcher = FragmentMatcher(LEVEL_FRAG_PROBER, args)

    content = prober.read(args.IN)
    if isinstance(content, Level):
        object_source = iter_objects(content.iter_objects())
    else:
        # CustomObject
        object_source = iter_objects([content])
    p = PrintContext()
    for obj in object_source:
        matcher.visit_object(obj, p)
    if matcher.sections:
        p(f"Unique sections: {len(matcher.sections)}")
        with p.tree_children():
            for sec in matcher.sections.values():
                p.tree_next_child()
                p(f"Section: {sec}")

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
