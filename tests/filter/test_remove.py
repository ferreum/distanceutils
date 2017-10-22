from argparse import Namespace
import unittest

from distance import Level
from distance.filter import RemoveFilter
from tests.common import ExtraAssertMixin


def mkargs(maxrecurse=-1, type=[], all=False, numbers=[], section=[]):
    return Namespace(maxrecurse=maxrecurse, type=type, all=all, numbers=numbers, section=section)


class RemoveTest(unittest.TestCase):

    def test_by_type(self):
        l = Level("tests/in/level/test-straightroad.bytes")

        f = RemoveFilter(mkargs(type=["Empire(Start|End)Zone"], all=True))
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

        f = RemoveFilter(mkargs(section=["3,9,1"], all=True))
        f.apply(l)

        self.assertEqual(3, len(l.layers[0].objects))
        self.assertEqual(['DirectionalLight', 'EmpireStartZone', 'EmpireEndZone'],
                         [o.type for o in f.removed])
        self.assertEqual(3, f.num_matches)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
