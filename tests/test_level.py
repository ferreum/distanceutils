import unittest

from distance import Level, DefaultClasses
from distance.printing import PrintContext
from distance.bytes import ErrorPosition
from .common import check_exceptions


class LevelTest(unittest.TestCase):

    def test_probe(self):
        obj = DefaultClasses.file.read("tests/in/level/test-straightroad.bytes")
        self.assertEqual(type(obj), Level)

    def test_level(self):
        level = Level("tests/in/level/test-straightroad.bytes")
        self.assertEqual(level.name, "Test-straightroad")
        check_exceptions(level)

    def test_print(self):
        p = PrintContext.for_test()
        p.print_object(Level("tests/in/level/test-straightroad.bytes"))

    def test_truncated(self):
        level = Level.maybe("tests/in/level/test-straightroad_truncated.bytes")
        self.assertEqual(level.name, "Test-straightroad")
        self.assertRaises(EOFError, check_exceptions, level.layers[0].objects[2])
        self.assertRaises(EOFError, check_exceptions, level.layers[0].objects[-1])
        self.assertEqual(len(level.layers), 1)
        self.assertEqual(len(level.layers[0].objects), 3)

    def test_truncated_print(self):
        p = PrintContext(file=None, flags=('offset', 'groups', 'subobjects', 'fragments', 'sections', 'allprops'))
        level = Level.maybe("tests/in/level/test-straightroad_truncated.bytes")
        p.print_object(level.layers[0].objects[1].fragments[0])

    def test_truncated_iter(self):
        level = Level.maybe("tests/in/level/test-straightroad_truncated_2.bytes")
        self.assertEqual(level.name, "Test-straightroad")
        obj = level.layers[0].objects[1]
        self.assertEqual(EOFError, type(obj.exception))

    def test_truncated_seq(self):
        level = Level.maybe("tests/in/level/test-straightroad_truncated_2.bytes")
        self.assertEqual(level.name, "Test-straightroad")
        objs = level.layers[0].objects[:]
        self.assertEqual(2, len(objs))
        self.assertEqual(EOFError, type(objs[-1].exception))

    def test_invalid_str(self):
        level = Level("tests/in/level/invalid-groupname.bytes")
        self.assertEqual(level.name, "Test Group")
        self.assertEqual(len(level.layers), 1)
        self.assertEqual(len(level.layers[0].objects), 5)
        for i, obj in enumerate(level.layers[0].objects):
            self.assertIsNotNone(obj, f"i == {i}")
            self.assertTrue(obj.sane_end_pos, f"i == {i}")
            if i == 2:
                try:
                    check_exceptions(obj)
                except UnicodeError as e:
                    pos = ErrorPosition.first(e)
                    self.assertEqual(pos.start, 0x12f7)
                    self.assertEqual(pos.error, 0x1321)
                else:
                    raise AssertionError("UnicodeError not thrown")
            else:
                check_exceptions(obj)

    def test_settings_version_25(self):
        level = Level("tests/in/level/test straightroad v25.bytes")
        self.assertEqual(level.name, "Test-straightroad v25")

        self.assertEqual("Default", level.layers[0].layer_name)
        self.assertEqual(5, len(level.layers[0].objects))
        self.assertEqual("Background", level.layers[1].layer_name)
        self.assertEqual(1, len(level.layers[1].objects))
        self.assertEqual("UltraPlanet", level.layers[1].objects[0].type)

        check_exceptions(level)

    def test_settings_version_26_author(self):
        level = Level("tests/in/level/test straightroad v26 author.bytes")
        self.assertEqual(level.name, "Test-straightroad v26")

        self.assertEqual("Ferreus", level.settings.author_name)

        check_exceptions(level)


# vim:set sw=4 ts=8 sts=4 et:
