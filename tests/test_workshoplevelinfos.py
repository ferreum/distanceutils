import unittest

from distance.workshoplevelinfos import WorkshopLevelInfos
from distance.printing import PrintContext


class Version0Test(unittest.TestCase):

    LEVEL_IDS = [469806096, 822049253, 738529116, 753242700, 819617632, 837765551, 895852129, 920857185, 922165443, 923374136, 923919455, 925074578, 925807935, 927306728, 927891781, 864308595, 928965113, 928293077, 0, 727889718, 930822683, 931056317, 932950922, 932137893, 933651174, 934668868, 935484491, 936029646, 937387342, 942334134, 937961654, 938169628, 937865749, 939014598, 939810443, 939803443, 939807851, 939554130, 941191706]
    LEVEL_NAMES = ['Lost Fortress', 'Main Menu Datastream', 'Linear Green', 'Impurity', 'Canyon Realm (Hot Wheels Acceleracers)', 'The-fall_00', 'Futuristic Highway - Tech District', 'SimpleRace?', 'Stretch Your Wings', '2caKe', 'Jaded Sphere', 'Corrupted Flight', 'Space menu', 'Spirit', 'Laserrush', 'Micro realm (hotwheels acceleracers)', 'Crash Corse MainMenu', 'Sacrifical', '', 'Egypt (Full)', 'Test Lab', 'Test-1A', 'Fog Realm', 'SpeedRun', 'Speed-1', 'Departure', 'Broken Road', 'Death', 'Absurdly Impractical Level', 'storm realm 2.0 (unanimated)', 'The Arctic', 'A Long Way Down', 'Cybergrid Realm (Hot Wheels Acceleracers)', 'Zedron Landing', 'Konna Mondaze', 'Fear', 'Sand', 'Skyline Realm', 'Recovering']

    def test_version0(self):
        infos = WorkshopLevelInfos("tests/in/workshoplevelinfos/version_0.bytes")
        levels = infos.levels
        self.assertEqual([l.id for l in levels],
                            Version0Test.LEVEL_IDS)
        self.assertEqual([l.title for l in levels],
                            Version0Test.LEVEL_NAMES)
        self.assertEqual([l.author for l in levels],
                            ['Ferreus'] + ['Unknown'] * 38)
        self.assertEqual([l.authorid for l in levels][:3],
                            [76561198040630941] * 2 + [76561198089234092])
        self.assertEqual([l.published_by_user for l in levels],
                            [1] * 2 + [0] * 37)
        self.assertEqual([l.tags for l in levels][:3],
                            ['Level,Sprint,Advanced', 'Main Menu', 'Level,Sprint,Advanced'])
        self.assertEqual([l.published_date for l in levels][:3],
                            [1435349535, 1482243138, 1470466984])
        self.assertEqual([l.updated_date for l in levels][:3],
                            [1438108556, 1482711714, 1494893107])
        self.assertEqual([len(l.description) for l in levels][:9],
                            [158, 33, 215, 39, 255, 26, 60, 124, 353])
        self.assertEqual([l.description[:4] for l in levels][:2],
                            ['A hi', 'Very'])
        self.assertEqual([l.path for l in levels][:2],
                            ['WorkshopLevels/76561198040630941/lost fortress.bytes',
                            'WorkshopLevels/76561198040630941/main menu datastream.bytes'])
        self.assertEqual([l.upvotes for l in levels][:9],
                            [2273, 4, 92, 846, 758, 1, 39, 7, 5])
        self.assertEqual([l.downvotes for l in levels][:9],
                            [227, 0, 23, 36, 66, 0, 9, 3, 5])
        self.assertEqual([l.rating for l in levels][:9],
                            [1, 0, 0, 1, 2, 0, 0, 0, 1])
        self.assertEqual(39, len(levels))
        self.assertEqual([(o.sane_end_pos, o.exception) for o in levels], [(True, None)] * 39)

    def test_truncated(self):
        infos = WorkshopLevelInfos.maybe("tests/in/workshoplevelinfos/version_0_truncated.bytes")
        gen = iter(infos.levels)
        level = next(gen)
        self.assertEqual(level.id, 469806096)
        self.assertIsNone(level.exception)
        self.assertTrue(level.sane_end_pos)
        level = next(gen)
        self.assertEqual(level.id, 822049253)
        self.assertIsNone(level.author)
        self.assertIsNone(level.authorid)
        self.assertIsInstance(level.exception, EOFError)
        self.assertFalse(level.sane_end_pos)

    def test_truncated_2(self):
        infos = WorkshopLevelInfos.maybe("tests/in/workshoplevelinfos/version_0_truncated_2.bytes")
        gen = iter(infos.levels)
        level = next(gen)
        self.assertIsNone(level.exception)
        level = next(gen)
        self.assertIsInstance(level.exception, EOFError)
        self.assertFalse(level.sane_end_pos)

    def test_print(self):
        p = PrintContext.for_test()
        obj = WorkshopLevelInfos("tests/in/workshoplevelinfos/version_0.bytes")
        p.print_data_of(obj)


# vim:set sw=4 ts=8 sts=4 et:
