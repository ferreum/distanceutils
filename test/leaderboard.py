#!/usr/bin/python
# File:        leaderboard.py
# Description: leaderboard test
# Created:     2017-06-27


import unittest
import sys

sys.path.append('../')

from distance.leaderboard import Leaderboard
from distance.bytes import DstBytes


class Version0Test(unittest.TestCase):

    def test_version0(self):
        with open("in/leaderboard/version_0.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            lb = Leaderboard(dbytes)
            entries = lb.read_entries()
            self.assertEqual([e.time for e in entries],
                             [162468, 152668, 135258, 581374, 127799, 182704, 517334])
            self.assertEqual([e.playername for e in entries],
                             ['\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7fFerreus'] * 6
                             + ['Ferreus'])
            self.assertEqual(lb.version, 0)


class Version1Test(unittest.TestCase):

    def test_version1(self):
        with open("in/leaderboard/version_1.bytes", 'rb') as f:
            dbytes = DstBytes(f)
            lb = Leaderboard(dbytes)
            entries = lb.read_entries()
            self.assertEqual([e.time for e in entries],
                             [57400, 57570, 58110, 58470, 58820, 58840, 59180,
                              59720, 62060, 73060, 86260, 2017828, 213099,
                              154735, 128125, 127943, 110319, 105157, 104042, 99116])
            self.assertEqual([e.playername for e in entries],
                             ['Ferreus'] * 13 + ['\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7fFerreus'] + ['Ferreus'] * 3
                             + ['\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7fFerreus'] + ['Ferreus'] * 2)
            self.assertEqual(lb.version, 1)


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
