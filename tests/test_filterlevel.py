import unittest

from distance_scripts.filterlevel import make_arglist


class SplitArgsTest(unittest.TestCase):

    def test_empty(self):
        self.assertEqual([], make_arglist(""))

    def test_single(self):
        self.assertEqual([":all"], make_arglist("all"))

    def test_value(self):
        self.assertEqual([":num=2"], make_arglist("num=2"))

    def test_multiple(self):
        self.assertEqual([":all", ":num=2"], make_arglist("all:num=2"))

    def test_escape(self):
        self.assertEqual([":type=te:st"], make_arglist("type=te\\:st"))


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
