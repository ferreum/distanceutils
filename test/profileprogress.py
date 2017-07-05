#!/usr/bin/python
# File:        profileprogress.py
# Description: profileprogress
# Created:     2017-07-05


import unittest
import sys
import math

if '../' not in sys.path:
    sys.path.append('../')

from distance.profileprogress import ProfileProgress
from distance.bytes import DstBytes
from distance.constants import Completion, Mode


class ProfileProgressTest(unittest.TestCase):

    def test_parse_new(self):
        with open("in/profileprogress/new profile.bytes", 'rb') as f:
            obj = ProfileProgress(DstBytes(f))
            list(obj.iter_levels())

    def test_parse_single_map_started(self):
        with open("in/profileprogress/started acclivity.bytes", 'rb') as f:
            obj = ProfileProgress(DstBytes(f))
            levels = list(obj.iter_levels())
            self.assertEqual(len(levels), 1)
            self.assertEqual(levels[0][0].completion[Mode.SPRINT], Completion.STARTED)

    def test_parse_single_map_diamond(self):
        with open("in/profileprogress/diamond acclivity.bytes", 'rb') as f:
            obj = ProfileProgress(DstBytes(f))
            levels = list(obj.iter_levels())
            self.assertEqual(len(levels), 1)
            self.assertEqual(levels[0][0].completion[Mode.SPRINT], Completion.DIAMOND)


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
