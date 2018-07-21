import unittest

from distance.bytes import DstBytes, Magic, Section
from distance.prober import BytesProber
from distance.base import BaseObject, ObjectFragment
from distance.levelobjects import LevelObject
from distance import DefaultProbers
from distance._impl.fragments.levelfragments import GoldenSimplesFragment
from distance._impl.level_objects.objects import GoldenSimple


class TestObject(BaseObject):

    def __init__(self, **kw):
        self.init_args = kw


def TagClass(tag_):
    class TagClass(BaseObject):
        tag = tag_
    return TagClass


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


class TransactionTest(unittest.TestCase):

    def test_func(self):
        prober = BytesProber()
        t = prober.transaction()
        def never_call(s):
            assert False, "old func called"
        t.func('test')(never_call)
        t.commit()
        t = prober.transaction()
        t.func('test')(lambda s: TagClass(2))
        t.commit()
        res = prober.probe_section(Section(Magic[6], 't'))
        self.assertEqual(res.tag, 2)


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

    def test_fragment_by_tag_object(self):
        obj = BaseObject()
        frag = obj.fragment_by_tag('Object')
        self.assertEqual(frag, obj.fragments[0])

    def test_fragment_by_tag_goldensimples(self):
        obj = GoldenSimple(type='CubeGS')
        frag = obj.fragment_by_tag('GoldenSimples')
        expect = next(f for f in obj.fragments if isinstance(f, GoldenSimplesFragment))
        self.assertEqual(frag, expect)


# vim:set sw=4 ts=8 sts=4 et:
