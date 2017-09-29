from distance.level import Level


class Base(object):

    from tests import common

    class WriteReadTest(common.WriteReadTest):

        read_obj = Level


class StraightroadTest(Base.WriteReadTest):

    filename = "tests/in/level/test-straightroad.bytes"

    def verify_obj(self, level):
        self.assertEqual("Test-straightroad", level.level_name)
        self.assertEqual(6, len([o for l in level.layers for o in l.objects]))


class TheVirusBeginsS8Test(Base.WriteReadTest):

    filename = "tests/in/level-not-included/v1/the virus begins.bytes"

    def verify_obj(self, level):
        self.assertEqual("The Virus Begins", level.level_name)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
