#!/usr/bin/python
# File:        replay.py
# Description: replay
# Created:     2017-06-28


import unittest
import sys

if '../' not in sys.path:
    sys.path.append('../')

from distance.replay import Replay
from distance.bytes import DstBytes


def assertColor(first, second):
    for a, b in zip(first, second):
        if abs(a - b) > 0.001:
            raise AssertionError(f"colors don't match: {first} {second}")


class Version3Test(unittest.TestCase):

    def test_version3(self):
        with open("in/replay/version_3.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            replay = Replay(dbytes)
            self.assertEqual(replay.player_name, "Ferreus")
            self.assertEqual(replay.player_name_2, "Ferreus")
            self.assertEqual(replay.player_id, 76561198040630941)
            self.assertEqual(replay.finish_time, 4650)
            self.assertEqual(replay.car_name, "Refractor")
            assertColor(replay.car_color_primary, (0.193919882, 0, 0.0355945863, 1))
            assertColor(replay.car_color_secondary, (0.193919882, 0, 0.0355945863, 1))
            assertColor(replay.car_color_glow, (1, 0, 0.26908654, 1))
            assertColor(replay.car_color_sparkle, (1, 0, 0.6303446, 1))
            self.assertEqual(replay.version, 3)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
