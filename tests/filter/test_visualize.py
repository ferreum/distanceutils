from argparse import Namespace
import unittest

from distance import PROBER
from distance.filter import VisualizeFilter
from tests.common import ExtraAssertMixin


def mkargs(maxrecurse=-1, verbose=False):
    return Namespace(**locals())


def do_apply(fname, **kw):
    l = PROBER.read(f"tests/in/{fname}.bytes")
    f = VisualizeFilter(mkargs(**kw))
    f.apply(l)
    return l


def obj_by_type(objs, type):
    return next(o for o in objs if o.type == type)


class VisualizeTest(ExtraAssertMixin, unittest.TestCase):

    def test_tele_exit(self):
        l = do_apply("level/test single tele", verbose=True)

        objs = l.layers[0].objects
        self.assertEqual(2, len(objs))

        grp = obj_by_type(objs, 'Group')
        tele = obj_by_type(objs, 'Teleporter')

        exppos = (-7.405, -1.036, -9.532)
        self.assertSeqAlmostEqual(exppos, grp.transform.pos, places=3)
        self.assertSeqAlmostEqual(exppos, tele.transform.pos, places=3)
        self.assertAlmostEqual(0, grp.transform.qrot.angle())
        self.assertAlmostEqual(0, tele.transform.qrot.angle())

        sphere = obj_by_type(grp.children, 'SphereHDGS')

        self.assertSeqAlmostEqual((0, 36.8, 0), sphere.transform.pos)
        self.assertAlmostEqual(0, sphere.transform.qrot.angle())
        self.assertSeqAlmostEqual([0, 0, 0], sphere.transform.qrot.vec)
        self.assertSeqAlmostEqual([.25, .25, .25], sphere.transform.scale)

    def test_many_colliders(self):
        # just check for obvious crashes
        do_apply("level/many colliders", verbose=True)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
