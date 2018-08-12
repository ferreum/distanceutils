import unittest
import math

from distance import Level
from distance.printing import PrintContext, need_counters
from tests.common import check_exceptions, iter_level_objects


class LevelData(object):

    def __init__(self, file, with_groups=False, with_subobjects=False):
        self.level = level = Level(file)
        self.settings = level.settings
        self.name = level.settings.name
        check_exceptions(level)
        gen = iter_level_objects(level, with_groups=with_groups)
        self.objects = objects = list(gen)
        def get_subobjects(objs, is_sub):
            for obj in objs:
                if is_sub:
                    yield obj
                if not getattr(obj, 'is_object_group', True):
                    yield from get_subobjects(obj.children, True)
        self.subobjects = list(get_subobjects(objects, False))


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.opened_files = []

    def tearDown(self):
        self.close_files()

    def open(self, filename):
        try:
            f = open(filename, 'rb')
        except FileNotFoundError:
            self.skipTest(f"Test file {filename} does not exist")
        else:
            self.opened_files.append(f)
            return f

    def close_files(self):
        for f in self.opened_files:
            f.close()
        self.opened_files = []

    def getLevel(self, filename, with_groups=False,
                 with_subobjects=False):
        file = self.open(filename)
        return LevelData(file, with_groups=with_groups,
                         with_subobjects=with_subobjects)

    def assertTimes(self, data, *times):
        def normalize(value):
            if math.isnan(value):
                return "NaN"
            return int(value)
        self.assertEqual(tuple(map(normalize, data.settings.medal_times)), times)

    def assertScores(self, data, *scores):
        self.assertEqual(tuple(data.settings.medal_scores), scores)


class Base(object):

    class PrintTest(BaseTest):

        def test_print(self):
            skipped = []
            for file in self.files:
                with self.subTest(file=file):
                    p = PrintContext.for_test()
                    try:
                        p.print_data_of(Level(f"tests/in/level-not-included/{file}.bytes"))
                    except FileNotFoundError:
                        skipped.append(file)
            if skipped:
                self.skipTest(f"missing files: {skipped}")


class Section8Test(BaseTest):

    def test_the_virus_begins(self):
        data = self.getLevel("tests/in/level-not-included/s8/the virus begins.bytes")
        self.assertEqual(data.name, "The Virus Begins")
        self.assertEqual(len(data.objects), 402)
        self.assertEqual(len(data.subobjects), 582)

    def test_returnofandy(self):
        data = self.getLevel("tests/in/level-not-included/s8/returnofandy.bytes")
        self.assertEqual(data.settings.name, "ReturnOfAndy")
        self.assertEqual(len(data.objects), 835)
        self.assertEqual(len(data.subobjects), 987)


class Version0Test(BaseTest):

    def test_brutal_minimalism(self):
        data = self.getLevel("tests/in/level-not-included/v0/brutal minimalism.bytes")
        self.assertEqual(data.name, "Brutal Minimalism")
        self.assertTimes(data, 19149, 31916, 47874, 63832)
        self.assertScores(data, 664, 591, 419, 199)
        self.assertEqual(len(data.objects), 32)

    def test_the_stretch(self):
        data = self.getLevel("tests/in/level-not-included/v0/the stretch.bytes")
        self.assertEqual(data.name, "The Stretch")
        self.assertTimes(data, 105244, 175407, 263111, 350815)
        self.assertScores(data, 3654, 3248, 2307, 1096)
        self.assertEqual(len(data.objects), 147)


class Version1Test(BaseTest):

    def test_building_hop(self):
        data = self.getLevel("tests/in/level-not-included/v1/building hop.bytes")
        self.assertEqual(data.name, "Building hop")
        self.assertTimes(data, 30302, 50504, 75756, 101009)
        self.assertEqual(len(data.objects), 68)
        self.assertEqual(len(data.subobjects), 174)

    def test_city_of_gold(self):
        data = self.getLevel("tests/in/level-not-included/v1/roller coaster ride.bytes")
        self.assertEqual(data.name, "A City Of Gold")
        self.assertTimes(data, 73501, 122502, 183753, 245005)
        self.assertEqual(len(data.objects), 127)
        self.assertEqual(len(data.subobjects), 445)

    def test_dark_generator(self):
        data = self.getLevel("tests/in/level-not-included/v1/dark generator.bytes")
        self.assertEqual(data.name, "Dark Generator")
        self.assertTimes(data, -1, -1, -1, -1)
        self.assertEqual(len(data.objects), 76)
        self.assertEqual(len(data.subobjects), 108)

    def test_damnation(self):
        data = self.getLevel("tests/in/level-not-included/v1/damnation.bytes",
                             with_groups=True)
        self.assertEqual(data.name, "Damnation")
        self.assertTimes(data, 89421, 149035, 223552, 298070)
        self.assertEqual(len(data.objects), 606)
        self.assertEqual(len(data.subobjects), 1145)


class Version1PrintTest(Base.PrintTest):

    files = ["v1/" + n for n in ["car crusher", "city", "contraband delivery"]]


class Version3Test(BaseTest):

    def test_fall_running(self):
        data = self.getLevel("tests/in/level-not-included/v3/fall running.bytes")
        self.assertEqual(data.name, "Fall Running")
        self.assertTimes(data, 115000, 140000, 180000, 200000)
        self.assertEqual(len(data.objects), 325)
        self.assertEqual(len(data.subobjects), 516)

    def test_hexagon_18(self):
        data = self.getLevel("tests/in/level-not-included/v3/hexagon 18.bytes",
                             with_groups=True)
        self.assertEqual(data.name, "Hexagon 18")
        self.assertTimes(data, 0, 0, 0, 0)
        self.assertEqual(len(data.objects), 644)
        self.assertEqual(len(data.subobjects), 1277)

    def test_print_groups(self):
        p = PrintContext.for_test(flags=('groups',))
        f = self.open("tests/in/level-not-included/v3/hexagon 18.bytes")
        with need_counters(p) as counters:
            level = Level(f)
            p.print_data_of(level)
            self.assertEqual(counters.num_objects, 644)


class Version4Test(BaseTest):

    def test_dac18(self):
        data = self.getLevel("tests/in/level-not-included/v4/dac18.bytes")
        self.assertEqual(data.name, "DAC #17: Hexahorrific")
        self.assertTimes(data, 42000, 45000, 50000, 60000)
        self.assertEqual(len(data.objects), 298)
        self.assertEqual(len(data.subobjects), 30)

    def test_slip(self):
        data = self.getLevel("tests/in/level-not-included/v4/slipped second edit.bytes")
        self.assertEqual(data.name, "DAC #19: Slip")
        self.assertTimes(data, 105000, 130000, 170000, 210000)
        self.assertEqual(len(data.objects), 592)
        self.assertEqual(len(data.subobjects), 779)


class Version5Test(BaseTest):

    def test_cursed_mountain(self):
        data = self.getLevel("tests/in/level-not-included/v5/cursed_mountain.bytes")
        self.assertEqual(data.name, "Cursed Mountain")
        self.assertTimes(data, 100000, 120000, 150000, 210000)
        self.assertEqual(len(data.objects), 487)
        self.assertEqual(len(data.subobjects), 269)

    def test_darkness(self):
        data = self.getLevel("tests/in/level-not-included/v5/darkness.bytes",
                             with_groups=True)
        self.assertEqual(data.name, "Darkness")
        self.assertTimes(data, 60000, 100000, 130000, 160000)
        self.assertEqual(len(data.objects), 123)
        self.assertEqual(len(data.subobjects), 190)


class Version7Test(BaseTest):

    def test_thegrid(self):
        data = self.getLevel("tests/in/level-not-included/v7/thegrid.bytes")
        self.assertEqual(data.name, "The Grid")
        self.assertTimes(data, 200000, 220000, 240000, 270000)
        self.assertEqual(len(data.objects), 312)
        self.assertEqual(len(data.subobjects), 616)

    def test_neon_fury(self):
        data = self.getLevel("tests/in/level-not-included/v7/neon fury.bytes")
        self.assertEqual(data.name, "Neon Fury")
        self.assertTimes(data, 63000, 80000, 150000, 180000)
        self.assertEqual(len(data.objects), 292)
        self.assertEqual(len(data.subobjects), 441)

    def test_salvation(self):
        data = self.getLevel("tests/in/level-not-included/v7/salvation.bytes")
        self.assertEqual(data.name, "Salvation")
        self.assertTimes(data, 120000, 180000, 300000, 488700)
        self.assertEqual(len(data.objects), 564)
        self.assertEqual(len(data.subobjects), 571)

    def test_brief_chaos(self):
        data = self.getLevel("tests/in/level-not-included/v7/brief chaos.bytes")
        self.assertEqual(data.name, "Brief Chaos")
        self.assertTimes(data, 0, 0, 0, 0)
        self.assertEqual(len(data.objects), 111)
        self.assertEqual(len(data.subobjects), 620)


class Version8Test(BaseTest):

    def test_quicksilver(self):
        data = self.getLevel("tests/in/level-not-included/v8/quicksilver.bytes")
        self.assertEqual(data.name, "Quicksilver")
        self.assertTimes(data, 22000, 35000, 3321000, 3350000)
        self.assertEqual(len(data.objects), 309)
        self.assertEqual(len(data.subobjects), 286)

    def test_rampage(self):
        data = self.getLevel("tests/in/level-not-included/v8/rampage.bytes")
        self.assertEqual(data.name, "Rampage Flats")
        self.assertTimes(data, 85110, 140000, 179000, 180000)
        self.assertEqual(len(data.objects), 443)
        self.assertEqual(len(data.subobjects), 1005)


class Version9Test(BaseTest):

    def test_sector_6624(self):
        data = self.getLevel("tests/in/level-not-included/v9/sector 6624.bytes")
        self.assertEqual(data.name, "Sector 6624")
        self.assertTimes(data, 180000, 249000, 324000, 498000)
        self.assertScores(data, 10400, 6900, 5200, 4200)
        self.assertEqual(len(data.objects), 626)
        self.assertEqual(len(data.subobjects), 794)

    def test_flower(self):
        data = self.getLevel("tests/in/level-not-included/v9/flower.bytes")
        self.assertEqual(data.name, "Flower")
        self.assertTimes(data, -1, -1, -1, -1)
        self.assertScores(data, -1, -1, -1, -1)
        self.assertEqual(len(data.objects), 101)
        self.assertEqual(len(data.subobjects), 213)


class Version9PrintTest(Base.PrintTest):

    files = ("v9/sector 6624", "v9/flower")


# vim:set sw=4 ts=8 sts=4 et:
