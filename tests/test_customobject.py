import unittest

from distance.levelobjects import PROBER, SubTeleporter, WinLogic
from distance.bytes import DstBytes
from distance.printing import PrintContext
from distance.constants import ForceType


class InfoDisplayBoxTest(unittest.TestCase):

    def test_read(self):
        with open("tests/in/customobject/infodisplaybox 1.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.texts, ["Text0", "Text1", "Text2", "", "Text4"])

    def test_read_2(self):
        with open("tests/in/customobject/infodisplaybox 2.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.texts, ["Test_2", "", "", "", ""])

    def test_ver_0(self):
        p = PrintContext.for_test()
        with open("tests/in/customobject/infodisplaybox ver_0 1.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.texts[0], "Flight ability\ncorrupted")
            p.print_data_of(obj)

    def test_ver_0_2(self):
        p = PrintContext.for_test()
        with open("tests/in/customobject/infodisplaybox ver_0 2.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.texts[0], "Synchronizing with\r\nold <color=#00ff77>checkpoint</color>\r\nnetwork")
            self.assertAlmostEqual(obj.per_char_speed, 0.02)
            p.print_data_of(obj)

    def test_print_data(self):
        p = PrintContext.for_test()
        with open("tests/in/customobject/infodisplaybox 1.bytes", 'rb') as f:
            p.print_data_of(PROBER.read(DstBytes(f)))


class WorldTextTest(unittest.TestCase):

    def test_read(self):
        with open("tests/in/customobject/worldtext 1.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.text, "Test text")

    def test_read_2(self):
        with open("tests/in/customobject/worldtext helloworld.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.text, "Hello World")

    def test_read_3(self):
        with open("tests/in/customobject/worldtext weird.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.text, "Zero-G")

    def test_print_data(self):
        p = PrintContext.for_test()
        with open("tests/in/customobject/worldtext helloworld.bytes", 'rb') as f:
            p.print_data_of(PROBER.read(DstBytes(f)))


class TeleExitTest(unittest.TestCase):

    def test_link_id(self):
        with open("tests/in/customobject/tele exit checkpoint.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            tele = next(obj.iter_children(name='Teleporter'))
            self.assertIsInstance(tele, SubTeleporter)
            self.assertEqual(tele.link_id, 334)

    def test_with_checkpoint(self):
        with open("tests/in/customobject/tele exit checkpoint.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            tele = next(obj.iter_children(name='Teleporter'))
            self.assertIsInstance(tele, SubTeleporter)
            self.assertEqual(tele.trigger_checkpoint, 1)

    def test_without_checkpoint(self):
        with open("tests/in/customobject/tele exit nocheckpoint.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            tele = next(obj.iter_children(name='Teleporter'))
            self.assertIsInstance(tele, SubTeleporter)
            self.assertEqual(tele.trigger_checkpoint, 0)

    def test_print_data(self):
        p = PrintContext.for_test()
        with open("tests/in/customobject/tele exit nocheckpoint.bytes", 'rb') as f:
            p.print_data_of(PROBER.read(DstBytes(f)))

    def test_virusspiritspawner(self):
        p = PrintContext.for_test()
        with open("tests/in/customobject/virusspiritspawner.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            tele = next(obj.iter_children(name='Teleporter'))
            self.assertIsInstance(tele, SubTeleporter)
            self.assertEqual(tele.destination, 6666)
            p.print_data_of(obj)


class GravityTriggerTest(unittest.TestCase):

    def test_default(self):
        with open("tests/in/customobject/gravtrigger default.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.disable_gravity, True)
            self.assertEqual(obj.music_id, 19)
            self.assertEqual(obj.one_time_trigger, True)
            self.assertEqual(obj.disable_music_trigger, False)

    def test_changed(self):
        with open("tests/in/customobject/gravtrigger changed.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.disable_gravity, False)
            self.assertEqual(obj.music_id, 3)
            self.assertEqual(obj.one_time_trigger, False)
            self.assertEqual(obj.disable_music_trigger, True)

    def test_old(self):
        with open("tests/in/customobject/gravtrigger old.bytes", 'rb') as f:
            # only verify we don't error here
            PROBER.read(DstBytes(f))
            # TODO update when we read old format

    def test_print_default(self):
        p = PrintContext.for_test()
        with open("tests/in/customobject/gravtrigger default.bytes", 'rb') as f:
            p.print_data_of(PROBER.read(DstBytes(f)))

    def test_print_changed(self):
        p = PrintContext.for_test()
        with open("tests/in/customobject/gravtrigger changed.bytes", 'rb') as f:
            p.print_data_of(PROBER.read(DstBytes(f)))


class ForceZoneBoxTest(unittest.TestCase):

    files = ("default", "changed wind", "changed gravity")

    def test_default(self):
        with open(f"tests/in/customobject/forcezone default.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.force_type, ForceType.WIND)
            self.assertEqual(obj.drag_multiplier, 1.0)

    def test_gravity(self):
        with open(f"tests/in/customobject/forcezone changed gravity.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.force_type, ForceType.GRAVITY)
            self.assertEqual(obj.disable_global_gravity, 1)

    def test_print(self):
        for fname in self.files:
            with self.subTest(fname=fname):
                p = PrintContext.for_test()
                with open(f"tests/in/customobject/forcezone {fname}.bytes", 'rb') as f:
                    p.print_data_of(PROBER.read(DstBytes(f)))


class EnableAbilitiesBoxTest(unittest.TestCase):

    def test_default(self):
        p = PrintContext.for_test()
        with open(f"tests/in/customobject/enableabilitiesbox default.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.abilities.get('EnableFlying', 0), 0)
            self.assertEqual(obj.bloom_out, 1)
            p.print_data_of(obj)

    def test_flyboost(self):
        p = PrintContext.for_test()
        with open(f"tests/in/customobject/enableabilitiesbox flyboost.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.abilities['EnableFlying'], 1)
            self.assertEqual(obj.abilities['EnableBoosting'], 1)
            self.assertEqual(obj.bloom_out, 1)
            p.print_data_of(obj)

    def test_all_off(self):
        p = PrintContext.for_test()
        with open(f"tests/in/customobject/enableabilitiesbox all off.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(obj.abilities['EnableFlying'], 0)
            self.assertEqual(obj.abilities['EnableBoosting'], 0)
            self.assertEqual(obj.bloom_out, 0)
            p.print_data_of(obj)


class S5OffsetTest(unittest.TestCase):

    def test_glasssplineroadstraight(self):
        p = PrintContext.for_test()
        with open(f"tests/in/customobject/glasssplineroadstraight s5 offset.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(len(obj.children), 2)
            p.print_data_of(obj)

    def test_jumpbarrierlowhi(self):
        p = PrintContext.for_test()
        with open(f"tests/in/customobject/jumpbarrierlowhi s5 offset.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(len(obj.children), 3)
            p.print_data_of(obj)


class EmpireEndZoneTest(unittest.TestCase):

    def test_normal(self):
        p = PrintContext.for_test(flags=('children'))
        with open(f"tests/in/customobject/endzone.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(len(obj.children), 9)
            win_logic = next(obj.iter_children(name='WinLogic'))
            self.assertEqual(WinLogic, type(win_logic))
            self.assertIsNone(win_logic.delay_before_broadcast)
            p.print_data_of(obj)

    def test_delay_before_broadcast(self):
        p = PrintContext.for_test()
        with open(f"tests/in/customobject/endzone delay.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            self.assertEqual(len(obj.children), 9)
            win_logic = next(obj.iter_children(name='WinLogic'))
            self.assertEqual(WinLogic, type(win_logic))
            self.assertAlmostEqual(3.0, win_logic.delay_before_broadcast)
            p.print_data_of(obj)


class CarScreenTextDecodeTriggerTest(unittest.TestCase):

    def test_trigger(self):
        p = PrintContext.for_test()
        with open(f"tests/in/customobject/decodetrigger.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            p.print_data_of(obj)
            self.assertEqual(obj.text, "Please, help us.")
            self.assertEqual(obj.time_text, "")

    def test_ver0(self):
        p = PrintContext.for_test()
        with open(f"tests/in/customobject/decodetrigger v0.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            p.print_data_of(obj.fragments[0])
            self.assertEqual(obj.text, "INPUT(666\u2020):Extract();")
            self.assertAlmostEqual(obj.per_char_speed, 0.02)
            self.assertEqual(obj.clear_on_finish, True)
            self.assertEqual(obj.destroy_on_trigger_exit, False)
            self.assertEqual(obj.time_text, "Download")


class SplineRoadTest(unittest.TestCase):

    def test_tracknodes(self):
        p = PrintContext.for_test()
        with open("tests/in/customobject/splineroad.bytes", 'rb') as f:
            obj = PROBER.read(DstBytes(f))
            node0 = obj.children[0].fragments[0]
            node1 = obj.children[1].fragments[0]
            self.assertEqual(79, node0.parent_id)
            self.assertEqual(59, node0.snap_id)
            self.assertEqual(79, node1.parent_id)
            self.assertEqual(100, node1.snap_id)
            p.print_data_of(obj)


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
