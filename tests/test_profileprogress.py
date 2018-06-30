import unittest

from distance.profileprogress import ProfileProgress
from distance.printing import PrintContext
from distance.constants import Completion, Mode
from distance import DefaultProbers
from .common import check_exceptions, write_read


class ProfileProgressTest(unittest.TestCase):

    def test_probe(self):
        obj = DefaultProbers.file.read("tests/in/profileprogress/new profile.bytes")
        self.assertEqual(type(obj), ProfileProgress)

    def test_read_new(self):
        obj = ProfileProgress("tests/in/profileprogress/new profile.bytes")
        self.assertEqual(0, len(obj.levels[:]))

    def test_read_single_map_started(self):
        obj = ProfileProgress("tests/in/profileprogress/started acclivity.bytes")
        check_exceptions(obj)
        levels = obj.levels
        self.assertEqual(len(levels), 1)
        self.assertEqual(levels[0].completion[Mode.SPRINT], Completion.STARTED)

    def test_read_single_map_diamond(self):
        obj = ProfileProgress("tests/in/profileprogress/diamond acclivity.bytes")
        check_exceptions(obj)
        levels = obj.levels
        self.assertEqual(len(levels), 1)
        self.assertEqual(levels[0].completion[Mode.SPRINT], Completion.DIAMOND)
        stats = obj.stats
        check_exceptions(stats)
        self.assertEqual(13, stats.impacts)

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

    def test_trackmogrify_mods(self):
        obj = ProfileProgress("tests/in/profileprogress/stats_version_1 trackmogrify.bytes")
        self.assertEqual(obj.stats.trackmogrify_mods, ["insanely", "short"])

    def test_modify_write_read_progress(self):
        obj = ProfileProgress("tests/in/profileprogress/unlocked adventure.bytes")
        obj.officials[0] = "monolith"

        res, rdb = write_read(obj)

        self.assertEqual(res.officials, ["monolith"])

    def test_modify_write_read_stats(self):
        obj = ProfileProgress("tests/in/profileprogress/unlocked adventure.bytes")
        obj.stats.horns = 10003445333456

        res, rdb = write_read(obj)

        self.assertEqual(res.stats.horns, 10003445333456)


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et:
