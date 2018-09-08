import unittest
from contextlib import contextmanager

from distance.bytes import DstBytes, Magic, Section
from distance.classes import TagError, ProbeError, ClassLookupError, ClassCollector, ClassCollection, RegisterError
from distance.base import Fragment, BaseObject, ObjectFragment
from distance.levelobjects import LevelObject
from distance import DefaultClasses, Level, Replay, Leaderboard, WorkshopLevelInfos
from distance._impl.fragments.levelfragments import GoldenSimplesFragment
from distance._impl.level_objects.objects import GoldenSimple
from distance._impl.level_objects.group import Group
from distance._impl.level_objects.objects import OldSimple
from .common import write_read, check_exceptions, assertLargeEqual


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

    def fallback_func(self, *args):
        class TestObject(BaseObject):

            def __init__(self, **kw):
                self.init_args = kw
        return TestObject


    def test_read_creates_plain_object(self):
        coll = ClassCollection()
        coll.add_func(self.fallback_func, 'fallback')
        obj = coll.read("tests/in/customobject/2cubes.bytes")
        self.assertEqual(True, obj.init_args['plain'])

    def test_maybe_catches_exception(self):
        coll = ClassCollection(baseclass=BaseObject)
        coll.add_func(self.fallback_func, 'fallback')
        dbytes = DstBytes.in_memory()
        dbytes.write_uint(Magic[6])
        dbytes.seek(0)
        obj = coll.maybe(dbytes)
        self.assertEqual(EOFError, type(obj.exception))

    def test_maybe_propagates_io_exception(self):
        coll = ClassCollection()
        coll.add_func(self.fallback_func, 'fallback')
        dbytes = DstBytes.in_memory()
        dbytes.write_uint(Magic[6])
        dbytes.seek(0)
        def raise_error(*_):
            raise IOError
        dbytes.read_bytes = raise_error
        self.assertRaises(IOError, coll.maybe, dbytes)


class RegisteredTest(unittest.TestCase):

    def test_levelinfos(self):
        for ver in range(0, 1):
            with self.subTest(version=ver):
                result = DefaultClasses.file.read(f"tests/in/workshoplevelinfos/version_{ver}.bytes")
                self.assertIsInstance(result, WorkshopLevelInfos)

    def test_leaderboard(self):
        for ver in range(0, 2):
            with self.subTest(version=ver):
                result = DefaultClasses.file.read(f"tests/in/leaderboard/version_{ver}.bytes")
                self.assertIsInstance(result, Leaderboard)

    def test_replay(self):
        for ver in range(1, 5):
            with self.subTest(version=ver):
                result = DefaultClasses.file.read(f"tests/in/replay/version_{ver}.bytes")
                self.assertIsInstance(result, Replay)

    def test_create_replay(self):
        obj = DefaultClasses.common.create('Replay', type='Replay: Test')
        self.assertIsInstance(obj, Replay)
        self.assertEqual(obj.type, 'Replay: Test')

    def test_level(self):
        result = DefaultClasses.file.read(f"tests/in/level/test-straightroad.bytes")
        self.assertIsInstance(result, Level)

    def test_level_like_level(self):
        result = DefaultClasses.level_like.read(f"tests/in/level/test-straightroad.bytes")
        self.assertIsInstance(result, Level)

    def test_level_like_group(self):
        result = DefaultClasses.level_like.read(f"tests/in/customobject/2cubes.bytes")
        self.assertIsInstance(result, Group)

    def test_level_like_object(self):
        result = DefaultClasses.level_like.read(f"tests/in/customobject/oldsimple cube.bytes")
        self.assertIsInstance(result, OldSimple)

    def test_level_like_blacklist(self):
        files = ["tests/in/replay/version_1.bytes",
                 "tests/in/leaderboard/version_0.bytes",
                 "tests/in/profileprogress/new profile.bytes",
                 "tests/in/levelinfos/LevelInfos.bytes",
                 "tests/in/workshoplevelinfos/version_0.bytes",
                 "tests/in/fragment/animator v7.frag"]
        for file in files:
            with self.subTest(file=file):
                self.assertRaises(ProbeError, DefaultClasses.level_like.read, file)

    def test_customobject_object(self):
        result = DefaultClasses.customobjects.read("tests/in/customobject/2cubes.bytes")

        self.assertIsInstance(result, Group)

    def test_customobject_blacklist(self):
        files = ["tests/in/level/test-straightroad.bytes",
                 "tests/in/replay/version_1.bytes",
                 "tests/in/leaderboard/version_0.bytes",
                 "tests/in/profileprogress/new profile.bytes",
                 "tests/in/levelinfos/LevelInfos.bytes",
                 "tests/in/workshoplevelinfos/version_0.bytes",
                 "tests/in/fragment/animator v7.frag"]
        for file in files:
            with self.subTest(file=file):
                self.assertRaises(ProbeError, DefaultClasses.customobjects.read, file)


class UnknownObjectFileTest(unittest.TestCase):

    def setUp(self):
        self.db = db = DstBytes.in_memory()
        with db.write_section(Magic[6], '__distanceutils__test__object__'):
            pass
        db.seek(0)

    def test_unknown_file(self):
        obj = DefaultClasses.file.read(self.db)

        self.assertEqual(type(obj), LevelObject)

    def test_unknown_level_like(self):
        obj = DefaultClasses.level_like.read(self.db)

        self.assertEqual(obj.type, '__distanceutils__test__object__')

    def test_unknown_non_level_objects(self):
        with self.assertRaises(ProbeError):
            DefaultClasses.non_level_objects.read(self.db)


class VerifyTest(unittest.TestCase):

    def test_classes_validity(self):
        DefaultClasses._verify_autoload()

    def test_autoload_is_uptodate(self):
        actual, loaded = DefaultClasses._verify_autoload()
        assertLargeEqual(self, actual, loaded,
                         msg="autoload module is outdated")


class VerifyClassInfoTest(unittest.TestCase):

    def test_create_fragment(self):
        frag = DefaultClasses.fragments.create('Object')
        self.assertEqual(type(frag), ObjectFragment)

    def test_create_fragment_unknown_no_fallback(self):
        with self.assertRaises(TagError):
            DefaultClasses.fragments.create('SomeComponent')

    def test_create_fragment_autoloaded(self):
        frag = DefaultClasses.fragments.create('GoldenSimples')
        self.assertEqual(type(frag), GoldenSimplesFragment)

    def test_create_object_unknown_fallback(self):
        obj = DefaultClasses.level_objects.create('SomeThing')
        self.assertIsInstance(obj, LevelObject)
        self.assertEqual(obj.type, 'SomeThing')

    def test_create_object_unknown_disabled_fallback(self):
        with self.assertRaises(TagError):
            DefaultClasses.level_objects.create('SomeThing', fallback=False)

    def test_klass_level(self):
        cls = DefaultClasses.level.klass('Level')
        self.assertIs(cls, Level)

    def test_fragment_attrs_get(self):
        obj = GoldenSimple(type='CubeGS')
        self.assertEqual(obj.emit_index, 17)

    def test_fragment_attrs_get_with_missing_fragment(self):
        obj = GoldenSimple(type='CubeGS')
        del obj['GoldenSimples']
        with self.assertRaises(AttributeError):
            obj.emit_index

    def test_fragment_attrs_set(self):
        obj = GoldenSimple(type='CubeGS')
        obj.emit_index = 23
        self.assertEqual(obj.emit_index, 23)

    def test_fragment_attrs_set_with_missing_fragment(self):
        obj = GoldenSimple(type='CubeGS')
        del obj['GoldenSimples']
        with self.assertRaises(AttributeError):
            obj.emit_index = 23

    def test_registration_version_merge(self):
        src1 = ClassCollector()
        src2 = ClassCollector()
        base = Section.base(Magic[2], 23)
        frag1 = src1.fragment(TagFragment('Frag1', 'Test', base_container=base, container_versions=1))
        frag5 = src2.fragment(TagFragment('Frag5', 'Test', base_container=base, container_versions=5))
        frag23 = src2.fragment(TagFragment('Frag23', 'Test', base_container=base, container_versions=(2, 3)))
        glob = globals()
        glob['Frag1'] = frag1
        glob['Frag23'] = frag23
        glob['Frag5'] = frag5

        with classes_on_module(frag1, frag23, frag5):
            coll = ClassCollection()
            coll._load_impl(src1, True)
            coll._load_impl(src2, True)

            def sec(ver):
                return Section(base=base, version=ver).to_key()
            def get_klass(*args, **kw):
                fact = coll.factory(*args, **kw)
                return fact.cls, fact.container.to_key()
            self.assertEqual(coll.get_base_key('Test'), base.to_key())
            self.assertEqual((frag1, sec(1)), get_klass('Test', version=1))
            self.assertEqual((frag23, sec(2)), get_klass('Test', version=2))
            self.assertEqual((frag23, sec(3)), get_klass('Test', version=3))
            self.assertEqual((frag5, sec(5)), get_klass('Test', version=5))

    def test_reg_version_conflict(self):
        src1 = ClassCollector()
        src2 = ClassCollector()
        base = Section.base(Magic[2], 23)
        src1.fragment(TagFragment('Frag1', 'Test', base_container=base, container_versions=1))
        src2.fragment(TagFragment('Frag2', 'Test', base_container=base, container_versions=(1, 2)))

        coll = ClassCollection()
        coll._load_impl(src1, True)
        with self.assertRaises(RegisterError) as cm:
            coll._load_impl(src2, True)
        self.assertRegex(str(cm.exception), r'already registered for .*Frag1')

    def test_reg_base_container_conflict(self):
        src1 = ClassCollector()
        src2 = ClassCollector()
        src1.fragment(TagFragment('Frag1', 'Test', base_container=Section.base(Magic[2], 23), container_versions=1))
        src2.fragment(TagFragment('Frag2', 'Test', base_container=Section.base(Magic[2], 34), container_versions=2))

        coll = ClassCollection()
        coll._load_impl(src1, True)
        with self.assertRaises(RegisterError) as cm:
            coll._load_impl(src2, True)
        self.assertRegex(str(cm.exception), r'already registered for \(22222222, 23, None\)')

    def test_reg_base_container_merge(self):
        src1 = ClassCollector()
        src2 = ClassCollector()
        frag1 = src1.fragment(TagFragment('Frag1', 'Test', base_container=Section.base(Magic[2], 34), container_versions=2))
        frag2 = src2.add_info(TagFragment('Frag2', 'Test'))

        with classes_on_module(frag1, frag2):
            for one_first in (True, False):
                with self.subTest(one_first=one_first):
                    coll = ClassCollection()
                    if one_first:
                        coll._load_impl(src1, True)
                        coll._load_impl(src2, True)
                    else:
                        coll._load_impl(src2, True)
                        coll._load_impl(src1, True)
                    self.assertEqual((Magic[2], 34, None), coll.get_base_key('Test'))
                    self.assertEqual(frag2, coll.klass('Test'))

    def test_add_tag(self):
        src = ClassCollector()
        src.add_tag('Test', Magic[2], 0x9001)

        coll = ClassCollection()
        coll._load_impl(src, True)

        self.assertEqual(coll.get_base_key('Test'), (Magic[2], 0x9001, None))

    def test_get_tag(self):
        src = ClassCollector()
        src.add_tag('Test', Magic[2], 0x9001)

        coll = ClassCollection()
        coll._load_impl(src, True)

        self.assertEqual(coll.get_tag(Section(Magic[2], 0x9001, 12)), 'Test')

    def test_get_tag_missing(self):
        coll = ClassCollection()

        with self.assertRaises(KeyError):
            coll.get_tag(Section(Magic[2], 0x9001, 12))

    def test_get_tag_goldensimples(self):
        res = DefaultClasses.fragments.get_tag(Section(Magic[2], 0x83, 2323))

        self.assertEqual(res, 'GoldenSimples')

    def test_get_base_key(self):
        coll = ClassCollection()
        coll.fragment(TagFragment('Frag1', 'Test', default_container=Section.base(Magic[2], 34, 3)))

        res = coll.get_base_key('Test')

        self.assertEqual(res, Section.base(Magic[2], 34).to_key())

    def test_get_base_key_missing(self):
        coll = ClassCollection()

        with self.assertRaises(TagError) as cm:
            coll.get_base_key('Test')
        self.assertRegex(str(cm.exception), r"'Test'")

    def test_get_base_key_typeerror(self):
        coll = ClassCollection()

        with self.assertRaises(TypeError):
            coll.get_base_key(object())

    def test_klass_teleporter_exit_version_new(self):
        cls = DefaultClasses.fragments.klass('TeleporterExit', version=1)
        from distance._impl.fragments.levelfragments import TeleporterExitFragment
        self.assertEqual(TeleporterExitFragment, cls)

    def test_klass_teleporter_exit_version_old(self):
        cls = DefaultClasses.fragments.klass('TeleporterExit', version=0)
        from distance._impl.fragments.npfragments import OldTeleporterExitFragment
        self.assertEqual(OldTeleporterExitFragment, cls)

    def test_klass_invalid_version(self):
        with self.assertRaises(ClassLookupError) as cm:
            DefaultClasses.fragments.klass('GoldenSimples', version=999)
        self.assertEqual(str(cm.exception), "'GoldenSimples', version=999")

    def test_create_teleporter_exit_version_new(self):
        frag = DefaultClasses.fragments.factory('TeleporterExit', version=1)()
        from distance._impl.fragments.levelfragments import TeleporterExitFragment
        self.assertEqual(
            (TeleporterExitFragment, Section(Magic[2], 0x3f, 1).to_key()),
            (type(frag), frag.container.to_key()))

    def test_create_teleporter_exit_version_old(self):
        frag = DefaultClasses.fragments.factory('TeleporterExit', version=0)()
        from distance._impl.fragments.npfragments import OldTeleporterExitFragment
        self.assertEqual(
            (OldTeleporterExitFragment, Section(Magic[2], 0x3f, 0).to_key()),
            (type(frag), frag.container.to_key()))

    def test_create_sets_container_and_object_type(self):
        obj = DefaultClasses.level_objects.create('CubeGS')
        self.assertEqual(obj.type, 'CubeGS')
        self.assertTrue(obj.container.to_key(), (Magic[6], 'CubeGS'))

    def test_created_object_can_be_written(self):
        obj = DefaultClasses.level_objects.create('CubeGS')

        res, rdb = write_read(obj)

        self.assertEqual(obj.type, 'CubeGS')
        self.assertTrue(obj.container.to_key(), (Magic[6], 'CubeGS'))

    def test_create_with_dbytes(self):
        obj = DefaultClasses.level_objects.create('Group', dbytes='tests/in/customobject/2cubes.bytes')

        self.assertEqual(obj.type, 'Group')
        self.assertEqual(len(obj.children), 2)
        check_exceptions(obj)

    def test_factory_with_dbytes(self):
        obj = DefaultClasses.level_objects.factory('Group')(dbytes='tests/in/customobject/2cubes.bytes')

        self.assertEqual(obj.type, 'Group')
        self.assertEqual(len(obj.children), 2)
        check_exceptions(obj)


# vim:set sw=4 ts=8 sts=4 et:
