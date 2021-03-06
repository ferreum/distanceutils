import unittest

from distance import DefaultClasses
from distance.base import (
    ObjectFragment,
    Fragment,
)
from distance._impl.level_objects.objects import (
    SubTeleporter,
    WinLogic,
    GoldenSimple,
    WorldText,
)
from distance._impl.fragments.levelfragments import (
    CarScreenTextDecodeTriggerFragment,
    AnimatorFragment,
)
from distance._impl.fragments.npfragments import (
    NamedPropertiesFragment,
    ByteNamedProperty,
    OldCarScreenTextDecodeTriggerFragment,
)
from distance.printing import PrintContext
from distance.constants import ForceType
from construct import Container
from distance._common import (
    ModesMapperProperty,
    MedalTimesMapperProperty,
    MedalScoresMapperProperty,
)
from . import common
from .common import check_exceptions, write_read


PROBER = DefaultClasses.level_objects


def TagFragment(name, tag, **kw):
    kw['class_tag'] = tag
    return type(name, (Fragment,), kw)


class InfoDisplayBoxTest(unittest.TestCase):

    def test_read(self):
        obj = PROBER.read("tests/in/customobject/infodisplaybox 1.bytes")
        self.assertEqual(obj.texts, ["Text0", "Text1", "Text2", "", "Text4"])

    def test_read_2(self):
        obj = PROBER.read("tests/in/customobject/infodisplaybox 2.bytes")
        self.assertEqual(obj.texts, ["Test_2", "", "", "", ""])

    def test_ver_0(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/infodisplaybox ver_0 1.bytes")
        self.assertEqual(obj.texts[0], "Flight ability\ncorrupted")
        p.print_object(obj)

    def test_ver_0_2(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/infodisplaybox ver_0 2.bytes")
        self.assertEqual(obj.texts[0], "Synchronizing with\r\nold <color=#00ff77>checkpoint</color>\r\nnetwork")
        self.assertAlmostEqual(obj.per_char_speed, 0.02)
        p.print_object(obj)

    def test_print(self):
        p = PrintContext.for_test()
        p.print_object(PROBER.read("tests/in/customobject/infodisplaybox 1.bytes"))

    def test_quarantinetrigger(self):
        obj = PROBER.read("tests/in/customobject/quarantinetrigger empty infodisplaylogic.bytes")
        check_exceptions(obj)
        PrintContext.for_test().print_object(obj)


class InfoDisplayBoxV2WriteReadTest(common.WriteReadTest):

    filename = "tests/in/customobject/infodisplaybox 1.bytes"
    read_obj = PROBER.read

    def verify_obj(self, obj):
        self.assertEqual(obj.texts[0], "Text0")


class WorldTextTest(unittest.TestCase):

    def test_read(self):
        obj = PROBER.read("tests/in/customobject/worldtext 1.bytes")
        self.assertEqual(obj.text, "Test text")

    def test_read_default_helloworld(self):
        obj = PROBER.read("tests/in/customobject/worldtext helloworld.bytes")
        self.assertIsNone(obj.text, None)

    def test_read_3(self):
        obj = PROBER.read("tests/in/customobject/worldtext weird.bytes")
        self.assertEqual(obj.text, "Zero-G")

    def test_print(self):
        p = PrintContext.for_test()
        p.print_object(PROBER.read("tests/in/customobject/worldtext helloworld.bytes"))

    def test_create(self):
        obj = WorldText(text="test")
        res, rdb = write_read(obj)
        self.assertEqual(res.text, "test")


class TeleporterTest(unittest.TestCase):

    def test_link_id(self):
        obj = PROBER.read("tests/in/customobject/tele exit checkpoint.bytes")
        tele = next(obj for obj in obj.children if obj.type == 'Teleporter')
        self.assertIsInstance(tele, SubTeleporter)
        self.assertEqual(tele.link_id, 334)

    def test_with_checkpoint(self):
        obj = PROBER.read("tests/in/customobject/tele exit checkpoint.bytes")
        tele = next(obj for obj in obj.children if obj.type == 'Teleporter')
        self.assertIsInstance(tele, SubTeleporter)
        self.assertEqual(tele.trigger_checkpoint, 1)

    def test_without_checkpoint(self):
        obj = PROBER.read("tests/in/customobject/tele exit nocheckpoint.bytes")
        tele = next(obj for obj in obj.children if obj.type == 'Teleporter')
        self.assertIsInstance(tele, SubTeleporter)
        self.assertEqual(tele.trigger_checkpoint, 0)

    def test_print_data(self):
        p = PrintContext.for_test()
        p.print_object(PROBER.read("tests/in/customobject/tele exit nocheckpoint.bytes"))

    def test_virusspiritspawner(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/virusspiritspawner.bytes")
        tele = next(obj for obj in obj.children if obj.type == 'Teleporter')
        self.assertIsInstance(tele, SubTeleporter)
        self.assertEqual(tele.destination, 6666)
        p.print_object(obj)

    def test_build_6641(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/tele build 6641.bytes")
        tele = next(obj for obj in obj.children if obj.type == 'Teleporter')
        self.assertEqual(tele.destination, 3)
        p.print_object(obj)


class OldTeleporterTest(unittest.TestCase):

    def test_read(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/tele v0.bytes")
        p.print_object(obj)
        tele = next(obj for obj in obj.children if obj.type == 'Teleporter')
        self.assertIsInstance(tele, SubTeleporter)
        self.assertEqual(0, tele.link_id)
        self.assertEqual(0, tele.destination)


class SoccerGoalTest(unittest.TestCase):

    def test_read(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/soccergoal.bytes")
        check_exceptions(obj)
        p.print_object(obj)


class BatteryBuildingTest(unittest.TestCase):

    # has PulseMaterial, which does NOT contain named properties

    def test_read(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/batterybuilding.bytes")
        check_exceptions(obj)
        p.print_object(obj)


class RotatingSpotLightTest(unittest.TestCase):

    def test_read(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/rotatingspotlight.bytes")
        check_exceptions(obj)
        p.print_object(obj)


class GravityTriggerTest(unittest.TestCase):

    def test_default(self):
        obj = PROBER.read("tests/in/customobject/gravtrigger default.bytes")
        self.assertEqual(obj.disable_gravity, True)
        self.assertEqual(obj.music_id, 19)
        self.assertEqual(obj.one_time_trigger, True)
        self.assertEqual(obj.disable_music_trigger, False)

    def test_changed(self):
        obj = PROBER.read("tests/in/customobject/gravtrigger changed.bytes")
        self.assertEqual(obj.disable_gravity, False)
        self.assertEqual(obj.music_id, 3)
        self.assertEqual(obj.one_time_trigger, False)
        self.assertEqual(obj.disable_music_trigger, True)

    def test_old(self):
        # only verify we don't error here
        PROBER.read("tests/in/customobject/gravtrigger old.bytes")
        # TODO update when we read old format

    def test_print_default(self):
        p = PrintContext.for_test()
        p.print_object(PROBER.read("tests/in/customobject/gravtrigger default.bytes"))

    def test_print_changed(self):
        p = PrintContext.for_test()
        p.print_object(PROBER.read("tests/in/customobject/gravtrigger changed.bytes"))


class ForceZoneBoxTest(unittest.TestCase):

    files = ("default", "changed wind", "changed gravity")

    def test_default(self):
        obj = PROBER.read("tests/in/customobject/forcezone default.bytes")
        self.assertEqual(obj.force_type, ForceType.WIND)
        self.assertEqual(obj.drag_multiplier, 1.0)

    def test_gravity(self):
        obj = PROBER.read("tests/in/customobject/forcezone changed gravity.bytes")
        self.assertEqual(obj.force_type, ForceType.GRAVITY)
        self.assertEqual(obj.disable_global_gravity, 1)
        self.assertEqual("Custom Zone", obj.custom_name)

    def test_print(self):
        for fname in self.files:
            with self.subTest(fname=fname):
                p = PrintContext.for_test()
                filename = f"tests/in/customobject/forcezone {fname}.bytes"
                p.print_object(PROBER.read(filename))


class EnableAbilitiesBoxTest(unittest.TestCase):

    def test_default(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/enableabilitiesbox default.bytes")
        self.assertEqual(obj.abilities.get('EnableFlying', 0), 0)
        self.assertEqual(obj.enable_boosting, 0)
        self.assertEqual(obj.enable_jumping, 0)
        self.assertEqual(obj.enable_jets, 0)
        self.assertEqual(obj.enable_flying, 0)
        self.assertEqual(obj.bloom_out, 1)
        p.print_object(obj)

    def test_flyboost(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/enableabilitiesbox flyboost.bytes")
        self.assertEqual(obj.abilities['EnableFlying'], 1)
        self.assertEqual(obj.abilities['EnableBoosting'], 1)
        self.assertEqual(obj.enable_boosting, 1)
        self.assertEqual(obj.enable_jumping, 0)
        self.assertEqual(obj.enable_jets, 0)
        self.assertEqual(obj.enable_flying, 1)
        self.assertEqual(obj.bloom_out, 1)
        p.print_object(obj)

    def test_all_off(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/enableabilitiesbox all off.bytes")
        self.assertEqual(obj.abilities['EnableFlying'], 0)
        self.assertEqual(obj.abilities['EnableBoosting'], 0)
        self.assertEqual(obj.enable_boosting, 0)
        self.assertEqual(obj.enable_jumping, 0)
        self.assertEqual(obj.enable_jets, 0)
        self.assertEqual(obj.enable_flying, 0)
        self.assertEqual(obj.bloom_out, 0)
        p.print_object(obj)


class S5OffsetTest(unittest.TestCase):

    def test_glasssplineroadstraight(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/glasssplineroadstraight s5 offset.bytes")
        self.assertEqual(len(obj.children), 2)
        p.print_object(obj)

    def test_jumpbarrierlowhi(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/jumpbarrierlowhi s5 offset.bytes")
        self.assertEqual(len(obj.children), 3)
        p.print_object(obj)


class EmpireEndZoneTest(unittest.TestCase):

    def test_normal(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/endzone.bytes")
        self.assertEqual(len(obj.children), 9)
        win_logic = next(obj for obj in obj.children if obj.type == 'WinLogic')
        self.assertEqual(WinLogic, type(win_logic))
        self.assertIsNone(win_logic.delay_before_broadcast)
        p.print_object(obj)

    def test_delay_before_broadcast(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/endzone delay.bytes")
        self.assertEqual(len(obj.children), 9)
        win_logic = next(obj for obj in obj.children if obj.type == 'WinLogic')
        self.assertEqual(WinLogic, type(win_logic))
        self.assertAlmostEqual(3.0, win_logic.delay_before_broadcast)
        p.print_object(obj)

    def test_weird_textmesh(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/endzone weird textmesh.bytes")
        check_exceptions(obj)
        p.print_object(obj)


class CarScreenTextDecodeTriggerTest(unittest.TestCase):

    def test_trigger(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/decodetrigger.bytes")
        frag = obj['CarScreenTextDecodeTrigger']
        self.assertEqual(CarScreenTextDecodeTriggerFragment, type(frag))
        p.print_object(obj)
        self.assertEqual(obj.text, "Please, help us.")
        self.assertEqual(obj.time_text, "")

    def test_ver0(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/decodetrigger v0.bytes")
        frag = obj['CarScreenTextDecodeTrigger']
        self.assertEqual(OldCarScreenTextDecodeTriggerFragment, type(frag))
        p.print_object(frag)
        self.assertEqual(obj.text, "INPUT(666\u2020):Extract();")
        self.assertAlmostEqual(obj.per_char_speed, 0.02)
        self.assertEqual(obj.clear_on_finish, True)
        self.assertEqual(obj.destroy_on_trigger_exit, False)
        self.assertEqual(obj.time_text, "Download")


class SplineRoadTest(unittest.TestCase):

    def test_tracknodes(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/splineroad.bytes")
        node0 = obj.children[0]['TrackNode']
        node1 = obj.children[1]['TrackNode']
        self.assertEqual(79, node0.parent_id)
        self.assertEqual(59, node0.snap_id)
        self.assertEqual(79, node1.parent_id)
        self.assertEqual(100, node1.snap_id)
        p.print_object(obj)


class CubeGsTest(unittest.TestCase):

    def test_probe(self):
        obj = PROBER.read("tests/in/customobject/2cubes.bytes")
        self.assertEqual(GoldenSimple, type(obj.children[0]))
        self.assertEqual(GoldenSimple, type(obj.children[1]))


class ConstructorTest(unittest.TestCase):

    def test_invalid_attr(self):
        self.assertRaises(AttributeError, GoldenSimple, test_attr=2)

    def test_attr(self):
        obj = GoldenSimple(emit_index=50)
        self.assertEqual(obj.emit_index, 50)


class TestFragments(unittest.TestCase):

    def test_getbytype_after_assign(self):
        old_anim = AnimatorFragment()
        obj = DefaultClasses.level_objects.create('Group')
        obj.fragments = [ObjectFragment(), old_anim]
        obj['Animator']

        new_anim = AnimatorFragment()
        obj.fragments = [ObjectFragment(), new_anim]

        res = obj['Animator']
        self.assertIs(new_anim, res)


class PropertyTest(unittest.TestCase):

    class TestFragment(Fragment):

        medals_list = [
            Container(time=40, score=200),
            Container(time=30, score=400),
            Container(time=20, score=700),
            Container(time=10, score=1000),
        ]

        modes = ModesMapperProperty('modes_list')
        times = MedalTimesMapperProperty('medals_list')
        scores = MedalScoresMapperProperty('medals_list')

    class NamedPropFragment(NamedPropertiesFragment):

        test = ByteNamedProperty('testValue')

    def test_create_modes(self):
        frag = self.TestFragment(modes={})
        self.assertEqual(list(frag.modes_list), [])

    def test_create_times(self):
        frag = self.TestFragment(times=(50, 49, 48, 47))
        self.assertEqual(frag.medals_list, [
            Container(time=50, score=200),
            Container(time=49, score=400),
            Container(time=48, score=700),
            Container(time=47, score=1000),
        ])

    def test_create_scores(self):
        frag = self.TestFragment(scores=(100, 101, 102, 103))
        self.assertEqual(frag.medals_list, [
            Container(time=40, score=100),
            Container(time=30, score=101),
            Container(time=20, score=102),
            Container(time=10, score=103),
        ])

    def test_named_property(self):
        frag = self.NamedPropFragment(test=34)
        self.assertEqual(frag.test, 34)


class SetAbilitiesTriggerDefaultsTest(common.WriteReadTest):

    filename = "tests/in/customobject/SetAbilitiesTrigger 6641 default with cube.bytes"
    read_obj = PROBER.read

    def verify_obj(self, obj):
        frag = obj.children[1]['SetAbilitiesTrigger']
        self.assertEqual(frag.enable_flying, 1)
        self.assertEqual(frag.enable_jumping, 1)
        self.assertEqual(frag.enable_boosting, 1)
        self.assertEqual(frag.enable_jet_rotating, 1)
        self.assertEqual(frag.infinite_cooldown, 0)
        self.assertAlmostEqual(frag.delay, 0.0)
        self.assertEqual(frag.show_ability_alert, 1)
        self.assertEqual(frag.bloom_out, 0)
        self.assertEqual(frag.play_sound, 1)
        self.assertEqual(frag.show_car_screen_image, 1)
        self.assertEqual(frag.timer_text, "downloading")
        self.assertEqual(frag.ignore_in_arcade, 0)
        self.assertEqual(frag.use_slow_mo, 0)
        self.assertAlmostEqual(frag.delay_before_slow_mo, 0.0)
        self.assertAlmostEqual(frag.slow_mo_time_scale, 0.25)
        self.assertAlmostEqual(frag.slow_mo_duration, 2.0)
        self.assertAlmostEqual(frag.glitch_duration_after, 0.66)
        self.assertEqual(frag.visuals_only, 0)


class SetAbilitiesTriggerChangedTest(common.WriteReadTest):

    filename = "tests/in/customobject/SetAbilitiesTrigger 6641 changed with cube.bytes"
    read_obj = PROBER.read

    def verify_obj(self, obj):
        frag = obj.children[0]['SetAbilitiesTrigger']
        self.assertEqual(frag.enable_flying, 0)
        self.assertEqual(frag.enable_jumping, 1)
        self.assertEqual(frag.enable_boosting, 1)
        self.assertEqual(frag.enable_jet_rotating, 0)
        self.assertEqual(frag.infinite_cooldown, 0)
        self.assertAlmostEqual(frag.delay, 0.0)
        self.assertEqual(frag.show_ability_alert, 1)
        self.assertEqual(frag.bloom_out, 0)
        self.assertEqual(frag.play_sound, 1)
        self.assertEqual(frag.show_car_screen_image, 1)
        self.assertEqual(frag.timer_text, "testing")
        self.assertEqual(frag.ignore_in_arcade, 0)
        self.assertEqual(frag.use_slow_mo, 1)
        self.assertAlmostEqual(frag.delay_before_slow_mo, 0.5)
        self.assertAlmostEqual(frag.slow_mo_time_scale, 0.8)
        self.assertAlmostEqual(frag.slow_mo_duration, 10.0)
        self.assertAlmostEqual(frag.glitch_duration_after, 0.66)
        self.assertEqual(frag.play_slow_mo_audio, 1)
        self.assertEqual(frag.visuals_only, 0)


class WarpAnchorDefaultTest(common.WriteReadTest):

    filename = "tests/in/customobject/WarpAnchor 6641 default with sphere.bytes"
    read_obj = PROBER.read

    def verify_obj(self, obj):
        frag = obj.children[0]['WarpAnchor']
        # many omitted
        self.assertEqual(frag.trigger_type, 'sphere')
        self.assertEqual(int(frag.trigger_type), 0)
        self.assertEqual(frag.my_id, 0)
        self.assertEqual(frag.other_id, 0)
        self.assertEqual(frag.type_of_warp, 'there_and_back')
        self.assertEqual(int(frag.type_of_warp), 0)
        self.assertEqual(frag.transition_effect, 'none')
        self.assertEqual(int(frag.transition_effect), 0)
        self.assertAlmostEqual(frag.glitch_intensity, 1.1)
        self.assertEqual(frag.countdown_time_scale, 1.0)
        self.assertEqual(frag.disable_countdown, 0)


class WarpAnchorChangedTest(common.WriteReadTest):

    filename = "tests/in/customobject/WarpAnchor 6641 changed with cube.bytes"
    read_obj = PROBER.read

    def verify_obj(self, obj):
        frag = obj.children[1]['WarpAnchor']
        # many omitted
        self.assertEqual(frag.trigger_type, 'box')
        self.assertEqual(int(frag.trigger_type), 1)
        self.assertEqual(frag.my_id, 15)
        self.assertEqual(frag.other_id, 20)
        self.assertEqual(frag.type_of_warp, 'there_and_back')
        self.assertEqual(int(frag.type_of_warp), 0)
        self.assertEqual(frag.transition_effect, 'teleport_virus')
        self.assertEqual(int(frag.transition_effect), 4)
        self.assertAlmostEqual(frag.glitch_intensity, 4.0)
        self.assertEqual(frag.countdown_time_scale, 2.0)
        self.assertEqual(frag.disable_countdown, 0)


# vim:set sw=4 ts=8 sts=4 et:
