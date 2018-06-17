from argparse import Namespace
import unittest

from distance import Level
from distance.levelobjects import OldSimple
from distance import levelfragments as levelfrags
from distance.filter import GoldifyFilter
from tests.common import ExtraAssertMixin


class GoldifyTest(ExtraAssertMixin, unittest.TestCase):

    def test_bugs(self):
        l = Level("tests/in/level/test-oldsimples.bytes")
        oldnum = len(l.layers[0].objects)

        f = GoldifyFilter(Namespace(maxrecurse=-1, mode="bugs", debug=False))
        f.apply(l)

        cube = None
        for obj in l.layers[0].objects:
            if isinstance(obj, OldSimple) and obj.shape == 'Cube':
                raise AssertionError("Old cube found")
            if obj.type == 'CubeGS':
                if cube is not None:
                    raise AssertionError("Multiple CubeGS")
                cube = obj
        if cube is None:
            raise AssertionError("CubeGS not found")
        self.assertSeqAlmostEqual((-341.3285, 0, -336.9198), cube.transform[0], places=4)
        self.assertSeqAlmostEqual((0, .0612, 0, .9981), cube.transform[1], places=4)
        self.assertSeqAlmostEqual((0.78125,)*3, cube.transform[2])
        self.assertEqual(oldnum, len(l.layers[0].objects))
        self.assertEqual(1, f.num_replaced)

    def test_with_animator(self):
        import numpy as np

        l = Level("tests/in/level/old cone with anim.bytes")
        old = l.layers[0].objects[0]

        f = GoldifyFilter(Namespace(maxrecurse=-1, mode="unsafe", debug=False))
        f.apply(l)

        grp, = l.layers[0].objects
        self.assertEqual('Group', grp.type)
        self.assertSeqAlmostEqual(old.transform.pos, grp.transform.pos)
        rotdiff = np.quaternion(2**.5/-2, 2**.5/2, 0, 0) / grp.transform.qrot
        self.assertAlmostEqual(0, rotdiff.angle())
        self.assertSeqAlmostEqual((10, 10, 10), grp.transform.scale)

        gs, = grp.children
        self.assertSeqAlmostEqual((0, 0, 1.409), gs.transform.pos)
        rotdiff = np.quaternion(2**.5/2, 2**.5/2, 0, 0) / gs.transform.qrot
        self.assertAlmostEqual(0, rotdiff.angle())

        self.assertTrue(any(f for f in grp.fragments
                            if isinstance(f, levelfrags.AnimatorFragment)))


# vim:set sw=4 ts=8 sts=4 et:
