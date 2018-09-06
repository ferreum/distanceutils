import unittest

from distance import DefaultClasses
from distance.base import Fragment
from distance.levelobjects import MaterialFragment
from distance._impl.fragments.levelfragments import (
    TrackNodeFragment,
    AnimatorFragment,
    EventListenerFragment,
)
from distance._impl.fragments.npfragments import (
    NamedPropertiesFragment,
    PopupBlockerLogicFragment,
    ObjectSpawnCircleFragment,
    StructNamedProperty,
)
from distance._impl.level_objects.objects import EventTrigger
from distance.bytes import SKIP_BYTES, DstBytes, Section, Magic, S_UINT
from tests import common
from tests.common import ExtraAssertMixin, write_read


class Base(object):

    class WriteReadTest(common.WriteReadTest):

        prober = DefaultClasses.fragments

        def test_clone(self):
            obj = self.read_obj_pre(self.filename)
            modified = self.modify_obj(obj)

            cloned = modified.clone()
            res, buf = write_read(cloned, read_func=self.read_obj)

            self.verify_obj(res)

        def test_probe(self):
            res = self.prober.read(self.filename)
            res = self.modify_obj(res)

            self.assertEqual(self.read_obj, type(res))
            self.verify_obj(res)


class UnknownTest(Base.WriteReadTest):

    filename = "tests/in/fragment/material splineroad.frag"

    read_obj_pre = Fragment

    read_obj = MaterialFragment

    def verify_obj(self, frag):
        MaterialTest.verify_obj(self, frag)


class CreateTest(unittest.TestCase):

    def test_write_cloned_created(self):
        frag = Fragment(raw_data=b'')

        clone = frag.clone()

        clone.container = Section(Magic[3], 1, 0)

        db = DstBytes.in_memory()
        clone.write(db)
        db.seek(0)
        res = Section(db)

        self.assertEqual(Section(Magic[3], 1, 0).to_key(), res.to_key())
        self.assertEqual(0, res.content_size)


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


class AnimatorFragmentV7Test(ExtraAssertMixin, Base.WriteReadTest):

    filename = "tests/in/fragment/animator v7.frag"

    read_obj = AnimatorFragment

    def verify_obj(self, frag):
        self.assertEqual(7, frag.container.version)
        self.assertEqual(5, frag.motion_mode)
        self.assertEqual(1, frag.do_scale)
        self.assertSeqAlmostEqual((0.601, 0.602, 0.603), frag.scale_exponents)
        self.assertEqual(1, frag.do_rotate)
        self.assertSeqAlmostEqual((0.501, 0.502, 0.503), frag.rotate_axis)
        self.assertEqual(0, frag.rotate_global)
        self.assertAlmostEqual(0.504, frag.rotate_magnitude)
        self.assertSeqAlmostEqual((0.105, 0.106, 0.107), frag.centerpoint)
        self.assertEqual(4, frag.translate_type)
        self.assertSeqAlmostEqual((0.456, 0.457, 0.458), frag.translate_vector)
        self.assertAlmostEqual(0.801, frag.follow_track_distance)
        self.assertAlmostEqual(None, frag.double_pivot_distance)
        self.assertEqual(None, frag.follow_percent_of_track)
        self.assertEqual(None, frag.wrap_around)
        self.assertSeqAlmostEqual((0.901, 0.902, 0.903), frag.projectile_gravity)
        self.assertAlmostEqual(0.701, frag.delay)
        self.assertAlmostEqual(0.702, frag.duration)
        self.assertAlmostEqual(0.703, frag.time_offset)
        self.assertEqual(1, frag.do_loop)
        self.assertEqual(1, frag.extrapolation_type)
        self.assertEqual(6, frag.curve_type)
        self.assertAlmostEqual(0.704, frag.editor_anim_time)
        self.assertEqual(1, frag.use_custom_pong_values)
        self.assertAlmostEqual(0.721, frag.pong_delay)
        self.assertAlmostEqual(0.722, frag.pong_duration)
        self.assertEqual(6, frag.pong_curve_type)
        self.assertEqual(1, frag.anim_physics)
        self.assertEqual(0, frag.always_animate)
        self.assertEqual(2, frag.default_action)
        self.assertEqual(3, frag.trigger_on_action)
        self.assertEqual(1, frag.trigger_wait_for_anim_finish)
        self.assertEqual(1, frag.trigger_on_reset)
        self.assertEqual(3, frag.trigger_off_action)
        self.assertEqual(1, frag.trigger_off_wait_for_anim_finish)
        self.assertEqual(1, frag.trigger_off_reset)


class AnimatorFragmentV10Test(ExtraAssertMixin, Base.WriteReadTest):

    filename = "tests/in/fragment/animator v10.frag"

    read_obj = AnimatorFragment

    def verify_obj(self, frag):
        self.assertEqual(10, frag.container.version)
        self.assertEqual(5, frag.motion_mode)
        self.assertEqual(1, frag.do_scale)
        self.assertSeqAlmostEqual((0.601, 0.602, 0.603), frag.scale_exponents)
        self.assertEqual(1, frag.do_rotate)
        self.assertSeqAlmostEqual((0.501, 0.502, 0.503), frag.rotate_axis)
        self.assertEqual(0, frag.rotate_global)
        self.assertAlmostEqual(0.504, frag.rotate_magnitude)
        self.assertSeqAlmostEqual((0.105, 0.106, 0.107), frag.centerpoint)
        self.assertEqual(4, frag.translate_type)
        self.assertSeqAlmostEqual((0.456, 0.457, 0.458), frag.translate_vector)
        self.assertAlmostEqual(0.801, frag.follow_track_distance)
        self.assertAlmostEqual(None, frag.double_pivot_distance)
        self.assertEqual(0, frag.follow_percent_of_track)
        self.assertEqual(1, frag.wrap_around)
        self.assertSeqAlmostEqual((0.901, 0.902, 0.903), frag.projectile_gravity)
        self.assertAlmostEqual(0.701, frag.delay)
        self.assertAlmostEqual(0.702, frag.duration)
        self.assertAlmostEqual(0.703, frag.time_offset)
        self.assertEqual(1, frag.do_loop)
        self.assertEqual(None, frag.extrapolation_type)
        self.assertEqual(0, frag.do_extend)
        self.assertEqual(6, frag.curve_type)
        self.assertAlmostEqual(0.704, frag.editor_anim_time)
        self.assertEqual(1, frag.use_custom_pong_values)
        self.assertAlmostEqual(0.721, frag.pong_delay)
        self.assertAlmostEqual(0.722, frag.pong_duration)
        self.assertEqual(6, frag.pong_curve_type)
        self.assertEqual(1, frag.anim_physics)
        self.assertEqual(0, frag.always_animate)
        self.assertEqual(4, frag.default_action)
        self.assertEqual(3, frag.trigger_on_action)
        self.assertEqual(1, frag.trigger_wait_for_anim_finish)
        self.assertEqual(1, frag.trigger_on_reset)
        self.assertEqual(3, frag.trigger_off_action)
        self.assertEqual(1, frag.trigger_off_wait_for_anim_finish)
        self.assertEqual(1, frag.trigger_off_reset)


class AnimatorFragmentV11Test(ExtraAssertMixin, Base.WriteReadTest):

    filename = "tests/in/fragment/animator v11.frag"

    read_obj = AnimatorFragment

    def verify_obj(self, frag):
        self.assertEqual(11, frag.container.version)
        self.assertEqual(5, frag.motion_mode)
        self.assertEqual(1, frag.do_scale)
        self.assertSeqAlmostEqual((0.601, 0.602, 0.603), frag.scale_exponents)
        self.assertEqual(1, frag.do_rotate)
        self.assertSeqAlmostEqual((0.501, 0.502, 0.503), frag.rotate_axis)
        self.assertEqual(0, frag.rotate_global)
        self.assertAlmostEqual(0.504, frag.rotate_magnitude)
        self.assertSeqAlmostEqual((0.105, 0.106, 0.107), frag.centerpoint)
        self.assertEqual(4, frag.translate_type)
        self.assertSeqAlmostEqual((0.456, 0.457, 0.458), frag.translate_vector)
        self.assertAlmostEqual(0.801, frag.follow_track_distance)
        self.assertAlmostEqual(1.802, frag.double_pivot_distance)
        self.assertEqual(0, frag.follow_percent_of_track)
        self.assertEqual(1, frag.wrap_around)
        self.assertSeqAlmostEqual((0.901, 0.902, 0.903), frag.projectile_gravity)
        self.assertAlmostEqual(0.701, frag.delay)
        self.assertAlmostEqual(0.702, frag.duration)
        self.assertAlmostEqual(0.703, frag.time_offset)
        self.assertEqual(1, frag.do_loop)
        self.assertEqual(None, frag.extrapolation_type)
        self.assertEqual(0, frag.do_extend)
        self.assertEqual(6, frag.curve_type)
        self.assertAlmostEqual(0.704, frag.editor_anim_time)
        self.assertEqual(1, frag.use_custom_pong_values)
        self.assertAlmostEqual(0.721, frag.pong_delay)
        self.assertAlmostEqual(0.722, frag.pong_duration)
        self.assertEqual(6, frag.pong_curve_type)
        self.assertEqual(1, frag.anim_physics)
        self.assertEqual(0, frag.always_animate)
        self.assertEqual(4, frag.default_action)
        self.assertEqual(3, frag.trigger_on_action)
        self.assertEqual(1, frag.trigger_wait_for_anim_finish)
        self.assertEqual(1, frag.trigger_on_reset)
        self.assertEqual(3, frag.trigger_off_action)
        self.assertEqual(1, frag.trigger_off_wait_for_anim_finish)
        self.assertEqual(1, frag.trigger_off_reset)


class EventListenerV1Test(Base.WriteReadTest):

    filename = 'tests/in/fragment/eventlistener v1.frag'

    read_obj = EventListenerFragment

    def verify_obj(self, frag):
        self.assertEqual(frag.event_name, "Test Event")
        self.assertEqual(None, frag.delay)


class EventListenerV2Test(Base.WriteReadTest):

    filename = 'tests/in/fragment/eventlistener v2.frag'

    read_obj = EventListenerFragment

    def verify_obj(self, frag):
        self.assertEqual(frag.event_name, "Test Event")
        self.assertAlmostEqual(frag.delay, 9.99, places=5)


class AnimatorFragmentCreateTest(unittest.TestCase):

    def test_create_write_read(self):
        frag = AnimatorFragment(motion_mode=4)

        res, rdb = write_read(frag)

        self.assertEqual(res.motion_mode, 4)


class EventTriggerFragmentTest(Base.WriteReadTest):

    filename = 'tests/in/customobject/eventtriggerbox.bytes'
    read_obj = EventTrigger
    prober = DefaultClasses.level_objects

    def verify_obj(self, obj):
        self.assertEqual(obj.type, 'EventTriggerBox')
        self.assertEqual(obj['EventTrigger'].event_name, "Test Event")
        self.assertEqual(obj['EventTrigger'].one_shot, 0)

    def test_clone(self):
        "cannot clone"


class TypedNamedPropertyTest(unittest.TestCase):

    def setUp(self):

        class TestFragment(NamedPropertiesFragment):
            uint_prop = StructNamedProperty('a_uint', S_UINT, default="default")

        self.frag = TestFragment()

    def test_get(self):
        self.frag.props['a_uint'] = b'\x06\x01\x00\x00'
        self.assertEqual(self.frag.uint_prop, 262)

    def test_get_default(self):
        self.assertEqual(self.frag.uint_prop, "default")

    def test_get_skip(self):
        self.frag.props['a_uint'] = SKIP_BYTES
        self.assertEqual(self.frag.uint_prop, "default")

    def test_set(self):
        self.frag.uint_prop = 4
        self.assertEqual(self.frag.props['a_uint'], b'\x04\x00\x00\x00')

    def test_del(self):
        self.frag.props['a_uint'] = b'\x04\x00\x00\x00'
        del self.frag.uint_prop
        self.assertTrue('a_uint' not in self.frag.props)


# vim:set sw=4 ts=8 sts=4 et:
