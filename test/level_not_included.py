#!/usr/bin/python
# File:        level_not_included.py
# Description: level_not_included
# Created:     2017-06-29


import unittest
import sys
import math

if '../' not in sys.path:
    sys.path.append('../')

from distance.level import Level
from distance.bytes import DstBytes, UnexpectedEOFError


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.files = []

    def tearDown(self):
        self.close_files()

    def close_files(self):
        for f in self.files:
            f.close()
        self.files = []

    def getLevel(self, filename):
        f = open(filename, 'rb')
        self.files.append(f)
        self.level = level = Level(DstBytes(f))
        self.results = results = list(level.iter_objects())
        self.objects = objects = [o for o, _, _ in results]
        return level, objects

    def assertTimes(self, *times):
        def normalize(value):
            if math.isnan(value):
                return "NaN"
            return int(value)
        self.assertEqual(tuple(map(normalize, self.objects[0].medal_times)), times)

    def assertScores(self, *scores):
        self.assertEqual(tuple(self.objects[0].medal_scores), scores)


class Version0Test(BaseTest):

    def test_brutal_minimalism(self):
        level, objects = self.getLevel("in/level-not-included/v0/brutal minimalism.bytes")
        self.assertEqual(level.level_name, "Brutal Minimalism")
        self.assertTimes(19149, 31916, 47874, 63832)
        self.assertScores(664, 591, 419, 199)
        self.assertEqual(len(objects), 33)

    def test_the_stretch(self):
        level, objects = self.getLevel("in/level-not-included/v0/the stretch.bytes")
        self.assertEqual(level.level_name, "The Stretch")
        self.assertTimes(105244, 175407, 263111, 350815)
        self.assertScores(3654, 3248, 2307, 1096)
        self.assertEqual(len(objects), 148)


class Version1Test(BaseTest):

    def test_magi(self):
        level, objects = self.getLevel("in/level-not-included/v1/magi.bytes")
        self.assertEqual(level.level_name, "Magi")
        self.assertTimes(195000, 200000, 260000, 320000)
        self.assertEqual(len(objects), 882)

    def test_building_hop(self):
        level, objects = self.getLevel("in/level-not-included/v1/building hop.bytes")
        self.assertEqual(level.level_name, "Building hop")
        self.assertTimes(30302, 50504, 75756, 101009)
        self.assertEqual(len(objects), 69)

    def test_city_of_gold(self):
        level, objects = self.getLevel("in/level-not-included/v1/roller coaster ride.bytes")
        self.assertEqual(level.level_name, "A City Of Gold")
        self.assertTimes(73501, 122502, 183753, 245005)
        self.assertEqual(len(objects), 128)

    def test_many_success(self):
        for name in ("attempt", "car crusher", "city", "construction zone", "contraband delivery", "entanglement",
                     "escape the core", "flashback", "giant butts", "hardcore black", "hexopolis", "hextreme",
                     "optimal routing", "qwe", "racingcars", "returnofandy", "saw ride", "scratchdisk", "solid",
                     "spectagular", "storm belt", "the virus begins", "traps", "upandup", "vertical king"):
            with self.subTest(name=name):
                level, objects = self.getLevel(f"in/level-not-included/v1/{name}.bytes")
                for obj, sane, exc in self.results:
                    self.assertIsNone(exc)
                    self.assertIsNone(obj.exception)
                    self.assertTrue(sane)
            self.close_files()


class Version3Test(BaseTest):

    def test_fall_running(self):
        level, objects = self.getLevel("in/level-not-included/v3/fall running.bytes")
        self.assertEqual(level.level_name, "Fall Running")
        self.assertTimes(115000, 140000, 180000, 200000)
        self.assertEqual(len(objects), 326)

    def test_greenhouse(self):
        level, objects = self.getLevel("in/level-not-included/v3/tree.bytes")
        self.assertEqual(level.level_name, "[STE] Greenhouse")
        self.assertTimes(0, 0, 0, 0)
        self.assertEqual(len(objects), 359)


class Version4Test(BaseTest):

    def test_dac18(self):
        level, objects = self.getLevel("in/level-not-included/v4/dac18.bytes")
        self.assertEqual(level.level_name, "DAC #17: Hexahorrific")
        self.assertTimes(42000, 45000, 50000, 60000)
        self.assertEqual(len(objects), 299)

    def test_slip(self):
        level, objects = self.getLevel("in/level-not-included/v4/slipped second edit.bytes")
        self.assertEqual(level.level_name, "DAC #19: Slip")
        self.assertTimes(105000, 130000, 170000, 210000)
        self.assertEqual(len(objects), 593)


class Version5Test(BaseTest):

    def test_brutal_minimalism(self):
        level, objects = self.getLevel("in/level-not-included/v5/cursed_mountain.bytes")
        self.assertEqual(level.level_name, "Cursed Mountain")
        self.assertTimes(100000, 120000, 150000, 210000)
        self.assertEqual(len(objects), 488)

    def test_le_teleputo(self):
        level, objects = self.getLevel("in/level-not-included/v5/le teleputo.bytes")
        self.assertEqual(level.level_name, "Le Teleputo")
        self.assertTimes(140000, 210000, 280000, 340000)
        self.assertEqual(len(objects), 1486)


class Version7Test(BaseTest):

    def test_thegrid(self):
        level, objects = self.getLevel("in/level-not-included/v7/thegrid.bytes")
        self.assertEqual(level.level_name, "The Grid")
        self.assertTimes(200000, 220000, 240000, 270000)
        self.assertEqual(len(objects), 313)

    def test_neon_fury(self):
        level, objects = self.getLevel("in/level-not-included/v7/neon fury.bytes")
        self.assertEqual(level.level_name, "Neon Fury")
        self.assertTimes(63000, 80000, 150000, 180000)
        self.assertEqual(len(objects), 293)

    def test_salvation(self):
        level, objects = self.getLevel("in/level-not-included/v7/salvation.bytes")
        self.assertEqual(level.level_name, "Salvation")
        self.assertTimes(120000, 180000, 300000, 488700)
        self.assertEqual(len(objects), 565)


class Version8Test(BaseTest):

    def test_quicksilver(self):
        level, objects = self.getLevel("in/level-not-included/v8/quicksilver.bytes")
        self.assertEqual(level.level_name, "Quicksilver")
        self.assertTimes(22000, 35000, 3321000, 3350000)
        self.assertEqual(len(objects), 310)

    def test_rampage(self):
        level, objects = self.getLevel("in/level-not-included/v8/rampage.bytes")
        self.assertEqual(level.level_name, "Rampage Flats")
        self.assertTimes(85110, 140000, 179000, 180000)
        self.assertEqual(len(objects), 444)


class Version9Test(BaseTest):

    def test_sector_6624(self):
        level, objects = self.getLevel("in/level-not-included/v9/sector 6624.bytes")
        self.assertEqual(level.level_name, "Sector 6624")
        self.assertTimes(180000, 249000, 324000, 498000)
        self.assertScores(10400, 6900, 5200, 4200)
        self.assertEqual(len(objects), 627)

    def test_sector_flower(self):
        level, objects = self.getLevel("in/level-not-included/v9/flower.bytes")
        self.assertEqual(level.level_name, "Flower")
        self.assertTimes(-1, -1, -1, -1)
        self.assertScores(-1, -1, -1, -1)
        self.assertEqual(len(objects), 102)


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
