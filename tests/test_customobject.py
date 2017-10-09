import unittest

from distance.levelobjects import PROBER, SubTeleporter, WinLogic
from distance.fragments import (
    TrackNodeFragment,
    BaseCarScreenTextDecodeTrigger,
    CarScreenTextDecodeTriggerFragment,
    OldCarScreenTextDecodeTriggerFragment,
)
from distance.printing import PrintContext
from distance.constants import ForceType
from .common import check_exceptions


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
        p.print_data_of(obj)

    def test_ver_0_2(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/infodisplaybox ver_0 2.bytes")
        self.assertEqual(obj.texts[0], "Synchronizing with\r\nold <color=#00ff77>checkpoint</color>\r\nnetwork")
        self.assertAlmostEqual(obj.per_char_speed, 0.02)
        p.print_data_of(obj)

    def test_print_data(self):
        p = PrintContext.for_test()
        p.print_data_of(PROBER.read("tests/in/customobject/infodisplaybox 1.bytes"))

    def test_quarantinetrigger(self):
        obj = PROBER.read("tests/in/customobject/quarantinetrigger empty infodisplaylogic.bytes")
        check_exceptions(obj)


class WorldTextTest(unittest.TestCase):

    def test_read(self):
        obj = PROBER.read("tests/in/customobject/worldtext 1.bytes")
        self.assertEqual(obj.text, "Test text")

    def test_read_default_helloworld(self):
        obj = PROBER.read("tests/in/customobject/worldtext helloworld.bytes")
        self.assertIsNone(obj.text, None)
        self.assertFalse(obj.is_skip)

    def test_read_3(self):
        obj = PROBER.read("tests/in/customobject/worldtext weird.bytes")
        self.assertEqual(obj.text, "Zero-G")

    def test_print_data(self):
        p = PrintContext.for_test()
        p.print_data_of(PROBER.read("tests/in/customobject/worldtext helloworld.bytes"))


class TeleExitTest(unittest.TestCase):

    def test_link_id(self):
        obj = PROBER.read("tests/in/customobject/tele exit checkpoint.bytes")
        tele = next(obj.iter_children(name='Teleporter'))
        self.assertIsInstance(tele, SubTeleporter)
        self.assertEqual(tele.link_id, 334)

    def test_with_checkpoint(self):
        obj = PROBER.read("tests/in/customobject/tele exit checkpoint.bytes")
        tele = next(obj.iter_children(name='Teleporter'))
        self.assertIsInstance(tele, SubTeleporter)
        self.assertEqual(tele.trigger_checkpoint, 1)

    def test_without_checkpoint(self):
        obj = PROBER.read("tests/in/customobject/tele exit nocheckpoint.bytes")
        tele = next(obj.iter_children(name='Teleporter'))
        self.assertIsInstance(tele, SubTeleporter)
        self.assertEqual(tele.trigger_checkpoint, 0)

    def test_print_data(self):
        p = PrintContext.for_test()
        p.print_data_of(PROBER.read("tests/in/customobject/tele exit nocheckpoint.bytes"))

    def test_virusspiritspawner(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/virusspiritspawner.bytes")
        tele = next(obj.iter_children(name='Teleporter'))
        self.assertIsInstance(tele, SubTeleporter)
        self.assertEqual(tele.destination, 6666)
        p.print_data_of(obj)


class OldTeleporterTest(unittest.TestCase):

    def test_read(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/tele v0.bytes")
        p.print_data_of(obj)
        tele = next(obj.iter_children(name='Teleporter'))
        self.assertIsInstance(tele, SubTeleporter)
        self.assertEqual(0, tele.link_id)
        self.assertEqual(0, tele.destination)


class SoccerGoalTest(unittest.TestCase):

    def test_read(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/soccergoal.bytes")
        check_exceptions(obj)
        p.print_data_of(obj)


class BatteryBuildingTest(unittest.TestCase):

    # has PulseMaterial, which does NOT contain named properties

    def test_read(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/batterybuilding.bytes")
        check_exceptions(obj)
        p.print_data_of(obj)


class RotatingSpotLightTest(unittest.TestCase):

    def test_read(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/rotatingspotlight.bytes")
        check_exceptions(obj)
        p.print_data_of(obj)


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
        p.print_data_of(PROBER.read("tests/in/customobject/gravtrigger default.bytes"))

    def test_print_changed(self):
        p = PrintContext.for_test()
        p.print_data_of(PROBER.read("tests/in/customobject/gravtrigger changed.bytes"))


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
                p.print_data_of(PROBER.read(filename))


class EnableAbilitiesBoxTest(unittest.TestCase):

    def test_default(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/enableabilitiesbox default.bytes")
        self.assertEqual(obj.abilities.get('EnableFlying', 0), 0)
        self.assertEqual(obj.bloom_out, 1)
        p.print_data_of(obj)

    def test_flyboost(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/enableabilitiesbox flyboost.bytes")
        self.assertEqual(obj.abilities['EnableFlying'], 1)
        self.assertEqual(obj.abilities['EnableBoosting'], 1)
        self.assertEqual(obj.bloom_out, 1)
        p.print_data_of(obj)

    def test_all_off(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/enableabilitiesbox all off.bytes")
        self.assertEqual(obj.abilities['EnableFlying'], 0)
        self.assertEqual(obj.abilities['EnableBoosting'], 0)
        self.assertEqual(obj.bloom_out, 0)
        p.print_data_of(obj)


class S5OffsetTest(unittest.TestCase):

    def test_glasssplineroadstraight(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/glasssplineroadstraight s5 offset.bytes")
        self.assertEqual(len(obj.children), 2)
        p.print_data_of(obj)

    def test_jumpbarrierlowhi(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/jumpbarrierlowhi s5 offset.bytes")
        self.assertEqual(len(obj.children), 3)
        p.print_data_of(obj)


class EmpireEndZoneTest(unittest.TestCase):

    def test_normal(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/endzone.bytes")
        self.assertEqual(len(obj.children), 9)
        win_logic = next(obj.iter_children(name='WinLogic'))
        self.assertEqual(WinLogic, type(win_logic))
        self.assertIsNone(win_logic.delay_before_broadcast)
        p.print_data_of(obj)

    def test_delay_before_broadcast(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/endzone delay.bytes")
        self.assertEqual(len(obj.children), 9)
        win_logic = next(obj.iter_children(name='WinLogic'))
        self.assertEqual(WinLogic, type(win_logic))
        self.assertAlmostEqual(3.0, win_logic.delay_before_broadcast)
        p.print_data_of(obj)

    def test_weird_textmesh(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/endzone weird textmesh.bytes")
        check_exceptions(obj)
        p.print_data_of(obj)


class CarScreenTextDecodeTriggerTest(unittest.TestCase):

    def test_trigger(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/decodetrigger.bytes")
        frag = obj.fragment_by_type(BaseCarScreenTextDecodeTrigger)
        self.assertEqual(CarScreenTextDecodeTriggerFragment, type(frag))
        p.print_data_of(obj)
        self.assertEqual(obj.text, "Please, help us.")
        self.assertEqual(obj.time_text, "")
        self.assertEqual(0, len(obj.announcer_phrases))

    def test_ver0(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/decodetrigger v0.bytes")
        frag = obj.fragment_by_type(BaseCarScreenTextDecodeTrigger)
        self.assertEqual(OldCarScreenTextDecodeTriggerFragment, type(frag))
        p.print_data_of(frag)
        self.assertEqual(obj.text, "INPUT(666\u2020):Extract();")
        self.assertAlmostEqual(obj.per_char_speed, 0.02)
        self.assertEqual(obj.clear_on_finish, True)
        self.assertEqual(obj.destroy_on_trigger_exit, False)
        self.assertEqual(obj.time_text, "Download")
        self.assertEqual(0, len(obj.announcer_phrases))


class SplineRoadTest(unittest.TestCase):

    def test_tracknodes(self):
        p = PrintContext.for_test()
        obj = PROBER.read("tests/in/customobject/splineroad.bytes")
        node0 = obj.children[0].fragment_by_type(TrackNodeFragment)
        node1 = obj.children[1].fragment_by_type(TrackNodeFragment)
        self.assertEqual(79, node0.parent_id)
        self.assertEqual(59, node0.snap_id)
        self.assertEqual(79, node1.parent_id)
        self.assertEqual(100, node1.snap_id)
        p.print_data_of(obj)


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
