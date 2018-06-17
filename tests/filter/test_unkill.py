from argparse import Namespace
import unittest

from distance import Level
from distance.filter import UnkillFilter


def mkargs(maxrecurse=-1, collision=True, color=True, debug=False):
    return Namespace(**locals())


class UnkillTest(unittest.TestCase):

    def test_replace(self):
        l = Level("tests/in/level/finite grids.bytes")

        f = UnkillFilter(mkargs())
        f.apply(l)

        types = [o.type for ly in l.layers for o in ly.objects]
        self.assertEqual(5, len(types))
        self.assertFalse(any('Kill' in t for t in types))


# vim:set sw=4 ts=8 sts=4 et:
