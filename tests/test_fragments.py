from distance.base import Fragment
from distance.fragments import (
    PROBER,
    MaterialFragment,
    TrackNodeFragment,
    PopupBlockerLogicFragment,
    ObjectSpawnCircleFragment,
)
from distance.bytes import DstBytes, SKIP_BYTES
from tests import common


class Base(object):

    class WriteReadTest(common.WriteReadTest):

        exact = True

        def test_probe(self):
            with open(self.filename, 'rb') as f:
                res = PROBER.read(DstBytes(f))

                self.assertEqual(self.read_obj, type(res))
                self.verify_obj(res)


class UnknownTest(Base.WriteReadTest):

    filename = "tests/in/fragment/material splineroad.frag"

    read_obj_pre = Fragment

    read_obj = MaterialFragment

    def verify_obj(self, frag):
        MaterialTest.verify_obj(self, frag)


class TracknodeTest(Base.WriteReadTest):

    filename = "tests/in/fragment/tracknode splineroad.frag"

    read_obj = TrackNodeFragment

    def verify_obj(self, frag):
        self.assertEqual(79, frag.parent_id)
        self.assertEqual(100, frag.snap_id)


class MaterialTest(Base.WriteReadTest):

    filename = "tests/in/fragment/material splineroad.frag"

    read_obj = MaterialFragment

    def verify_obj(self, frag):
        mats = frag.materials
        panel_color = mats['empire_panel_light']['_Color']
        self.assertAlmostEqual(0.50588, panel_color[0], places=5)
        self.assertAlmostEqual(0.50588, panel_color[1], places=5)
        self.assertAlmostEqual(0.50588, panel_color[2], places=5)
        self.assertAlmostEqual(1.00000, panel_color[3], places=5)
        self.assertEqual(4, len(mats))
        self.assertEqual([2, 3, 3, 3], [len(cols) for cols in mats.values()])


class MaterialV2Test(Base.WriteReadTest):

    filename = "tests/in/fragment/material v2.frag"

    read_obj = MaterialFragment

    def verify_obj(self, frag):
        mats = frag.materials
        color = mats['KillGridInfinitePlaneEditorPreview']['_Color']
        self.assertAlmostEqual(0.955882, color[0], places=5)
        self.assertAlmostEqual(0.063257, color[1], places=5)
        self.assertAlmostEqual(0.063257, color[2], places=5)
        self.assertAlmostEqual(0.443137, color[3], places=5)
        self.assertEqual(1, len(mats))


class PopupBlockerLogicTest(Base.WriteReadTest):

    filename = "tests/in/fragment/popupblockerlogic empire.frag"

    read_obj = PopupBlockerLogicFragment

    def verify_obj(self, frag):
        props = frag.props
        self.assertEqual(SKIP_BYTES, props['HoloDistance'])
        self.assertEqual(8, len(props))


class ObjectSpawnCircleTest(Base.WriteReadTest):

    filename = "tests/in/fragment/objectspawncircle lightningspawner.frag"

    read_obj = ObjectSpawnCircleFragment

    def verify_obj(self, frag):
        props = frag.props
        self.assertEqual(b'\x00\x00\x2a\x43', props['TriggerRadius'])
        self.assertEqual(6, len(props))


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
