import unittest
import math

from distance.level import Level, need_counters
from distance.printing import PrintContext
from tests.common import check_exceptions


def objects_with_groups(gen):
    for obj in gen:
        yield obj
        if getattr(obj, 'is_object_group', False):
            yield from objects_with_groups(obj.children)


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

    def getLevel(self, filename, with_layers=False, with_groups=False,
                 with_subobjects=False):
        f = self.open(filename)
        self.level = level = Level(f)
        gen = level.iter_objects(with_layers=with_layers)
        if with_groups:
            gen = objects_with_groups(gen)
        self.objects = objects = [level.settings] + list(gen)
        def get_subobjects(objs, is_sub):
            for obj in objs:
                if is_sub:
                    yield obj
                if not getattr(obj, 'is_object_group', True):
                    yield from get_subobjects(obj.children, True)
        check_exceptions(level)
        self.subobjects = list(get_subobjects(objects, False))
        return level, objects

    def assertTimes(self, *times):
        def normalize(value):
            if math.isnan(value):
                return "NaN"
            return int(value)
        self.assertEqual(tuple(map(normalize, self.objects[0].medal_times)), times)

    def assertScores(self, *scores):
        self.assertEqual(tuple(self.objects[0].medal_scores), scores)


class Base(object):

    class PrintTest(BaseTest):

        def test_print(self):
            for file in self.files:
                with self.subTest(file=file):
                    p = PrintContext.for_test()
                    try:
                        p.print_data_of(Level(f"tests/in/level-not-included/{file}.bytes"))
                    except FileNotFoundError:
                        self.skipTest(f"file {file!r} is missing")


class Version0Test(BaseTest):

    def test_brutal_minimalism(self):
        level, objects = self.getLevel("tests/in/level-not-included/v0/brutal minimalism.bytes")
        self.assertEqual(level.level_name, "Brutal Minimalism")
        self.assertTimes(19149, 31916, 47874, 63832)
        self.assertScores(664, 591, 419, 199)
        self.assertEqual(len(objects), 33)

    def test_the_stretch(self):
        level, objects = self.getLevel("tests/in/level-not-included/v0/the stretch.bytes")
        self.assertEqual(level.level_name, "The Stretch")
        self.assertTimes(105244, 175407, 263111, 350815)
        self.assertScores(3654, 3248, 2307, 1096)
        self.assertEqual(len(objects), 148)


class Version1Test(BaseTest):

    MANY_LEVELS = ("car crusher", "city", "contraband delivery",
                   "entanglement", "qwe", "returnofandy",
                   "the virus begins", "damnation")

    def test_building_hop(self):
        level, objects = self.getLevel("tests/in/level-not-included/v1/building hop.bytes")
        self.assertEqual(level.level_name, "Building hop")
        self.assertTimes(30302, 50504, 75756, 101009)
        self.assertEqual(len(objects), 69)
        self.assertEqual(len(self.subobjects), 174)

    def test_city_of_gold(self):
        level, objects = self.getLevel("tests/in/level-not-included/v1/roller coaster ride.bytes")
        self.assertEqual(level.level_name, "A City Of Gold")
        self.assertTimes(73501, 122502, 183753, 245005)
        self.assertEqual(len(objects), 128)
        self.assertEqual(len(self.subobjects), 445)

    def test_dark_generator(self):
        level, objects = self.getLevel("tests/in/level-not-included/v1/dark generator.bytes", with_layers=True)
        self.assertEqual(level.level_name, "Dark Generator")
        self.assertTimes(-1, -1, -1, -1)
        self.assertEqual(len(objects), 79)
        self.assertEqual(len(self.subobjects), 108)

    def test_damnation(self):
        level, objects = self.getLevel("tests/in/level-not-included/v1/damnation.bytes",
                                       with_layers=True, with_groups=True)
        self.assertEqual(level.level_name, "Damnation")
        self.assertTimes(89421, 149035, 223552, 298070)
        self.assertEqual(len(objects), 608)
        self.assertEqual(len(self.subobjects), 1145)


class Version1PrintTest(Base.PrintTest):

    files = ["v1/" + n for n in Version1Test.MANY_LEVELS[:3]]


class Version3Test(BaseTest):

    def test_fall_running(self):
        level, objects = self.getLevel("tests/in/level-not-included/v3/fall running.bytes")
        self.assertEqual(level.level_name, "Fall Running")
        self.assertTimes(115000, 140000, 180000, 200000)
        self.assertEqual(len(objects), 326)
        self.assertEqual(len(self.subobjects), 516)

    def test_hexagon_18(self):
        level, objects = self.getLevel("tests/in/level-not-included/v3/hexagon 18.bytes", with_groups=True)
        self.assertEqual(level.level_name, "Hexagon 18")
        self.assertTimes(0, 0, 0, 0)
        self.assertEqual(len(objects), 645)
        self.assertEqual(len(self.subobjects), 1277)

    def test_print_groups(self):
        p = PrintContext.for_test(flags=('groups',))
        f = self.open("tests/in/level-not-included/v3/hexagon 18.bytes")
        with need_counters(p) as counters:
            level = Level(f)
            p.print_data_of(level)
            self.assertEqual(counters.num_objects, 644)


class Version4Test(BaseTest):

    def test_dac18(self):
        level, objects = self.getLevel("tests/in/level-not-included/v4/dac18.bytes")
        self.assertEqual(level.level_name, "DAC #17: Hexahorrific")
        self.assertTimes(42000, 45000, 50000, 60000)
        self.assertEqual(len(objects), 299)
        self.assertEqual(len(self.subobjects), 30)

    def test_slip(self):
        level, objects = self.getLevel("tests/in/level-not-included/v4/slipped second edit.bytes")
        self.assertEqual(level.level_name, "DAC #19: Slip")
        self.assertTimes(105000, 130000, 170000, 210000)
        self.assertEqual(len(objects), 593)
        self.assertEqual(len(self.subobjects), 779)


class Version5Test(BaseTest):

    def test_cursed_mountain(self):
        level, objects = self.getLevel("tests/in/level-not-included/v5/cursed_mountain.bytes")
        self.assertEqual(level.level_name, "Cursed Mountain")
        self.assertTimes(100000, 120000, 150000, 210000)
        self.assertEqual(len(objects), 488)
        self.assertEqual(len(self.subobjects), 269)

    def test_darkness(self):
        level, objects = self.getLevel("tests/in/level-not-included/v5/darkness.bytes", with_groups=True)
        self.assertEqual(level.level_name, "Darkness")
        self.assertTimes(60000, 100000, 130000, 160000)
        self.assertEqual(len(objects), 124)
        self.assertEqual(len(self.subobjects), 190)


class Version7Test(BaseTest):

    def test_thegrid(self):
        level, objects = self.getLevel("tests/in/level-not-included/v7/thegrid.bytes")
        self.assertEqual(level.level_name, "The Grid")
        self.assertTimes(200000, 220000, 240000, 270000)
        self.assertEqual(len(objects), 313)
        self.assertEqual(len(self.subobjects), 616)

    def test_neon_fury(self):
        level, objects = self.getLevel("tests/in/level-not-included/v7/neon fury.bytes")
        self.assertEqual(level.level_name, "Neon Fury")
        self.assertTimes(63000, 80000, 150000, 180000)
        self.assertEqual(len(objects), 293)
        self.assertEqual(len(self.subobjects), 441)

    def test_salvation(self):
        level, objects = self.getLevel("tests/in/level-not-included/v7/salvation.bytes")
        self.assertEqual(level.level_name, "Salvation")
        self.assertTimes(120000, 180000, 300000, 488700)
        self.assertEqual(len(objects), 565)
        self.assertEqual(len(self.subobjects), 571)

    def test_brief_chaos(self):
        level, objects = self.getLevel("tests/in/level-not-included/v7/brief chaos.bytes")
        self.assertEqual(level.level_name, "Brief Chaos")
        self.assertTimes(0, 0, 0, 0)
        self.assertEqual(len(objects), 112)
        self.assertEqual(len(self.subobjects), 620)


class Version8Test(BaseTest):

    def test_quicksilver(self):
        level, objects = self.getLevel("tests/in/level-not-included/v8/quicksilver.bytes")
        self.assertEqual(level.level_name, "Quicksilver")
        self.assertTimes(22000, 35000, 3321000, 3350000)
        self.assertEqual(len(objects), 310)
        self.assertEqual(len(self.subobjects), 286)

    def test_rampage(self):
        level, objects = self.getLevel("tests/in/level-not-included/v8/rampage.bytes")
        self.assertEqual(level.level_name, "Rampage Flats")
        self.assertTimes(85110, 140000, 179000, 180000)
        self.assertEqual(len(objects), 444)
        self.assertEqual(len(self.subobjects), 1005)


class Version9Test(BaseTest):

    def test_sector_6624(self):
        level, objects = self.getLevel("tests/in/level-not-included/v9/sector 6624.bytes")
        self.assertEqual(level.level_name, "Sector 6624")
        self.assertTimes(180000, 249000, 324000, 498000)
        self.assertScores(10400, 6900, 5200, 4200)
        self.assertEqual(len(objects), 627)
        self.assertEqual(len(self.subobjects), 794)

    def test_flower(self):
        level, objects = self.getLevel("tests/in/level-not-included/v9/flower.bytes")
        self.assertEqual(level.level_name, "Flower")
        self.assertTimes(-1, -1, -1, -1)
        self.assertScores(-1, -1, -1, -1)
        self.assertEqual(len(objects), 102)
        self.assertEqual(len(self.subobjects), 213)


class Version9PrintTest(Base.PrintTest):

    files = ("v9/sector 6624", "v9/flower")


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
