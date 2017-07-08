#!/usr/bin/python
# File:        level.py
# Description: level
# Created:     2017-06-28


import unittest
import sys

if '../' not in sys.path:
    sys.path.append('../')

from distance.level import Level
from distance.bytes import DstBytes, PrintContext, UnexpectedEOFError


class LevelTest(unittest.TestCase):

    def test_level(self):
        with open("in/level/test-straightroad.bytes", 'rb') as f:
            level = Level(DstBytes(f))
            self.assertEqual(level.level_name, "Test-straightroad")

    def test_print_data(self):
        p = PrintContext.for_test()
        with open("in/level/test-straightroad.bytes", 'rb') as f:
            p.print_data_of(Level(DstBytes(f)))

    def test_truncated(self):
        with open("in/level/test-straightroad_truncated.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            level = Level(dbytes)
            self.assertEqual(level.level_name, "Test-straightroad")
            results = [level.read_settings()] + list(level.iter_objects())
            self.assertEqual(len(results), 3)

    def test_truncated2(self):
        with open("in/level/test-straightroad_truncated_2.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            level = Level(dbytes)
            self.assertEqual(level.level_name, "Test-straightroad")
            gen = level.iter_objects()
            obj, sane, exc = level.read_settings()
            obj, sane, exc = next(gen)
            with self.assertRaises(UnexpectedEOFError):
                raise AssertionError(next(gen))

    def test_invalid_str(self):
        with open("in/level/invalid-groupname.bytes", 'rb') as f:
            level = Level(DstBytes(f))
            self.assertEqual(level.level_name, "Test Group")
            settings = level.read_settings()
            gen = level.iter_objects()
            results = list(level.iter_objects())
            self.assertEqual(len(results), 5)
            for i, (obj, sane, exc) in enumerate(results):
                self.assertIsNotNone(obj, f"i == {i}")
                self.assertTrue(sane, f"i == {i}")
                self.assertEqual(exc, obj.exception)
                if i == 2:
                    self.assertIsInstance(exc, UnicodeError)
                else:
                    self.assertIsNone(exc, f"i == {i}")


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
