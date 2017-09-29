"""Try to find properties of fragments."""


import sys
import argparse
import re
from io import BytesIO

from distance.level import Level
from distance.levelobjects import (
    LevelObject,
    FRAG_PROBER as LEVEL_FRAG_PROBER,
)
from distance.bytes import (
    DstBytes, Section,
    MAGIC_2, MAGIC_3, MAGIC_9
)
from distance.printing import PrintContext
from distance.prober import BytesProber, ProbeError
from distance.base import Fragment


STR_EXCLUDE_PATTERN = re.compile(r"[^ -~]")


KNOWN_GOOD_SECTIONS = [
    Section(MAGIC_2, 0x25, 2), # PopupLogic
    Section(22222222, type=0x63, version=0), # Group name
    Section(22222222, type=0x16, version=1), # TrackNode
    Section(22222222, type=0x43, version=1), # from VirusSpiritTeaser
    Section(22222222, type=0x45, version=1), # from GravityTrigger
    Section(33333333, type=0x7, version=1), # from WorldText
    Section(22222222, type=0x50, version=1), # from VirusBuilding003Core
    Section(22222222, type=0x4b, version=1), # from MusicTrigger
    Section(33333333, type=0x7, version=2), # from v8 SectorNumberTextCeiling
    Section(22222222, type=0x50, version=2), # from v9 LevelEditorCarSpawner
    Section(22222222, type=0x77, version=4), # from v9 Biodome
    Section(22222222, type=0x9a, version=7), # from v9 Light
    Section(22222222, type=0x89, version=2), # from v9 EventTriggerBox
    Section(22222222, type=0x2c, version=2), # from v9 BrightenCarHeadlights
    Section(22222222, type=0x8a, version=1), # v9 component EventListener
    Section(22222222, type=0x4a, version=2), # InfoDisplayLogic from v9 InfoDisplayBox
    Section(22222222, type=0x43, version=2), # from v9 VirusMazeCeiling001

    # known good version
    Section(22222222, type=0x57, version=1), # from v9 CarScreenTextDecodeTrigger
    Section(22222222, type=0x38, version=1), # from v5 VirusMine, EmpireEndZoneCircle, ...
    Section(22222222, type=0x17, version=1), # from v5 EmpireCircle

    # false positives
    # bogus offset
    Section(22222222, type=0x81, version=7), # from v9 particle system
    Section(22222222, type=0x83, version=3), # from v9 GS
    Section(33333333, type=0x9, version=3), # from v8 LightbeamRays
    Section(22222222, type=0x77, version=3), # from v7 Biodome
    Section(22222222, type=0x77, version=2), # from v5 Biodome
    Section(22222222, type=0x19, version=1), # from v7 CheckpointLogic
    Section(33333333, type=0xa, version=1), # from v3 LensFlare
    Section(33333333, type=0x2, version=0), # from s8 (map The Virus Begins) VirusBuilding004
    Section(33333333, type=0x9, version=1), # from v3 Light2
    Section(33333333, type=0x9, version=4), # from v8 Light

    # contains a string
    Section(22222222, type=0x65, version=1), # from v9 WarningPulseLight (shader property name)
    Section(22222222, type=0x9f, version=1), # from v9 DiscoverableStuntArea (area name)
    Section(22222222, type=0x61, version=1), # from v3 CreditsNameOrb
]


KNOWN_GOOD_SECTIONS = {s.to_key() for s in KNOWN_GOOD_SECTIONS}


class DetectFragment(Fragment):
    pass


def setup_probers(args):
    prober = BytesProber()
    p_level = BytesProber(baseclass=LevelObject)
    p_frag = BytesProber(baseclass=Fragment)

    @prober.func
    def _detect_other(section):
        if section.magic == MAGIC_9:
            return Level
        return None

    @p_level.func
    def _fallback_levelobject(section):
        return LevelObject

    @p_frag.func
    def _fallback_fragment(section):
        return DetectFragment

    if not args.all:
        p_frag.extend(LEVEL_FRAG_PROBER)
    prober.extend(p_level)

    return prober, p_level, p_frag


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
        sec = frag.start_section
        offset = sec.data_start
        data = frag.raw_data
        matches = []

        if not self.all and sec.to_key() in KNOWN_GOOD_SECTIONS:
            return []

        if self.closeversions and sec.magic in (MAGIC_2, MAGIC_3):
            ver = sec.version
            versions = []
            if ver > 0:
                versions.extend(range(ver))
            versions.extend(range(ver + 1, ver + 3))
            for ver in versions:
                probe_sec = Section(sec.magic, sec.type, ver)
                try:
                    self.real_frag_prober.probe_section(probe_sec)
                except ProbeError:
                    pass
                else:
                    matches.append(("Other version", None, repr(probe_sec)))

        pos = 0
        buf = BytesIO(data)
        db = DstBytes(buf)
        while pos < len(data):
            db.pos = pos
            try:
                s = db.read_str()
            except Exception:
                pass
            else:
                if s and len(list(STR_EXCLUDE_PATTERN.findall(s))) < len(s) // 3:
                    matches.append(("String", pos, repr(s)))
            db.pos = pos
            try:
                i = db.read_int(8)
            except Exception:
                pass
            else:
                if offset <= i <= offset + len(data):
                    relative = i - offset - pos
                    matches.append(("Offset", pos, f"0x{i:08x} (pos{relative:+}/end{relative-8:+})"))
            pos += 1
        return matches


    def visit_object(self, obj, p):
        frags = []
        for frag in obj.fragments:
            if isinstance(frag, DetectFragment):
                matches = self.find_matches(frag)
                if matches:
                    frags.append((frag, matches))
                    self.sections[frag.start_section.to_key()] = frag.start_section

        if frags:
            p(f"Object: {obj.type!r}")
            p(f"Offset: 0x{obj.start_pos:08x}")
            p(f"Candidates: {len(frags)}")
            with p.tree_children():
                for frag, matches in frags:
                    p.tree_next_child()
                    p(f"Section: {frag.start_section}")
                    start = frag.start_pos
                    end = frag.end_pos
                    sec = frag.start_section
                    p(f"Offset: 0x{start:08x} to 0x{end:08x}"
                      f" (0x{end - start:x} bytes, data 0x{sec.data_size:x} bytes)")
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

    prober, p_level, p_frag = setup_probers(args)

    opts = dict(
        level_frag_prober=p_frag,
        level_subobj_prober=p_level,
        level_obj_prober=p_level,
    )

    matcher = FragmentMatcher(LEVEL_FRAG_PROBER, args)

    content = prober.read(args.IN, opts=opts)
    if isinstance(content, Level):
        object_source = iter_objects(content.iter_objects())
    else:
        # CustomObject
        object_source = iter_objects([content])
    p = PrintContext(file=sys.stdout, flags=())
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
