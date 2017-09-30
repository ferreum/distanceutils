import unittest

from distance.profileprogress import ProfileProgress
from distance.bytes import DstBytes
from distance.printing import PrintContext
from distance.constants import Completion, Mode
from .common import check_exceptions


class ProfileProgressTest(unittest.TestCase):

    def test_read_new(self):
        with open("tests/in/profileprogress/new profile.bytes", 'rb') as f:
            obj = ProfileProgress(DstBytes(f))
            self.assertEqual([], obj.levels[:])

    def test_read_single_map_started(self):
        with open("tests/in/profileprogress/started acclivity.bytes", 'rb') as f:
            obj = ProfileProgress(DstBytes(f))
            levels = obj.levels
            self.assertEqual(len(levels), 1)
            check_exceptions(levels[0])
            self.assertEqual(levels[0].completion[Mode.SPRINT], Completion.STARTED)

    def test_read_single_map_diamond(self):
        with open("tests/in/profileprogress/diamond acclivity.bytes", 'rb') as f:
            obj = ProfileProgress(DstBytes(f))
            levels = obj.levels
            self.assertEqual(len(levels), 1)
            check_exceptions(levels[0])
            self.assertEqual(levels[0].completion[Mode.SPRINT], Completion.DIAMOND)
            stats = obj.stats
            check_exceptions(stats)
            self.assertEqual(13, stats.stats['impacts'])

    def test_print_data(self):
        p = PrintContext.for_test()
        with open("tests/in/profileprogress/diamond acclivity.bytes", 'rb') as f:
            p.print_data_of(ProfileProgress(DstBytes(f)))

    def test_levels_version2(self):
        p = PrintContext.for_test()
        with open("tests/in/profileprogress/levels_version_2.bytes", 'rb') as f:
            p.print_data_of(ProfileProgress(DstBytes(f)))

    def test_print_new(self):
        p = PrintContext.for_test()
        with open("tests/in/profileprogress/new profile.bytes", 'rb') as f:
            p.print_data_of(ProfileProgress(DstBytes(f)))

    def test_unlocked_adventure(self):
        p = PrintContext.for_test()
        with open("tests/in/profileprogress/unlocked adventure.bytes", 'rb') as f:
            p.print_data_of(ProfileProgress(DstBytes(f)))


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
