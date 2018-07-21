import unittest
from io import BytesIO
from contextlib import contextmanager
from collections import Sequence

from distance.bytes import DstBytes
from distance.level import Level
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
    if isinstance(obj, BaseObject):
        for frag in obj.fragments:
            check_exceptions(frag)
        for child in obj.children:
            check_exceptions(child)
    if obj.class_tag == 'Layer':
        for obj in obj.objects:
            check_exceptions(obj)


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


def read_or_skip(cls, filename, *args, **kw):
    try:
        return cls(filename, *args, **kw)
    except FileNotFoundError:
        raise unittest.SkipTest(f"file {filename!r} is missing")


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

    modify_obj -
        used to make a test modification to the object.

    """

    cmp_bytes = True
    exact = True

    skip_if_missing = False

    def read_obj_pre(self, dbytes):
        return self.read_obj(dbytes)

    def modify_obj(self, obj):
        return obj

    @contextmanager
    def open(self, filename):
        try:
            with open(filename, 'rb') as f:
                yield f
        except FileNotFoundError:
            if self.skip_if_missing:
                self.skipTest(f"file {filename!r} is missing")
            raise

    def test_read(self):
        with self.open(self.filename) as f:
            res = self.read_obj(DstBytes(f))
            res = self.modify_obj(res)

            self.verify_obj(res)

    def test_write_read(self):
        with self.open(self.filename) as f:
            orig_bytes = f.read()
            orig_buf = BytesIO(orig_bytes)

        dbr = DstBytes(orig_buf)
        orig = self.read_obj_pre(dbr)
        orig_len = len(orig_bytes)

        modified = self.modify_obj(orig)
        res, buf = write_read(modified, read_func=self.read_obj)

        self.verify_obj(res)
        if self.cmp_bytes:
            if orig_bytes != buf.getvalue():
                from distance_scripts.verify import listdiffs
                listdiffs(orig, res)
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
            if isinstance(va, Sequence):
                self.assertSeqAlmostEqual(va, vb)
            else:
                self.assertAlmostEqual(va, vb, msg=f"\nindex={i}\na={a}\nb={b}{msg}", **kw)


# vim:set sw=4 ts=8 sts=4 et:
