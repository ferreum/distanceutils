import unittest
from contextlib import contextmanager

from distance.bytes import DstBytes
from distance.knowntypes import read


@contextmanager
def bytes_from(name):
    with open(name, 'rb') as f:
        yield DstBytes(f)


class ProberTest(unittest.TestCase):

    def test_levelinfos(self):
        for ver in range(0, 1):
            with self.subTest(version=ver):
                with bytes_from(f"tests/in/workshoplevelinfos/version_{ver}.bytes") as dbytes:
                    result = read(dbytes)
                    self.assertEqual("WorkshopLevelInfos", type(result).__name__)

    def test_leaderboard(self):
        for ver in range(0, 2):
            with self.subTest(version=ver):
                with bytes_from(f"tests/in/leaderboard/version_{ver}.bytes") as dbytes:
                    result = read(dbytes)
                    self.assertEqual("Leaderboard", type(result).__name__)

    def test_replay(self):
        for ver in range(1, 5):
            with self.subTest(version=ver):
                with bytes_from(f"tests/in/replay/version_{ver}.bytes") as dbytes:
                    result = read(dbytes)
                    self.assertEqual("Replay", type(result).__name__)

    def test_level(self):
        for levelfile in ("test-straightroad",):
            with self.subTest(levelfile=levelfile):
                with bytes_from(f"tests/in/level/{levelfile}.bytes") as dbytes:
                    result = read(dbytes)
                    self.assertEqual("Level", type(result).__name__)


if __name__ == '__main__':
    unittest.main()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
