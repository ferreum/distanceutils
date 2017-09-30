import unittest

from distance.replay import Replay
from distance.printing import PrintContext


def assertColor(first, second):
    if len(first) != len(second):
        raise AssertionError(f"different number of channels: {first} {second}")
    for a, b in zip(first, second):
        if abs(a - b) > 0.001:
            raise AssertionError(f"colors don't match: {first} {second}")


class Version1Test(unittest.TestCase):

    def test_version1(self):
        replay = Replay("tests/in/replay/version_1.bytes")
        self.assertEqual(replay.player_name, "Ferreus")
        self.assertEqual(replay.player_name_2, None)
        self.assertEqual(replay.player_id, None)
        self.assertEqual(replay.finish_time, 104370)
        self.assertEqual(replay.replay_duration, None)
        self.assertEqual(replay.car_name, "Refractor")
        assertColor(replay.car_color_primary, (0.193919882, 0, 0.0355945863, 1))
        assertColor(replay.car_color_secondary, (0.193919882, 0, 0.0355945863, 1))
        assertColor(replay.car_color_glow, (1, 0, 0.26908654, 1))
        assertColor(replay.car_color_sparkle, (1, 0, 0.6303446, 1))
        self.assertEqual(replay.version, 1)

    def test_print_data(self):
        p = PrintContext.for_test()
        p.print_data_of(Replay("tests/in/replay/version_1.bytes"))


class Version2Test(unittest.TestCase):

    def test_version2(self):
        replay = Replay("tests/in/replay/version_2.bytes")
        self.assertEqual(replay.player_name, "Ferreus")
        self.assertEqual(replay.player_name_2, "Ferreus")
        self.assertEqual(replay.player_id, 76561198040630941)
        self.assertEqual(replay.finish_time, None)
        self.assertEqual(replay.replay_duration, None)
        self.assertEqual(replay.car_name, "Refractor")
        assertColor(replay.car_color_primary, (0.193919882, 0, 0.0355945863, 1))
        assertColor(replay.car_color_secondary, (0.193919882, 0, 0.0355945863, 1))
        assertColor(replay.car_color_glow, (1, 0, 0.26908654, 1))
        assertColor(replay.car_color_sparkle, (1, 0, 0.6303446, 1))
        self.assertEqual(replay.version, 2)

    def test_print_data(self):
        p = PrintContext.for_test()
        p.print_data_of(Replay("tests/in/replay/version_2.bytes"))


class Version3Test(unittest.TestCase):

    def test_version3(self):
        replay = Replay("tests/in/replay/version_3.bytes")
        self.assertEqual(replay.player_name, "Ferreus")
        self.assertEqual(replay.player_name_2, "Ferreus")
        self.assertEqual(replay.player_id, 76561198040630941)
        self.assertEqual(replay.finish_time, 4650)
        self.assertEqual(replay.replay_duration, 4649)
        self.assertEqual(replay.car_name, "Refractor")
        assertColor(replay.car_color_primary, (0.193919882, 0, 0.0355945863, 1))
        assertColor(replay.car_color_secondary, (0.193919882, 0, 0.0355945863, 1))
        assertColor(replay.car_color_glow, (1, 0, 0.26908654, 1))
        assertColor(replay.car_color_sparkle, (1, 0, 0.6303446, 1))
        self.assertEqual(replay.version, 3)

    def test_print_data(self):
        p = PrintContext.for_test()
        p.print_data_of(Replay("tests/in/replay/version_3.bytes"))


class Version4Test(unittest.TestCase):

    def test_version4(self):
        replay = Replay("tests/in/replay/version_4.bytes")
        self.assertEqual(replay.player_name, "Ferreus")
        self.assertEqual(replay.player_name_2, "Ferreus")
        self.assertEqual(replay.player_id, 76561198040630941)
        self.assertEqual(replay.finish_time, 9570)
        self.assertEqual(replay.replay_duration, 9576)
        self.assertEqual(replay.car_name, "Refractor")
        assertColor(replay.car_color_primary, (0.193919882, 0, 0.0355945863, 1))
        assertColor(replay.car_color_secondary, (0.193919882, 0, 0.0355945863, 1))
        assertColor(replay.car_color_glow, (1, 0, 0.26908654, 1))
        assertColor(replay.car_color_sparkle, (1, 0, 0.6303446, 1))
        self.assertEqual(replay.version, 4)

    def test_partial(self):
        replay = Replay.maybe("tests/in/replay/version_4_truncated.bytes")
        self.assertEqual(replay.player_name, "Ferreus")
        self.assertEqual(replay.player_name_2, "Ferreus")
        self.assertEqual(replay.player_id, 76561198040630941)
        self.assertEqual(replay.finish_time, 9570)
        self.assertEqual(replay.replay_duration, 9576)
        self.assertEqual(replay.car_name, "Refractor")
        assertColor(replay.car_color_primary, (0.193919882, 0, 0.0355945863, 1))
        assertColor(replay.car_color_secondary, (0.193919882, 0, 0.0355945863, 1))
        assertColor(replay.car_color_glow, (1, 0, 0.26908654, 1))
        self.assertIsNone(replay.car_color_sparkle)
        self.assertEqual(replay.version, 4)
        self.assertIsNotNone(replay.exception)

    def test_partial_2(self):
        replay = Replay.maybe("tests/in/replay/version_4_truncated_2.bytes")
        self.assertEqual(replay.player_name, "Ferreus")
        self.assertEqual(replay.player_name_2, "Ferreus")
        self.assertEqual(replay.player_id, 76561198040630941)
        self.assertEqual(replay.finish_time, 9570)
        self.assertEqual(replay.replay_duration, 9576)
        self.assertIsNone(replay.car_name)
        self.assertIsNone(replay.car_color_primary)
        self.assertIsNone(replay.car_color_secondary)
        self.assertIsNone(replay.car_color_glow)
        self.assertIsNone(replay.car_color_sparkle)
        self.assertEqual(replay.version, 4)
        self.assertIsNotNone(replay.exception)

    def test_print_data(self):
        p = PrintContext.for_test()
        p.print_data_of(Replay("tests/in/replay/version_4.bytes"))


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
