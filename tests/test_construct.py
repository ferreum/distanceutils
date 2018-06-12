import unittest

from construct import ConstructError

from distance.bytes import DstBytes, Magic
from distance.construct import C, BaseConstructFragment, ExposeConstructFields
from tests.common import write_read


@ExposeConstructFields
class TestFragment(BaseConstructFragment):

    _format = C.struct(
        first_string = C.str,
        second_uint = C.uint,
    )


class TestFragmentTest(unittest.TestCase):

    def setUp(self):
        self.dbytes = db = DstBytes.in_memory()
        with db.write_section(Magic[2], 0x1337, 42):
            db.write_str("a string")
            db.write_int(4, 64)
        db.seek(0)

    def test_read(self):
        frag = TestFragment(self.dbytes)
        self.assertEqual(frag.first_string, "a string")
        self.assertEqual(frag.second_uint, 64)

    def test_write_read(self):
        frag = TestFragment(self.dbytes)
        res, rdb = write_read(frag)
        self.assertEqual(res.first_string, "a string")
        self.assertEqual(res.second_uint, 64)


class TestError(unittest.TestCase):

    def test_construct_error(self):
        db = DstBytes.in_memory()
        with db.write_section(Magic[2], 0x1337, 42):
            db.write_str("the string")
        db.seek(0)

        frag = TestFragment.maybe(db)

        self.assertIsInstance(frag.exception, ValueError)
        self.assertIsInstance(frag.exception.__cause__, ConstructError)

# vim:set sw=4 ts=8 sts=4 et:
