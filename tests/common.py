import unittest
from io import BytesIO

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


class WriteReadTest(unittest.TestCase):

    """Base Write/Read test.

    Subclasses need to define:

    read_obj - function to read the actual object

    filename - str, the filanem

    verify_obj - function to verify the read object

    optional:
    read_obj_pre -
        used instead of read_obj before writing,
        read_obj is used otherwise

    """

    exact = True

    def read_obj_pre(self, dbytes):
        return self.read_obj(dbytes)

    def test_read(self):
        with open(self.filename, 'rb') as f:
            res = self.read_obj(DstBytes(f))

            self.verify_obj(res)

    def test_write_read(self):
        with open(self.filename, 'rb') as f:
            dbr = DstBytes(f)
            orig = self.read_obj_pre(dbr)
            orig_len = orig.layers[-1].end_pos

            res, buf = write_read(orig)

            self.verify_obj(res)
            self.assertEqual(orig_len, len(buf.getbuffer()))

            if self.exact:
                f.seek(0)
                self.assertEqual(f.read(), buf.getbuffer())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
