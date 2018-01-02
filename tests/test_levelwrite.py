from distance.level import Level


class Base(object):

    from tests import common

    class WriteReadTest(common.WriteReadTest):

        read_obj = Level


class StraightroadTest(Base.WriteReadTest):

    filename = "tests/in/level/test-straightroad.bytes"

    def verify_obj(self, level):
        self.assertEqual("Test-straightroad", level.name)
        self.assertEqual(6, len([o for l in level.layers for o in l.objects]))


class StraightroadV25Test(Base.WriteReadTest):

    filename = "tests/in/level/test straightroad v25.bytes"

    def verify_obj(self, level):
        self.assertEqual("Test-straightroad v25", level.name)
        self.assertEqual(2, len(level.layers))
        self.assertEqual(5, len(level.layers[0].objects))
        self.assertEqual(1, len(level.layers[1].objects))


class StraightroadV26AuthorTest(Base.WriteReadTest):

    filename = "tests/in/level/test straightroad v26 author.bytes"

    def verify_obj(self, level):
        self.assertEqual("Test-straightroad v26", level.name)
        self.assertEqual("Ferreus", level.settings.author_name)


class V25LevelDescriptionTest(Base.WriteReadTest):

    filename = "tests/in/level/level with description.bytes"

    def verify_obj(self, level):
        self.assertEqual("level with description", level.name)
        self.assertEqual("level with description", level.settings.name)
        self.assertEqual("test level description", level.settings.description)


class ChangeLevelnameTest(Base.WriteReadTest):

    filename = "tests/in/level/test-straightroad.bytes"

    cmp_bytes = False

    def modify_obj(self, obj):
        obj.name = "Changed Container Name"
        obj.settings.name = "Changed Settings Name"
        return obj

    def verify_obj(self, level):
        self.assertEqual(level.name, "Changed Container Name")
        self.assertEqual(level.settings.name, "Changed Settings Name")


class TheVirusBeginsS8Test(Base.WriteReadTest):

    filename = "tests/in/level-not-included/v1/the virus begins.bytes"
    skip_if_missing = True

    def verify_obj(self, level):
        self.assertEqual("The Virus Begins", level.name)


class BirthdayBashCourtS8Test(Base.WriteReadTest):

    filename = "tests/in/level-not-included/s8/birthday bash court.bytes"
    skip_if_missing = True

    def verify_obj(self, level):
        self.assertEqual("birthday bash court", level.name)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
