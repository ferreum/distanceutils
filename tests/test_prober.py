import unittest

from distance.bytes import DstBytes, MAGIC_6
from distance.prober import BytesProber
from distance.base import BaseObject
from distance.knowntypes import read


class TestObject(BaseObject):

    def __init__(self, **kw):
        self.init_args = kw


class ProberTest(unittest.TestCase):

    def test_read_creates_plain_object(self):
        prober = BytesProber()
        prober.add_func(lambda *_: TestObject)
        obj = prober.read("tests/in/customobject/2cubes.bytes")
        self.assertEqual(True, obj.init_args['plain'])

    def test_maybe_catches_exception(self):
        prober = BytesProber()
        prober.add_func(lambda *_: TestObject)
        dbytes = DstBytes.in_memory()
        dbytes.write_int(4, MAGIC_6)
        dbytes.seek(0)
        obj = prober.maybe(dbytes)
        self.assertEqual(EOFError, type(obj.exception))

    def test_maybe_propagates_io_exception(self):
        prober = BytesProber()
        prober.add_func(lambda *_: TestObject)
        dbytes = DstBytes.in_memory()
        dbytes.write_int(4, MAGIC_6)
        dbytes.seek(0)
        def raise_error(*_):
            raise IOError
        dbytes.read_int = raise_error
        self.assertRaises(IOError, prober.maybe, dbytes)


class RegisteredTest(unittest.TestCase):

    def test_levelinfos(self):
        for ver in range(0, 1):
            with self.subTest(version=ver):
                result = read(f"tests/in/workshoplevelinfos/version_{ver}.bytes")
                self.assertEqual("WorkshopLevelInfos", type(result).__name__)

    def test_leaderboard(self):
        for ver in range(0, 2):
            with self.subTest(version=ver):
                result = read(f"tests/in/leaderboard/version_{ver}.bytes")
                self.assertEqual("Leaderboard", type(result).__name__)

    def test_replay(self):
        for ver in range(1, 5):
            with self.subTest(version=ver):
                result = read(f"tests/in/replay/version_{ver}.bytes")
                self.assertEqual("Replay", type(result).__name__)

    def test_level(self):
        for levelfile in ("test-straightroad",):
            with self.subTest(levelfile=levelfile):
                result = read(f"tests/in/level/{levelfile}.bytes")
                self.assertEqual("Level", type(result).__name__)


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
