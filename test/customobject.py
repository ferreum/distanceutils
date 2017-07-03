#!/usr/bin/python
# File:        customobject.py
# Description: customobject
# Created:     2017-07-03


import unittest
import sys
import math

if '../' not in sys.path:
    sys.path.append('../')

from distance.level import PROBER
from distance.bytes import DstBytes


def results_with_groups(gen):
    for obj, sane, exc in gen:
        yield obj, sane, exc
        if obj.has_children:
            yield from results_with_groups(obj.iter_children())


class InfoDisplayBoxTest(unittest.TestCase):

    def test_parse(self):
        with open("in/customobject/infodisplaybox 1.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.texts, ["Text0", "Text1", "Text2", "", "Text4"])

    def test_parse_2(self):
        with open("in/customobject/infodisplaybox 2.bytes", 'rb') as f:
            obj = PROBER.parse(DstBytes(f))
            self.assertEqual(obj.texts, ["Test_2", "", "", "", ""])


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
