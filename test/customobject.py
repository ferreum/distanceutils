#!/usr/bin/python
# File:        customobject.py
# Description: customobject
# Created:     2017-07-03


import unittest
import sys
import math

if '../' not in sys.path:
    sys.path.append('../')

from distance.level import PROBER
from distance.bytes import DstBytes, PrintContext
from distance.constants import ForceType


def results_with_groups(gen):
    for obj, sane, exc in gen:
        yield obj, sane, exc
        if obj.has_children:
            yield from results_with_groups(obj.iter_children())


class InfoDisplayBoxTest(unittest.TestCase):

    def test_parse(self):
        with open("in/customobject/infodisplaybox 1.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.texts, ["Text0", "Text1", "Text2", "", "Text4"])

    def test_parse_2(self):
        with open("in/customobject/infodisplaybox 2.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.texts, ["Test_2", "", "", "", ""])

    def test_ver_0(self):
        p = PrintContext.for_test()
        with open("in/customobject/infodisplaybox ver_0.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.texts[0], "Flight ability\ncorrupted")
            p.print_data_of(obj)

    def test_print_data(self):
        p = PrintContext.for_test()
        with open("in/customobject/infodisplaybox 1.bytes", 'rb') as f:
            p.print_data_of(PROBER.parse(DstBytes(f)))


class WorldTextTest(unittest.TestCase):

    def test_parse(self):
        with open("in/customobject/worldtext 1.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.text, "Test text")

    def test_parse_2(self):
        with open("in/customobject/worldtext helloworld.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.text, "Hello World")

    def test_parse_3(self):
        with open("in/customobject/worldtext weird.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.text, "Zero-G")

    def test_print_data(self):
        p = PrintContext.for_test()
        with open("in/customobject/worldtext helloworld.bytes", 'rb') as f:
            p.print_data_of(PROBER.parse(DstBytes(f)))


class TeleExitTest(unittest.TestCase):

    def test_with_checkpoint(self):
        with open("in/customobject/tele exit checkpoint.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.sub_teleporter.trigger_checkpoint, 1)

    def test_without_checkpoint(self):
        with open("in/customobject/tele exit nocheckpoint.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.sub_teleporter.trigger_checkpoint, 0)

    def test_print_data(self):
        p = PrintContext.for_test()
        with open("in/customobject/tele exit nocheckpoint.bytes", 'rb') as f:
            p.print_data_of(PROBER.parse(DstBytes(f)))

    def test_virusspiritspawner(self):
        p = PrintContext.for_test()
        with open("in/customobject/virusspiritspawner.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.sub_teleporter.destination, 6666)
            p.print_data_of(obj)


class GravityTriggerTest(unittest.TestCase):

    def test_default(self):
        with open("in/customobject/gravtrigger default.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.disable_gravity, True)
            self.assertEqual(obj.music_id, 19)
            self.assertEqual(obj.one_time_trigger, True)
            self.assertEqual(obj.disable_music_trigger, False)

    def test_changed(self):
        with open("in/customobject/gravtrigger changed.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.disable_gravity, False)
            self.assertEqual(obj.music_id, 3)
            self.assertEqual(obj.one_time_trigger, False)
            self.assertEqual(obj.disable_music_trigger, True)

    def test_old(self):
        with open("in/customobject/gravtrigger old.bytes", 'rb') as f:
            # only verify we don't error here
            PROBER.parse(DstBytes(f))
            # TODO update when we parse old format

    def test_print_default(self):
        p = PrintContext.for_test()
        with open("in/customobject/gravtrigger default.bytes", 'rb') as f:
            p.print_data_of(PROBER.parse(DstBytes(f)))

    def test_print_changed(self):
        p = PrintContext.for_test()
        with open("in/customobject/gravtrigger changed.bytes", 'rb') as f:
            p.print_data_of(PROBER.parse(DstBytes(f)))


class ForceZoneBoxTest(unittest.TestCase):

    files = ("default", "changed wind", "changed gravity")

    def test_default(self):
        with open(f"in/customobject/forcezone default.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.force_type, ForceType.WIND)
            self.assertEqual(obj.drag_multiplier, 1.0)

    def test_gravity(self):
        with open(f"in/customobject/forcezone changed gravity.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.force_type, ForceType.GRAVITY)
            self.assertEqual(obj.disable_global_gravity, 1)

    def test_print(self):
        for fname in self.files:
            with self.subTest(fname=fname):
                p = PrintContext.for_test()
                with open(f"in/customobject/forcezone {fname}.bytes", 'rb') as f:
                    p.print_data_of(PROBER.parse(DstBytes(f)))


class EnableAbilitiesBoxTest(unittest.TestCase):

    def test_default(self):
        p = PrintContext.for_test()
        with open(f"in/customobject/enableabilitiesbox default.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.abilities.get('EnableFlying', 0), 0)
            p.print_data_of(obj)

    def test_flyboost(self):
        p = PrintContext.for_test()
        with open(f"in/customobject/enableabilitiesbox flyboost.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.abilities['EnableFlying'], 1)
            self.assertEqual(obj.abilities['EnableBoosting'], 1)
            p.print_data_of(obj)


class S5Offset(unittest.TestCase):

    def test_glasssplineroadstraight(self):
        p = PrintContext.for_test()
        with open(f"in/customobject/glasssplineroadstraight s5 offset.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(len(obj.subobjects), 2)
            p.print_data_of(obj)

    def test_jumpbarrierlowhi(self):
        p = PrintContext.for_test()
        with open(f"in/customobject/jumpbarrierlowhi s5 offset.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(len(obj.subobjects), 3)
            p.print_data_of(obj)


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
