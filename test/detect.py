#!/usr/bin/python
# File:        detect.py
# Description: detect
# Created:     2017-06-28


import unittest
import sys
from contextlib import contextmanager

if '../' not in sys.path:
    sys.path.append('../')

from distance.bytes import DstBytes
from distance.detect import parse


@contextmanager
def bytes_from(name):
    with open(name, 'rb') as f:
        yield DstBytes(f)


class DetectTest(unittest.TestCase):

    def test_levelinfos(self):
        for ver in range(0, 1):
            with self.subTest(version=ver):
                with bytes_from(f"in/levelinfos/version_{ver}.bytes") as dbytes:
                    result = parse(dbytes)
                    self.assertEqual("LevelInfos", type(result).__name__)

    def test_leaderboard(self):
        for ver in range(0, 2):
            with self.subTest(version=ver):
                with bytes_from(f"in/leaderboard/version_{ver}.bytes") as dbytes:
                    result = parse(dbytes)
                    self.assertEqual("Leaderboard", type(result).__name__)

    def test_replay(self):
        for ver in range(1, 5):
            with self.subTest(version=ver):
                with bytes_from(f"in/replay/version_{ver}.bytes") as dbytes:
                    result = parse(dbytes)
                    self.assertEqual("Replay", type(result).__name__)

    def test_level(self):
        for levelfile in ("test-straightroad",):
            with self.subTest(levelfile=levelfile):
                with bytes_from(f"in/level/{levelfile}.bytes") as dbytes:
                    result = parse(dbytes)
                    self.assertEqual("Level", type(result).__name__)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0: