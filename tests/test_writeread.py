import unittest

from distance import DefaultProbers
from distance._impl.level_objects.objects import (
    LevelObject, GoldenSimple, InfoDisplayBox, WinLogic,
    OldSimple, WorldText,
)
from distance.levelfragments import (
    MaterialFragment,
)
from distance import Level
from distance.base import Fragment, ObjectFragment
from distance.prober import BytesProber
from tests import common
from tests.common import check_exceptions, write_read, ExtraAssertMixin


Group = DefaultProbers.common.klass('Group')


class UnknownObject(LevelObject):
    pass


class UnknownFragment(Fragment):
    pass


UNK_PROBER = BytesProber(baseclass=UnknownObject)
UNK_FRAG_PROBER = BytesProber(baseclass=UnknownFragment)
UNK_FRAG_PROBER.add_fragment(ObjectFragment)


class UnknownProbers(object):
    level_objects = UNK_PROBER
    level_subobjects = UNK_PROBER
    fragments = UNK_FRAG_PROBER


class WedgeGSTest(ExtraAssertMixin, unittest.TestCase):

    def test_simple(self):
        orig = GoldenSimple(type='WedgeGS')
        orig.image_index = 39

        res = write_read(orig)[0]

        self.assertEqual(39, res.image_index)

    def test_properties(self):
        orig = GoldenSimple(type='WedgeGS')

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

        res = write_read(orig)[0]

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

    def test_children_section(self):
        """Distance requires an (even empty) list of children for some objects."""
        orig = GoldenSimple(type='WedgeGS')

        res = write_read(orig)[0]

        self.assertTrue(res.fragments[0].has_children)

    def test_mat_color_delete(self):
        orig = GoldenSimple(type='WedgeGS')

        del orig.mat_spec

        self.assertFalse(hasattr(orig, 'mat_spec'))


class GroupTest(unittest.TestCase):

    def test_empty(self):
        orig = Group()

        res = write_read(orig)[0]

        self.assertEqual(0, len(res.children))

    def test_children(self):
        orig = Group(children=[Group()])

        res = write_read(orig)[0]

        self.assertEqual(1, len(res.children))
        self.assertEqual(Group, type(res.children[0]))

    def test_custom_name(self):
        orig = Group(custom_name='test group')

        res = write_read(orig)[0]

        self.assertEqual('test group', res.custom_name)


class GroupWriteReadTest(common.WriteReadTest):

    read_obj = Group

    filename = "tests/in/customobject/2cubes.bytes"

    def verify_obj(self, obj):
        check_exceptions(obj)
        self.assertEqual(3, len(obj.sections))
        self.assertEqual("2cubes", obj.custom_name)


class WorldTextTest(common.WriteReadTest):

    read_obj = WorldText

    filename = "tests/in/customobject/worldtext 1.bytes"

    def verify_obj(self, obj):
        self.assertEqual("Test text", obj.text)


class WorldTextV2Test(common.WriteReadTest):

    read_obj = WorldText

    filename = "tests/in/customobject/worldtext weird.bytes"

    def verify_obj(self, obj):
        self.assertEqual("Zero-G", obj.text)


class ChangeTypeTest(unittest.TestCase):

    def test_writeread(self):
        orig = OldSimple("tests/in/customobject/oldsimple cube.bytes")
        orig.type = 'Cylinder'

        res = write_read(orig)[0]

        self.assertEqual('Cylinder', res.type)


class OldSimpleWriteReadTest(ExtraAssertMixin, common.WriteReadTest):

    read_obj = OldSimple

    filename = "tests/in/customobject/oldsimple cube.bytes"

    def verify_obj(self, obj):
        self.assertSeqAlmostEqual((1, 1, 1, .5), obj.color_diffuse)
        self.assertSeqAlmostEqual((50, 50, 50), obj.transform[2])
        self.assertFalse(hasattr(obj, 'color_emit'))


class OldSimpleTest(ExtraAssertMixin, unittest.TestCase):

    def test_init(self):
        self.assertEqual('Cylinder', OldSimple(shape='Cylinder').type)
        self.assertEqual('CylinderWithCollision',
                         OldSimple(shape='Cylinder', with_collision=True).type)
        self.assertEqual('EmissiveCylinder',
                         OldSimple(shape='Cylinder', emissive=True).type)

    def test_setters(self):
        obj = OldSimple()
        obj.shape='Ring'
        self.assertEqual('Ring', obj.type)
        obj.with_collision = True
        self.assertEqual('RingWithCollision', obj.type)
        obj.emissive = True
        self.assertEqual('EmissiveRingWithCollision', obj.type)

    def test_get_collision(self):
        self.assertTrue(OldSimple(type='RingWithCollision').with_collision)
        self.assertFalse(OldSimple(type='EmissiveCube').with_collision)

    def test_get_emissive(self):
        self.assertTrue(OldSimple(type='EmissiveCube').emissive)
        self.assertFalse(OldSimple(type='RingWithCollision').emissive)

    def test_get_shape(self):
        self.assertEqual('Cylinder', OldSimple(type='Cylinder').shape)
        self.assertEqual('Ring', OldSimple(type='RingWithCollision').shape)
        self.assertEqual('Cone', OldSimple(type='EmissiveConeWithCollision').shape)


class UnknownTest(common.WriteReadTest):

    filename = "tests/in/customobject/infodisplaybox 1.bytes"
    def read_obj_pre(self, db, **kw):
        return DefaultProbers.level_objects.read(db, probers=UnknownProbers(), **kw)
    read_obj = InfoDisplayBox

    def verify_obj(self, obj):
        self.assertEqual(["Text0", "Text1", "Text2", "", "Text4"], obj.texts)


class UnknownSubobjectsTest(common.WriteReadTest):

    filename = "tests/in/customobject/endzone delay.bytes"
    def read_obj_pre(self, db, **kw):
        return DefaultProbers.level_objects.read(db, probers=UnknownProbers(), **kw)
    read_obj = DefaultProbers.level_objects.read

    def verify_obj(self, obj):
        win_logic = next(obj.iter_children(ty=WinLogic))
        self.assertAlmostEqual(3.0, win_logic.delay_before_broadcast)


class UnknownSection32Test(common.WriteReadTest):

    filename = "tests/in/customobject/gravtrigger old.bytes"
    def read_obj_pre(self, db, **kw):
        return DefaultProbers.level_objects.read(db, probers=UnknownProbers(), **kw)
    read_obj = DefaultProbers.level_objects.read

    def verify_obj(self, obj):
        check_exceptions(obj)
        self.assertIsNone(obj.trigger_radius)


class TracknodeFragmentTest(common.WriteReadTest):

    filename = "tests/in/customobject/splineroad.bytes"
    read_obj = LevelObject

    def verify_obj(self, obj):
        node0 = obj.children[0]['TrackNode']
        node1 = obj.children[1]['TrackNode']
        self.assertEqual(79, node0.parent_id)
        self.assertEqual(59, node0.snap_id)
        self.assertEqual(79, node1.parent_id)
        self.assertEqual(100, node1.snap_id)


class MaterialFragmentTest(common.WriteReadTest):

    filename = "tests/in/customobject/splineroad.bytes"
    read_obj = LevelObject

    def verify_obj(self, obj):
        frag = obj['Material']
        mats = frag.materials
        panel_color = mats['empire_panel_light']['_Color']
        self.assertAlmostEqual(0.50588, panel_color[0], places=5)
        self.assertAlmostEqual(0.50588, panel_color[1], places=5)
        self.assertAlmostEqual(0.50588, panel_color[2], places=5)
        self.assertAlmostEqual(1.00000, panel_color[3], places=5)
        self.assertEqual(4, len(mats))
        self.assertEqual([2, 3, 3, 3], [len(cols) for cols in mats.values()])


class MaterialFragmentNoEntriesTest(common.WriteReadTest):

    filename = "tests/in/fragment/material no entries.frag"

    read_obj = MaterialFragment

    def verify_obj(self, obj):
        self.assertEqual({}, dict(obj.materials))


class LevelTest(common.WriteReadTest):

    filename = "tests/in/level/test-straightroad.bytes"
    read_obj = Level

    def verify_obj(self, obj):
        self.assertEqual(6, len(obj.layers[0].objects))


# vim:set sw=4 ts=8 sts=4 et:
