import unittest
from io import BytesIO
from contextlib import contextmanager

from distance.bytes import DstBytes
from distance.level import Level, Layer
from distance.base import BaseObject


def disable_writes(dbytes):
    def do_raise(*args, **kwargs):
        raise AssertionError("attempted to write")
    dbytes.write_bytes = do_raise


def check_exceptions(obj):
    if obj.exception:
        raise obj.exception
    if isinstance(obj, Level):
        check_exceptions(obj.settings)
        for layer in obj.layers:
            check_exceptions(layer)
    if isinstance(obj, Layer):
        for obj in obj.objects:
            check_exceptions(obj)
    if isinstance(obj, BaseObject):
        for frag in obj.fragments:
            check_exceptions(frag)
        for child in obj.children:
            check_exceptions(child)


def write_read(obj, read_func=None):
    if read_func is None:
        read_func = type(obj)

    dbytes = DstBytes.in_memory()

    obj.write(dbytes)
    dbytes.seek(0)
    disable_writes(dbytes)
    result = read_func(dbytes)

    check_exceptions(result)

    return result, dbytes.file


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

    skip_if_missing = False

    def read_obj_pre(self, dbytes):
        return self.read_obj(dbytes)

    @contextmanager
    def open(self, filename):
        try:
            with open(filename, 'rb') as f:
                yield f
        except FileNotFoundError:
            if self.skip_if_missing:
                self.skipTest("file {filename!r} is missing")
            raise

    def test_read(self):
        with self.open(self.filename) as f:
            res = self.read_obj(DstBytes(f))

            self.verify_obj(res)

    def test_write_read(self):
        with self.open(self.filename) as f:
            orig_bytes = f.read()
            orig_buf = BytesIO(orig_bytes)

        dbr = DstBytes(orig_buf)
        orig = self.read_obj_pre(dbr)
        orig_len = len(orig_bytes)

        res, buf = write_read(orig, read_func=self.read_obj)

        self.verify_obj(res)
        self.assertEqual(orig_len, len(buf.getbuffer()))

        if self.exact:
            self.assertEqual(orig_bytes, buf.getvalue())


class ExtraAssertMixin(object):

    def assertSeqAlmostEqual(self, a, b, msg="", **kw):
        if msg:
            msg = f" :\n{msg}"
        if len(a) != len(b):
            self.assertEqual(a, b)
            raise AssertionError(f"{a} != {b}\na={a}\nb={b}{msg}")
        for i, (va, vb) in enumerate(zip(a, b)):
            self.assertAlmostEqual(va, vb, msg=f"\nindex={i}\na={a}\nb={b}{msg}", **kw)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
