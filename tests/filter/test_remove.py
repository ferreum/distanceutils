from argparse import Namespace
import unittest

from distance.level import Level
from distance.filter import RemoveFilter


def mkargs(maxrecurse=-1, type=[], numbers=[], section=[],
           print_=False, invert=False):
    return Namespace(**locals())


class RemoveTest(unittest.TestCase):

    def test_by_type(self):
        l = Level("tests/in/level/test-straightroad.bytes")

        f = RemoveFilter(mkargs(type=["Empire(Start|End)Zone"]))
        f.apply(l)

        for obj in l.layers[0].objects:
            if "Zone" in obj.type:
                raise AssertionError("Found road: {obj.type}")
        self.assertEqual(['EmpireStartZone', 'EmpireEndZone'], [o.type for o in f.removed])
        self.assertEqual(2, f.num_matches)

    def test_by_number(self):
        l = Level("tests/in/level/test-straightroad.bytes")

        f = RemoveFilter(mkargs(numbers=[0]))
        f.apply(l)

        obj = l.layers[0].objects[0]
        self.assertEqual('KillGridInfinitePlane', obj.type)
        self.assertEqual(['LevelEditorCarSpawner'], [o.type for o in f.removed])
        self.assertEqual(6, f.num_matches)

    def test_by_section(self):
        l = Level("tests/in/level/test-straightroad.bytes")

        f = RemoveFilter(mkargs(section=["3,9,1"]))
        f.apply(l)

        self.assertEqual(3, len(l.layers[0].objects))
        self.assertEqual(['DirectionalLight', 'EmpireStartZone', 'EmpireEndZone'],
                         [o.type for o in f.removed])
        self.assertEqual(3, f.num_matches)

    def test_invert(self):
        l = Level("tests/in/level/test-straightroad.bytes")

        f = RemoveFilter(mkargs(type=['Road'], invert=True))
        f.apply(l)

        self.assertEqual(1, len(l.layers[0].objects))
        self.assertEqual('EmpireSplineRoadStraight', l.layers[0].objects[0].type)


# vim:set sw=4 ts=8 sts=4 et:
