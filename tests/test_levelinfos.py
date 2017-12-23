import unittest

from distance.levelinfos import LevelInfos
from distance.printing import PrintContext


class Version0LevelsTest(unittest.TestCase):

    def setUp(self):
        self.infos = LevelInfos("tests/in/levelinfos/LevelInfos.bytes")
        self.levels = self.infos.levels

    def test_length(self):
        self.assertEqual(len(self.levels), 2)

    def test_names(self):
        self.assertEqual('Lost Fortress', self.levels[0].level_name)
        self.assertEqual('Main Menu Datastream', self.levels[1].level_name)

    def test_paths(self):
        self.assertEqual('MyLevels/lost fortress.bytes', self.levels[0].level_path)
        self.assertEqual('MyLevels/main menu datastream.bytes', self.levels[1].level_path)

    def test_basename(self):
        self.assertEqual('lost fortress', self.levels[0].level_basename)
        self.assertEqual('main menu datastream', self.levels[1].level_basename)

    def test_modes(self):
        self.assertEqual({1: 1, 2: 0, 3: 0, 5: 0, 8: 0, 10: 0}, self.levels[0].modes)
        self.assertEqual({1: 0, 2: 0, 5: 0, 8: 0, 13: 1}, self.levels[1].modes)

    def test_times(self):
        exp = [240000, 180000, 135000, 90000]
        for i, time in enumerate(self.levels[0].medal_times):
            self.assertAlmostEqual(exp[i], time)
        exp = [-1, -1, -1, -1]
        for i, time in enumerate(self.levels[1].medal_times):
            self.assertAlmostEqual(exp[i], time)

    def test_scores(self):
        self.assertEqual([0, 0, 0, 0], self.levels[0].medal_scores)
        self.assertEqual([-1, -1, -1, -1], self.levels[1].medal_scores)

    def test_printing_works(self):
        p = PrintContext.for_test()
        p.print_data_of(self.infos)


class Version0EntryVersion2Test(unittest.TestCase):

    def setUp(self):
        self.infos = LevelInfos("tests/in/levelinfos/LevelInfos v2.bytes")
        self.levels = self.infos.levels

    def test_length(self):
        self.assertEqual(len(self.levels), 2)

    def test_description(self):
        desc0 = self.levels[0].description
        self.assertEqual(158, len(desc0))
        self.assertTrue("6th day" in desc0)

        desc1 = self.levels[1].description
        self.assertEqual(56, len(desc1))
        self.assertTrue("real thing" in desc1)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
