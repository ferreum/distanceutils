import unittest
from math import sqrt, sin, cos, pi

from distance.bytes import DstBytes, SKIP_BYTES, S_FLOAT3, S_FLOAT4
from distance.base import Transform
from tests.common import ExtraAssertMixin


class DstBytesTest(ExtraAssertMixin, unittest.TestCase):

    def test_fill_none(self):
        t = Transform.fill()

        self.assertSeqAlmostEqual(((0, 0, 0), (0, 0, 0, 1), (1, 1, 1)), t)

    def test_fill_pos(self):
        t = Transform.fill(pos=(1, 2, 3))

        self.assertSeqAlmostEqual(((1, 2, 3), (0, 0, 0, 1), (1, 1, 1)), t)

    def test_fill_rot(self):
        t = Transform.fill(rot=(1, 2, 3, 4))

        self.assertSeqAlmostEqual(((0, 0, 0), (1, 2, 3, 4), (1, 1, 1)), t)

    def test_fill_scale(self):
        t = Transform.fill(scale=(1, 2, 3))

        self.assertSeqAlmostEqual(((0, 0, 0), (0, 0, 0, 1), (1, 2, 3)), t)

    def test_fill_pos_err(self):
        self.assertRaises(TypeError, Transform.fill, pos=())
        self.assertRaises(TypeError, Transform.fill, pos=(1, 2))
        self.assertRaises(TypeError, Transform.fill, pos=(1, 2, 3, 4))
        self.assertRaises(TypeError, Transform.fill, pos=1)

    def test_fill_rot_err(self):
        self.assertRaises(TypeError, Transform.fill, rot=())
        self.assertRaises(TypeError, Transform.fill, rot=(1, 2, 3))
        self.assertRaises(TypeError, Transform.fill, rot=(1, 2, 3, 4, 5))
        self.assertRaises(TypeError, Transform.fill, rot=1)

    def test_fill_scale_err(self):
        self.assertRaises(TypeError, Transform.fill, scale=())
        self.assertRaises(TypeError, Transform.fill, scale=(1, 2))
        self.assertRaises(TypeError, Transform.fill, scale=(1, 2, 3, 4))
        self.assertRaises(TypeError, Transform.fill, scale=1)

    def test_empty(self):
        self.assertEqual((), tuple(Transform()))

    def test_effective_empty(self):
        self.assertSeqAlmostEqual(
            ((0, 0, 0), (0, 0, 0, 1), (1, 1, 1)),
            Transform().effective())

    def test_effective_args_empty(self):
        self.assertSeqAlmostEqual(
            ((1, 2, 3), (4, 5, 6, 7), (8, 9, 0)),
            Transform().effective((1, 2, 3), (4, 5, 6, 7), (8, 9, 0)))

    def test_effective_skip(self):
        self.assertAlmostEqual(
            ((0, 0, 0), (0, 0, 0, 1), (1, 1, 1)),
            Transform((), (), ()).effective())

    def test_effective_skip_args(self):
        self.assertSeqAlmostEqual(
            ((1, 2, 3), (4, 5, 6, 7), (8, 9, 0)),
            Transform((), (), ()).effective((1, 2, 3), (4, 5, 6, 7), (8, 9, 0)))

    def test_effective_set(self):
        self.assertSeqAlmostEqual(
            ((1, 2, 3), (4, 5, 6, 7), (8, 9, 0)),
            Transform((1, 2, 3), (4, 5, 6, 7), (8, 9, 0)).effective())

    def test_apply_identitity(self):
        self.assertSeqAlmostEqual(
            ((0, 0, 0), (0, 0, 0, 1), (1, 1, 1)),
            Transform.fill().apply(*Transform.fill()))

    def test_apply_pos(self):
        self.assertSeqAlmostEqual(
            ((1, 2, 3), (0, 0, 0, 1), (1, 1, 1)),
            Transform.fill().apply((1, 2, 3)))

    def test_apply_rot(self):
        self.assertSeqAlmostEqual(
            ((0, 0, 0), (0, .707, 0, .707), (1, 1, 1)),
            Transform.fill().apply(rot=(0, .707, 0, .707)))

    def test_apply_scale(self):
        self.assertSeqAlmostEqual(
            ((0, 0, 0), (0, 0, 0, 1), (2, 3, 4)),
            Transform.fill().apply(scale=(2, 3, 4)))

    def test_apply_scale_axisswap(self):
        rot = (sin(pi/4), 0, 0, cos(pi/4))
        self.assertSeqAlmostEqual(
            ((0, 0, 0), rot, (2, 4, 3)),
            Transform.fill(scale=(2, 3, 4)).apply(rot=rot))

    def test_apply_scale_axislock(self):
        rot = (sin(pi/3), 0, 0, cos(pi/3))
        self.assertSeqAlmostEqual(
            ((0, 0, 0), rot, (2, 4, 4)),
            Transform.fill(scale=(2, 4, 4)).apply(rot=rot))

    def test_apply_scale_axislock_error(self):
        rot = (sin(pi/3), 0, 0, cos(pi/3))
        self.assertRaisesRegex(
            ValueError, r"Incompatible",
            Transform.fill(scale=(2, 2, 4)).apply, rot=rot)

    def test_apply_not_effective(self):
        self.assertRaises(TypeError, Transform.fill().apply, ())


class ReadWriteTest(ExtraAssertMixin, unittest.TestCase):

    def test_read_skip(self):
        db = DstBytes.from_data(SKIP_BYTES * 3)

        t = Transform.read_from(db)

        self.assertEqual(Transform((), (), ()), t)

    def test_read(self):
        db = DstBytes.from_data(
            S_FLOAT3.pack(1, 2, 3) + S_FLOAT4.pack(4, 5, 6, 7) + S_FLOAT3.pack(8, 9, 0))

        t = Transform.read_from(db)

        self.assertEqual(Transform((1, 2, 3), (4, 5, 6, 7), (8, 9, 0)), t)

    def test_write_skip(self):
        db = DstBytes.in_memory()

        Transform((), (), ()).write_to(db)

        self.assertEqual(SKIP_BYTES * 3, db.file.getbuffer())

    def test_write_empty(self):
        db = DstBytes.in_memory()

        Transform().write_to(db)

        self.assertEqual(SKIP_BYTES * 3, db.file.getbuffer())

    def tests_write(self):
        db = DstBytes.in_memory()

        Transform((1, 2, 3), (4, 5, 6, 7), (8, 9, 0)).write_to(db)

        db.seek(0)
        self.assertSeqAlmostEqual((1, 2, 3), db.read_struct(S_FLOAT3))
        self.assertSeqAlmostEqual((4, 5, 6, 7), db.read_struct(S_FLOAT4))
        self.assertSeqAlmostEqual((8, 9, 0), db.read_struct(S_FLOAT3))


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
