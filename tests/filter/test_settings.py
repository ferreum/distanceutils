from argparse import Namespace
import unittest

from distance import Level
from distance.filter import SettingsFilter
from distance.constants import Mode


orig_modes = {
    Mode.SPRINT: 1, Mode.STUNT: 0, Mode.SOCCER: 0,
    Mode.SPEED_AND_STYLE: 1, Mode.CHALLENGE: 1, Mode.TAG: 0,
}


def mkargs(name=None, namefmt='{name}', modes=None, modes_add=(),
           modes_remove=(), abilities=None):
    return Namespace(**locals())


def do_apply(**kw):
    l = Level("tests/in/level/test-straightroad.bytes")
    f = SettingsFilter(mkargs(**kw))
    f.apply(l)
    return l


class SettingsTest(unittest.TestCase):

    def test_name(self):
        l = do_apply(name="Changed Name")

        self.assertEqual("Changed Name", l.settings.name)

    def test_namefmt(self):
        l = do_apply(namefmt="Fmt {} {name} {version}")

        self.assertEqual("Fmt Test-straightroad Test-straightroad 3", l.settings.name)

    def test_modes(self):
        l = do_apply(modes={Mode.SPRINT: 1})

        self.assertEqual({Mode.SPRINT: 1}, dict(l.settings.modes))

    def test_modes_add(self):
        l = do_apply(modes_add={Mode.SOCCER: 1})

        exp = dict(orig_modes)
        exp[Mode.SOCCER] = 1
        self.assertEqual(exp, dict(l.settings.modes))

    def test_modes_remove(self):
        l = do_apply(modes_remove={Mode.SPRINT: 1})

        exp = dict(orig_modes)
        exp[Mode.SPRINT] = 0
        self.assertEqual(exp, dict(l.settings.modes))

    def test_abilities(self):
        l = do_apply(abilities=(0, 0, 1, 1, 1))

        self.assertEqual((0, 0, 1, 1, 1), l.settings.abilities)

    def test_empty(self):
        l = do_apply()

        self.assertEqual("Test-straightroad", l.name)
        self.assertEqual("Test-straightroad", l.settings.name)
        self.assertEqual((1, 0, 0, 0, 0), l.settings.abilities)
        self.assertEqual(3, l.settings.version)
        self.assertEqual(orig_modes, dict(l.settings.modes))


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
