"""Try to find properties of fragments."""


import argparse
import re

from distance import Level, DefaultClasses
from distance.bytes import DstBytes, Section, Magic
from distance.printing import PrintContext
from distance.classes import ProbeError
from distance.base import Fragment, ObjectFragment


NamedPropertiesFragment = DefaultClasses.common.klass('NamedPropertiesFragment')
MaterialFragment = DefaultClasses.fragments.klass('Material')


frag_prober = DefaultClasses.fragments


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


def iter_objects(source):
    for obj in source:
        yield obj
        yield from iter_objects(obj.children)


def iter_level_objects(level):
    for l in level.layers:
        yield from iter_objects(l.objects)


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

        if self.closeversions and type(frag) is Fragment and sec.magic in (Magic[2], Magic[3]):
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
        db = DstBytes.from_data(data)
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
                i = db.read_ulong()
            except Exception:
                pass
            else:
                if offset <= i <= offset + len(data):
                    relative = i - offset - pos
                    matches.append(("Offset", pos, f"0x{i:08x} (pos{relative:+}/end{relative-8:+})"))
            pos += 1
        return matches

    def fragment_pred(self, sec):
        if not self.all and sec.to_key() in KNOWN_GOOD_SECTIONS:
            return False
        cls = frag_prober.probe_section(sec)
        if issubclass(cls, (ObjectFragment, NamedPropertiesFragment, MaterialFragment)):
            return False
        return True

    def visit_object(self, obj, p):
        frags = []
        for frag in obj.filter_fragments(self.fragment_pred):
            matches = self.find_matches(frag)
            if matches:
                frags.append((frag, matches))
                self.sections[frag.container.to_key()] = frag.container

        if frags:
            p(f"Object: {obj.type!r}")
            p(f"Offset: 0x{obj.start_pos:08x}")
            p(f"Candidates: {len(frags)}")
            with p.tree_children(len(frags)):
                for frag, matches in frags:
                    p.tree_next_child()
                    p(f"Section: {frag.container}")
                    start = frag.start_pos
                    end = frag.end_pos
                    sec = frag.container
                    p(f"Offset: 0x{start:08x} to 0x{end:08x}"
                      f" (0x{end - start:x} bytes, content 0x{sec.content_size:x} bytes)")
                    p(f"Matches: {len(matches)}")
                    with p.tree_children(len(matches)):
                        for name, offset, text in matches:
                            p.tree_next_child()
                            offset = "" if offset is None else f"0x{offset:x} "
                            p(f"{name}: {offset}{text}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-a", "--all", action='store_true',
                        help="Also include known fragments.")
    parser.add_argument("--noversion", action='store_true',
                        help="Do not detect close versions.")
    parser.add_argument("IN",
                        help="Level .bytes filename.")
    args = parser.parse_args()

    matcher = FragmentMatcher(DefaultClasses.fragments, args)

    content = DefaultClasses.level_like.read(args.IN)
    if isinstance(content, Level):
        object_source = iter_level_objects(content)
    else:
        # CustomObject
        object_source = iter_objects([content])
    p = PrintContext()
    for obj in object_source:
        matcher.visit_object(obj, p)
    if matcher.sections:
        p(f"Unique sections: {len(matcher.sections)}")
        with p.tree_children(len(matcher.sections)):
            for sec in matcher.sections.values():
                p.tree_next_child()
                p(f"Section: {sec}")

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et:
