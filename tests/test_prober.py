import unittest
from contextlib import contextmanager

from distance.bytes import DstBytes, Magic, Section
from distance.prober import ClassCollector, BytesProber, RegisterError
from distance.base import Fragment, BaseObject, ObjectFragment
from distance.levelobjects import LevelObject
from distance import DefaultProbers
from distance._impl.fragments.levelfragments import GoldenSimplesFragment
from distance._impl.level_objects.objects import GoldenSimple
from .common import write_read


class TestObject(BaseObject):

    def __init__(self, **kw):
        self.init_args = kw


def TagFragment(name, tag, **kw):
    kw['class_tag'] = tag
    return type(name, (Fragment,), kw)


@contextmanager
def classes_on_module(*classes):
    globs = globals()
    for cls in classes:
        globs[cls.__name__] = cls
    try:
        yield
    finally:
        for cls in classes:
            del globs[cls.__name__]


class ProberTest(unittest.TestCase):

    def test_read_creates_plain_object(self):
        prober = BytesProber()
        prober.add_func(lambda *_: TestObject, 'fallback')
        obj = prober.read("tests/in/customobject/2cubes.bytes")
        self.assertEqual(True, obj.init_args['plain'])

    def test_maybe_catches_exception(self):
        prober = BytesProber()
        prober.add_func(lambda *_: TestObject, 'fallback')
        dbytes = DstBytes.in_memory()
        dbytes.write_int(4, Magic[6])
        dbytes.seek(0)
        obj = prober.maybe(dbytes)
        self.assertEqual(EOFError, type(obj.exception))

    def test_maybe_propagates_io_exception(self):
        prober = BytesProber()
        prober.add_func(lambda *_: TestObject, 'fallback')
        dbytes = DstBytes.in_memory()
        dbytes.write_int(4, Magic[6])
        dbytes.seek(0)
        def raise_error(*_):
            raise IOError
        dbytes.read_bytes = raise_error
        self.assertRaises(IOError, prober.maybe, dbytes)


class RegisteredTest(unittest.TestCase):

    def test_levelinfos(self):
        for ver in range(0, 1):
            with self.subTest(version=ver):
                result = DefaultProbers.file.read(f"tests/in/workshoplevelinfos/version_{ver}.bytes")
                self.assertEqual("WorkshopLevelInfos", type(result).__name__)

    def test_leaderboard(self):
        for ver in range(0, 2):
            with self.subTest(version=ver):
                result = DefaultProbers.file.read(f"tests/in/leaderboard/version_{ver}.bytes")
                self.assertEqual("Leaderboard", type(result).__name__)

    def test_replay(self):
        for ver in range(1, 5):
            with self.subTest(version=ver):
                result = DefaultProbers.file.read(f"tests/in/replay/version_{ver}.bytes")
                self.assertEqual("Replay", type(result).__name__)

    def test_level(self):
        for levelfile in ("test-straightroad",):
            with self.subTest(levelfile=levelfile):
                result = DefaultProbers.file.read(f"tests/in/level/{levelfile}.bytes")
                self.assertEqual("Level", type(result).__name__)


class UnknownObjectFileTest(unittest.TestCase):

    def setUp(self):
        self.db = db = DstBytes.in_memory()
        with db.write_section(Magic[6], '__distanceutils__test__object__'):
            pass
        db.seek(0)

    def test_unknown_object(self):
        obj = DefaultProbers.file.read(self.db)

        self.assertEqual(type(obj), BaseObject)

    def test_unknown_level_like(self):
        obj = DefaultProbers.level_like.read(self.db)

        self.assertEqual(type(obj), LevelObject)


class VerifyTest(unittest.TestCase):

    def test_verify(self):
        DefaultProbers._verify_autoload(verify_autoload=False)

    def test_verify_autoload(self):
        import distance
        if not distance.prober.do_autoload:
            self.skipTest("Autoload is disabled")
        actual, loaded = DefaultProbers._verify_autoload(verify_autoload=True)
        self.assertEqual(loaded, actual)


class VerifyClassInfo(unittest.TestCase):

    def test_create_fragment(self):
        frag = DefaultProbers.fragments.create('Object')
        self.assertEqual(type(frag), ObjectFragment)

    def test_create_fragment_autoloaded(self):
        frag = DefaultProbers.fragments.create('GoldenSimples')
        self.assertEqual(type(frag), GoldenSimplesFragment)

    def test_fragment_attrs(self):
        obj = GoldenSimple(type='CubeGS')
        self.assertEqual(obj.emit_index, 17)

    def test_registration_version_merge(self):
        prober1 = ClassCollector()
        prober2 = ClassCollector()
        base = Section.base(Magic[2], 23)
        frag1 = prober1.fragment(TagFragment('Frag1', 'Test', base_container=base, container_versions=1))
        frag5 = prober2.fragment(TagFragment('Frag5', 'Test', base_container=base, container_versions=5))
        frag23 = prober2.fragment(TagFragment('Frag23', 'Test', base_container=base, container_versions=(2, 3)))
        glob = globals()
        glob['Frag1'] = frag1
        glob['Frag23'] = frag23
        glob['Frag5'] = frag5

        with classes_on_module(frag1, frag23, frag5):
            prober = BytesProber()
            prober._load_impl(prober1, True)
            prober._load_impl(prober2, True)

            def sec(ver):
                return Section(base=base, version=ver).to_key()
            def get_klass(*args, **kw):
                fact = prober.factory(*args, **kw)
                return fact.cls, fact.container.to_key()
            self.assertEqual(prober.base_container_key('Test'), base.to_key())
            self.assertEqual((frag1, sec(1)), get_klass('Test', version=1))
            self.assertEqual((frag23, sec(2)), get_klass('Test', version=2))
            self.assertEqual((frag23, sec(3)), get_klass('Test', version=3))
            self.assertEqual((frag5, sec(5)), get_klass('Test', version=5))

    def test_reg_version_conflict(self):
        prober1 = ClassCollector()
        prober2 = ClassCollector()
        base = Section.base(Magic[2], 23)
        prober1.fragment(TagFragment('Frag1', 'Test', base_container=base, container_versions=1))
        prober2.fragment(TagFragment('Frag2', 'Test', base_container=base, container_versions=(1, 2)))

        prober = BytesProber()
        prober._load_impl(prober1, True)
        with self.assertRaises(RegisterError) as cm:
            prober._load_impl(prober2, True)
        self.assertRegex(str(cm.exception), r'already registered for .*Frag1')

    def test_reg_base_container_conflict(self):
        prober1 = ClassCollector()
        prober2 = ClassCollector()
        prober1.fragment(TagFragment('Frag1', 'Test', base_container=Section.base(Magic[2], 23), container_versions=1))
        prober2.fragment(TagFragment('Frag2', 'Test', base_container=Section.base(Magic[2], 34), container_versions=2))

        prober = BytesProber()
        prober._load_impl(prober1, True)
        with self.assertRaises(RegisterError) as cm:
            prober._load_impl(prober2, True)
        self.assertRegex(str(cm.exception), r'already registered for \(22222222, 23, None\)')

    def test_reg_base_container_merge(self):
        prober1 = ClassCollector()
        prober2 = ClassCollector()
        frag1 = prober1.fragment(TagFragment('Frag1', 'Test', base_container=Section.base(Magic[2], 34), container_versions=2))
        frag2 = prober2.add_info(TagFragment('Frag2', 'Test'))

        with classes_on_module(frag1, frag2):
            for one_first in (True, False):
                with self.subTest(one_first=one_first):
                    prober = BytesProber()
                    if one_first:
                        prober._load_impl(prober1, True)
                        prober._load_impl(prober2, True)
                    else:
                        prober._load_impl(prober2, True)
                        prober._load_impl(prober1, True)
                    self.assertEqual((Magic[2], 34, None), prober.base_container_key('Test'))
                    self.assertEqual(frag2, prober.klass('Test'))

    def test_klass_teleporter_exit_version_new(self):
        cls = DefaultProbers.fragments.klass('TeleporterExit', version=1)
        from distance._impl.fragments.levelfragments import TeleporterExitFragment
        self.assertEqual(TeleporterExitFragment, cls)

    def test_klass_teleporter_exit_version_old(self):
        cls = DefaultProbers.fragments.klass('TeleporterExit', version=0)
        from distance._impl.fragments.npfragments import OldTeleporterExitFragment
        self.assertEqual(OldTeleporterExitFragment, cls)

    def test_create_teleporter_exit_version_new(self):
        frag = DefaultProbers.fragments.factory('TeleporterExit', version=1)()
        from distance._impl.fragments.levelfragments import TeleporterExitFragment
        self.assertEqual(
            (TeleporterExitFragment, Section(Magic[2], 0x3f, 1).to_key()),
            (type(frag), frag.container.to_key()))

    def test_create_teleporter_exit_version_old(self):
        frag = DefaultProbers.fragments.factory('TeleporterExit', version=0)()
        from distance._impl.fragments.npfragments import OldTeleporterExitFragment
        self.assertEqual(
            (OldTeleporterExitFragment, Section(Magic[2], 0x3f, 0).to_key()),
            (type(frag), frag.container.to_key()))

    def test_create_sets_container_and_object_type(self):
        obj = DefaultProbers.level_objects.create('CubeGS')
        self.assertEqual(obj.type, 'CubeGS')
        self.assertTrue(obj.container.to_key(), (Magic[6], 'CubeGS'))

    def test_created_object_can_be_written(self):
        obj = DefaultProbers.level_objects.create('CubeGS')

        res, rdb = write_read(obj)

        self.assertEqual(obj.type, 'CubeGS')
        self.assertTrue(obj.container.to_key(), (Magic[6], 'CubeGS'))


# vim:set sw=4 ts=8 sts=4 et:
