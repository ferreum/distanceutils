#!/usr/bin/python
# File:        level.py
# Description: level
# Created:     2017-06-28


import unittest
import sys

if '../' not in sys.path:
    sys.path.append('../')

from distance.level import Level
from distance.bytes import DstBytes


class LevelTest(unittest.TestCase):

    def test_level(self):
        with open("in/level/test-straightroad.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            level = Level(dbytes)
            self.assertEqual(level.level_name, "Test-straightroad")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
