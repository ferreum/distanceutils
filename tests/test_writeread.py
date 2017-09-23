import unittest
from io import BytesIO

from distance.level import WedgeGS, Group
from distance.bytes import DstBytes
from distance.printing import PrintContext
from distance.constants import ForceType


def inflate(obj):
    for child in obj.children:
        inflate(child)


def check_exceptions(obj):
    if obj.exception:
        raise obj.exception
    for child in obj.children:
        check_exceptions(child)


def write_read(obj):
    buf = BytesIO()
    dbytes = DstBytes(buf)

    obj.write(dbytes)
    dbytes.pos = 0
    result = type(obj)(dbytes)

    inflate(result)
    check_exceptions(result)

    return result


class WedgeGSTest(unittest.TestCase):

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

        self.assertEqual((.1, .1, .1, .2), orig.mat_color)
        self.assertEqual((.3, .3, .3, .3), orig.mat_emit)
        self.assertEqual((.1, .1, .1, .4), orig.mat_reflect)
        self.assertEqual((.3, .3, .3, .3), orig.mat_spec)

        self.assertEqual(orig.tex_scale, (2, 2, 2))
        self.assertEqual(orig.tex_offset, (10, 10, -20))
        self.assertEqual(orig.image_index, 23)
        self.assertEqual(orig.emit_index, 5)
        self.assertEqual(orig.flip_tex_uv, 1)
        self.assertEqual(orig.world_mapped, 1)
        self.assertEqual(orig.disable_diffuse, 1)
        self.assertEqual(orig.disable_bump, 1)
        self.assertEqual(orig.bump_strength, 12.5)
        self.assertEqual(orig.disable_reflect, 1)
        self.assertEqual(orig.disable_collision, 1)
        self.assertEqual(orig.additive_transp, 1)
        self.assertEqual(orig.multip_transp, 1)
        self.assertEqual(orig.invert_emit, 1)


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


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
