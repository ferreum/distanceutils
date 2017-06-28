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
            self.assertEqual(replay.version, 3)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
