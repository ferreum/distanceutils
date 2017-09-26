import unittest

from distance.level import Level
from distance.bytes import DstBytes, UnexpectedEOFError
from distance.printing import PrintContext


class LevelTest(unittest.TestCase):

    def test_level(self):
        with open("tests/in/level/test-straightroad.bytes", 'rb') as f:
            level = Level(DstBytes(f))
            self.assertEqual(level.level_name, "Test-straightroad")

    def test_print_data(self):
        p = PrintContext.for_test()
        with open("tests/in/level/test-straightroad.bytes", 'rb') as f:
            p.print_data_of(Level(DstBytes(f)))

    def test_truncated(self):
        with open("tests/in/level/test-straightroad_truncated.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            level = Level(dbytes)
            self.assertEqual(level.level_name, "Test-straightroad")
            results = [level.settings] + list(level.iter_objects())
            self.assertEqual(len(results), 3)

    def test_truncated2(self):
        with open("tests/in/level/test-straightroad_truncated_2.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            level = Level(dbytes)
            self.assertEqual(level.level_name, "Test-straightroad")
            gen = level.iter_objects()
            next(gen)
            obj = next(gen)
            self.assertEqual(UnexpectedEOFError, type(obj.exception))

    def test_invalid_str(self):
        with open("tests/in/level/invalid-groupname.bytes", 'rb') as f:
            level = Level(DstBytes(f))
            self.assertEqual(level.level_name, "Test Group")
            results = list(level.iter_objects())
            self.assertEqual(len(results), 5)
            for i, obj in enumerate(results):
                self.assertIsNotNone(obj, f"i == {i}")
                self.assertTrue(obj.sane_end_pos, f"i == {i}")
                if i == 2:
                    self.assertIsInstance(obj.exception, UnicodeError)
                else:
                    self.assertIsNone(obj.exception, f"i == {i}")


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
