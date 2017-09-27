import unittest
from io import BytesIO

from distance.level import Level
from distance.bytes import DstBytes


def disable_writes(dbytes):
    def do_raise(*args, **kwargs):
        raise AssertionError("attempted to write")
    dbytes.write_bytes = do_raise


def write_read(obj, read_func=None):
    if read_func is None:
        read_func = type(obj)

    buf = BytesIO()
    dbytes = DstBytes(buf)

    obj.write(dbytes)
    dbytes.pos = 0
    disable_writes(dbytes)
    result = read_func(dbytes)

    if result.exception:
        raise result.exception

    return result, buf


class Base(object):

    class WriteReadTest(unittest.TestCase):

        exact = True

        def test_read(self):
            with open(self.filename, 'rb') as f:
                res = Level(DstBytes(f))

                self.verify_level(res)

        def test_write_read(self):
            with open(self.filename, 'rb') as f:
                dbr = DstBytes(f)
                orig = Level(dbr)
                orig_len = orig.layers[-1].end_pos

                res, buf = write_read(orig)

                self.verify_level(res)
                self.assertEqual(orig_len, len(buf.getbuffer()))

                if self.exact:
                    f.seek(0)
                    self.assertEqual(f.read(), buf.getbuffer())


class StraightroadTest(Base.WriteReadTest):

    filename = "tests/in/level/test-straightroad.bytes"

    def verify_level(self, level):
        self.assertEqual("Test-straightroad", level.level_name)
        self.assertEqual(6, len([o for l in level.layers for o in l.objects]))


class TheVirusBeginsS8Test(Base.WriteReadTest):

    filename = "tests/in/level-not-included/v1/the virus begins.bytes"

    def verify_level(self, level):
        self.assertEqual("The Virus Begins", level.level_name)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
