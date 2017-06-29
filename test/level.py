#!/usr/bin/python
# File:        level.py
# Description: level
# Created:     2017-06-28


import unittest
import sys

if '../' not in sys.path:
    sys.path.append('../')

from distance.level import Level
from distance.bytes import DstBytes, UnexpectedEOFError


class LevelTest(unittest.TestCase):

    def test_level(self):
        with open("in/level/test-straightroad.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            level = Level(dbytes)
            self.assertEqual(level.level_name, "Test-straightroad")

    def test_truncated(self):
        with open("in/level/test-straightroad_truncated.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            level = Level(dbytes)
            self.assertEqual(level.level_name, "Test-straightroad")
            results = list(level.iter_objects())
            self.assertEqual(len(results), 3)

    def test_truncated2(self):
        with open("in/level/test-straightroad_truncated_2.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            level = Level(dbytes)
            self.assertEqual(level.level_name, "Test-straightroad")
            gen = level.iter_objects()
            obj, sane, exc = next(gen)
            obj, sane, exc = next(gen)
            with self.assertRaises(UnexpectedEOFError):
                raise AssertionError(next(gen))


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
