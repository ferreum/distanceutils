import unittest
from io import BytesIO

from distance.levelobjects import (
    MaterialFragment,
    TrackNodeFragment,
    PopupBlockerLogicFragment,
    ObjectSpawnCircleFragment,
    ParticleEmitLogicFragment,
    LightFragment,
    PulseMaterialFragment,
)
from distance.levelobjects import FRAG_PROBER
from distance.bytes import DstBytes, SKIP_BYTES


def disable_writes(dbytes):
    def do_raise(*args, **kwargs):
        raise AssertionError("attempted to write")
    dbytes.write_bytes = do_raise


def write_read(obj, read_func=None):
    if read_func is None:
        read_func = type(obj)

    buf = BytesIO()
    dbytes = DstBytes(buf)

    obj.write(dbytes)
    dbytes.pos = 0
    disable_writes(dbytes)
    result = read_func(dbytes)

    if result.exception:
        raise result.exception

    return result, buf


class Base(object):

    class WriteReadTest(unittest.TestCase):

        exact = True

        def test_probe(self):
            with open(self.filename, 'rb') as f:
                res = FRAG_PROBER.read(DstBytes(f))

                self.assertEqual(self.frag_class, type(res))
                self.verify_fragment(res)

        def test_read(self):
            with open(self.filename, 'rb') as f:
                res = self.frag_class(DstBytes(f))

                self.verify_fragment(res)

        def test_write_read(self):
            with open(self.filename, 'rb') as f:
                dbr = DstBytes(f)
                obj = self.frag_class(dbr)

                res, buf = write_read(obj)

                self.verify_fragment(res)
                self.assertEqual(dbr.pos, len(buf.getbuffer()))

                if self.exact:
                    f.seek(0)
                    self.assertEqual(f.read(), buf.getbuffer())


class TracknodeTest(Base.WriteReadTest):

    filename = "tests/in/fragment/tracknode splineroad.frag"

    frag_class = TrackNodeFragment

    def verify_fragment(self, frag):
        self.assertEqual(79, frag.parent_id)
        self.assertEqual(100, frag.snap_id)


class MaterialTest(Base.WriteReadTest):

    filename = "tests/in/fragment/material splineroad.frag"

    frag_class = MaterialFragment

    def verify_fragment(self, frag):
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

    frag_class = MaterialFragment

    def verify_fragment(self, frag):
        mats = frag.materials
        color = mats['KillGridInfinitePlaneEditorPreview']['_Color']
        self.assertAlmostEqual(0.955882, color[0], places=5)
        self.assertAlmostEqual(0.063257, color[1], places=5)
        self.assertAlmostEqual(0.063257, color[2], places=5)
        self.assertAlmostEqual(0.443137, color[3], places=5)
        self.assertEqual(1, len(mats))


class PopupBlockerLogicTest(Base.WriteReadTest):

    filename = "tests/in/fragment/popupblockerlogic empire.frag"

    frag_class = PopupBlockerLogicFragment

    def verify_fragment(self, frag):
        props = frag.props
        self.assertEqual(SKIP_BYTES, props['HoloDistance'])
        self.assertEqual(8, len(props))


class ObjectSpawnCircleTest(Base.WriteReadTest):

    filename = "tests/in/fragment/objectspawncircle lightningspawner.frag"

    frag_class = ObjectSpawnCircleFragment

    def verify_fragment(self, frag):
        props = frag.props
        self.assertEqual(b'\x00\x00\x2a\x43', props['TriggerRadius'])
        self.assertEqual(6, len(props))


class ParticleEmitLogicTest(Base.WriteReadTest):

    filename = "tests/in/fragment/particleemitlogic brokensparkssmall.frag"

    frag_class = ParticleEmitLogicFragment

    def verify_fragment(self, frag):
        props = frag.props
        self.assertEqual(SKIP_BYTES, props['LightScale'])
        self.assertEqual(4, len(props))


class LightTest(Base.WriteReadTest):

    filename = "tests/in/fragment/light light.frag"

    frag_class = LightFragment

    def verify_fragment(self, frag):
        props = frag.props
        self.assertEqual(SKIP_BYTES, props['IgnoreColorChannel'])
        self.assertEqual(5, len(props))


class PulseMaterialTest(Base.WriteReadTest):

    filename = "tests/in/fragment/pulsematerial saw.frag"

    frag_class = PulseMaterialFragment

    def verify_fragment(self, frag):
        props = frag.props
        self.assertEqual(b'\0', props['IgnoreColorChannel'])
        self.assertEqual(7, len(props))


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
