import unittest

from distance.profileprogress import ProfileProgress
from distance.printing import PrintContext
from distance.constants import Completion, Mode
from .common import check_exceptions


class ProfileProgressTest(unittest.TestCase):

    def test_read_new(self):
        obj = ProfileProgress("tests/in/profileprogress/new profile.bytes")
        self.assertEqual([], obj.levels[:])

    def test_read_single_map_started(self):
        obj = ProfileProgress("tests/in/profileprogress/started acclivity.bytes")
        levels = obj.levels
        self.assertEqual(len(levels), 1)
        check_exceptions(levels[0])
        self.assertEqual(levels[0].completion[Mode.SPRINT], Completion.STARTED)

    def test_read_single_map_diamond(self):
        obj = ProfileProgress("tests/in/profileprogress/diamond acclivity.bytes")
        levels = obj.levels
        self.assertEqual(len(levels), 1)
        check_exceptions(levels[0])
        self.assertEqual(levels[0].completion[Mode.SPRINT], Completion.DIAMOND)
        stats = obj.stats
        check_exceptions(stats)
        self.assertEqual(13, stats.stats['impacts'])

    def test_print_data(self):
        p = PrintContext.for_test()
        obj = ProfileProgress("tests/in/profileprogress/diamond acclivity.bytes")
        p.print_data_of(obj)

    def test_levels_version2(self):
        p = PrintContext.for_test()
        obj = ProfileProgress("tests/in/profileprogress/levels_version_2.bytes")
        p.print_data_of(obj)

    def test_print_new(self):
        p = PrintContext.for_test()
        obj = ProfileProgress("tests/in/profileprogress/new profile.bytes")
        p.print_data_of(obj)

    def test_unlocked_adventure(self):
        p = PrintContext.for_test()
        obj = ProfileProgress("tests/in/profileprogress/unlocked adventure.bytes")
        p.print_data_of(obj)


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
