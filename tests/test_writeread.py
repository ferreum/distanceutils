import unittest
from io import BytesIO

from distance.level import (WedgeGS, Group, InfoDisplayBox, WinLogic,
                            SubTeleporter)
from distance.level import PROBER as LEVEL_PROBER
from distance.bytes import DstBytes
from distance.base import BaseObject


def inflate(obj):
    for child in obj.children:
        inflate(child)


def check_exceptions(obj):
    if obj.exception:
        raise obj.exception
    for child in obj.children:
        check_exceptions(child)


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

    inflate(result)
    check_exceptions(result)

    return result


class WedgeGSTest(unittest.TestCase):

    def assertSeqAlmostEqual(self, a, b):
        self.assertEqual(len(a), len(b), msg=f"\na={a}\nb={b}")
        for i, (va, vb) in enumerate(zip(a, b)):
            self.assertAlmostEqual(va, vb, msg=f"\ni={i}\na={a}\nb={b}")

    def test_simple(self):
        orig = WedgeGS()
        orig.image_index = 39

        res = write_read(orig)

        self.assertEqual(39, res.image_index)

    def test_properties(self):
        orig = WedgeGS()

        orig.mat_color = (.1, .1, .1, .2)
        orig.mat_emit = (.3, .3, .3, .3)
        orig.mat_reflect = (.1, .1, .1, .4)
        orig.mat_spec = (.3, .3, .3, .3)

        orig.tex_scale = (2, 2, 2)
        orig.tex_offset = (10, 10, -20)
        orig.image_index = 23
        orig.emit_index = 5
        orig.flip_tex_uv = 1
        orig.world_mapped = 1
        orig.disable_diffuse = 1
        orig.disable_bump = 1
        orig.bump_strength = 12.5
        orig.disable_reflect = 1
        orig.disable_collision = 1
        orig.additive_transp = 1
        orig.multip_transp = 1
        orig.invert_emit = 1

        res = write_read(orig)

        self.assertSeqAlmostEqual((.1, .1, .1, .2), res.mat_color)
        self.assertSeqAlmostEqual((.3, .3, .3, .3), res.mat_emit)
        self.assertSeqAlmostEqual((.1, .1, .1, .4), res.mat_reflect)
        self.assertSeqAlmostEqual((.3, .3, .3, .3), res.mat_spec)

        self.assertSeqAlmostEqual(res.tex_scale, (2, 2, 2))
        self.assertSeqAlmostEqual(res.tex_offset, (10, 10, -20))
        self.assertEqual(res.image_index, 23)
        self.assertEqual(res.emit_index, 5)
        self.assertEqual(res.flip_tex_uv, 1)
        self.assertEqual(res.world_mapped, 1)
        self.assertEqual(res.disable_diffuse, 1)
        self.assertEqual(res.disable_bump, 1)
        self.assertEqual(res.bump_strength, 12.5)
        self.assertEqual(res.disable_reflect, 1)
        self.assertEqual(res.disable_collision, 1)
        self.assertEqual(res.additive_transp, 1)
        self.assertEqual(res.multip_transp, 1)
        self.assertEqual(res.invert_emit, 1)


class GroupTest(unittest.TestCase):

    def test_empty(self):
        orig = Group()

        res = write_read(orig)

        self.assertEqual(0, len(res.children))

    def test_children(self):
        orig = Group(children=[Group()])

        res = write_read(orig)

        self.assertEqual(1, len(res.children))
        self.assertEqual(Group, type(res.children[0]))

    def test_custom_name(self):
        orig = Group(custom_name='test group')

        res = write_read(orig)

        self.assertEqual('test group', res.custom_name)


class UnknownTest(unittest.TestCase):

    def test_persist(self):
        with open("tests/in/customobject/infodisplaybox 1.bytes", 'rb') as f:
            obj = BaseObject(DstBytes(f))

            res = write_read(obj, read_func=InfoDisplayBox)

            self.assertEqual(["Text0", "Text1", "Text2", "", "Text4"], res.texts)

    def test_with_subobjects(self):
        with open("tests/in/customobject/endzone delay.bytes", 'rb') as f:
            obj = BaseObject(DstBytes(f))

            res = write_read(obj, read_func=LEVEL_PROBER.read)

            win_logic = next(res.iter_children(ty=WinLogic))
            self.assertAlmostEqual(3.0, win_logic.delay_before_broadcast)

    def test_old_section32(self):
        with open("tests/in/customobject/gravtrigger old.bytes", 'rb') as f:
            obj = BaseObject(DstBytes(f))

            res = write_read(obj, read_func=LEVEL_PROBER.read)

            self.assertAlmostEqual(3, res.music_id)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
