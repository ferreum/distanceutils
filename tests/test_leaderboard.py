import unittest

from distance.leaderboard import Leaderboard
from distance.printing import PrintContext


class Version0Test(unittest.TestCase):

    def test_version0(self):
        lb = Leaderboard("tests/in/leaderboard/version_0.bytes")
        entries = lb.entries
        self.assertEqual([e.time for e in entries],
                            [162468, 152668, 135258, 581374, 127799, 182704, 517334])
        self.assertEqual([e.playername for e in entries],
                            ['\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7fFerreus'] * 6
                            + ['Ferreus'])
        self.assertEqual(lb.version, 0)
        for entry in entries:
            if entry.exception:
                raise entry.exception

    def test_print_data(self):
        p = PrintContext.for_test()
        p.print_data_of(Leaderboard("tests/in/leaderboard/version_0.bytes"))


class Version1Test(unittest.TestCase):

    def test_version1(self):
        lb = Leaderboard("tests/in/leaderboard/version_1.bytes")
        entries = lb.entries
        self.assertEqual([e.time for e in entries],
                            [57400, 57570, 58110, 58470, 58820, 58840, 59180,
                            59720, 62060, 73060, 86260, 2017828, 213099,
                            154735, 128125, 127943, 110319, 105157, 104042, 99116])
        self.assertEqual([e.playername for e in entries],
                            ['Ferreus'] * 13 + ['\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7fFerreus'] + ['Ferreus'] * 3
                            + ['\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7fFerreus'] + ['Ferreus'] * 2)
        self.assertEqual(lb.version, 1)
        self.assertTrue(entries[-1].sane_end_pos)

    def test_truncated(self):
        lb = Leaderboard.maybe("tests/in/leaderboard/version_1_truncated.bytes")
        entries = lb.entries
        self.assertEqual([e.time for e in entries],
                            [57400, 57570, 58110, 58470, 58820, None])
        self.assertEqual([e.playername for e in entries], ['Ferreus'] * 5 + [None])
        self.assertEqual(lb.version, 1)
        self.assertEqual(EOFError, type(entries[-1].exception))
        self.assertFalse(entries[-1].sane_end_pos)

    def test_truncated2(self):
        lb = Leaderboard.maybe("tests/in/leaderboard/version_1_truncated_2.bytes")
        entries = lb.entries
        self.assertEqual([e.time for e in entries],
                            [57400, 57570, 58110, 58470, None])
        self.assertEqual([e.playername for e in entries], ['Ferreus'] * 5)
        self.assertEqual(lb.version, 1)
        self.assertFalse(entries[-1].sane_end_pos)

    def test_print_data(self):
        p = PrintContext.for_test()
        p.print_data_of(Leaderboard("tests/in/leaderboard/version_1.bytes"))


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
