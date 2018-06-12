import unittest

import construct as Con
from construct import ConstructError, FormatFieldError

from distance.bytes import DstBytes, Magic, Section
from distance.construct import C, BaseConstructFragment, ExposeConstructFields
from tests.common import write_read, check_exceptions


test_section = Section(Magic[2], 0x1337, 42)


@ExposeConstructFields
class TestFragment(BaseConstructFragment):

    default_section = test_section

    _format = C.struct(
        first_string = C.default(C.str, "default_str"),
        second_uint = C.default(C.uint, 12),
    )


@ExposeConstructFields
class NondefaultFragment(BaseConstructFragment):

    default_section = test_section

    _format = C.struct(
        first_string = C.str,
        second_uint = C.uint,
    )


@ExposeConstructFields
class ComplexFragment(BaseConstructFragment):

    default_section = test_section

    _format = C.struct(
        type = C.byte,
        value = Con.IfThenElse(Con.this.type == 0, C.byte, C.str)
    )


class TestFragmentTest(unittest.TestCase):

    def setUp(self):
        self.dbytes = db = DstBytes.in_memory()
        with db.write_section(test_section):
            db.write_str("a string")
            db.write_int(4, 64)
        db.seek(0)

        self.dbytes_empty = db = DstBytes.in_memory()
        with db.write_section(test_section):
            pass
        db.seek(0)

    def test_read(self):
        frag = TestFragment(self.dbytes)
        self.assertEqual(frag.first_string, "a string")
        self.assertEqual(frag.second_uint, 64)
        check_exceptions(frag)

    def test_write_read(self):
        frag = TestFragment(self.dbytes)
        res, rdb = write_read(frag)
        self.assertEqual(res.first_string, "a string")
        self.assertEqual(res.second_uint, 64)
        check_exceptions(res)

    def test_write_read_changed(self):
        frag = TestFragment(self.dbytes)
        frag.first_string = "new string"
        res, rdb = write_read(frag)
        self.assertEqual(frag.first_string, "new string")
        self.assertEqual(frag.second_uint, 64)
        check_exceptions(frag)

    def test_clone(self):
        frag = TestFragment(self.dbytes)
        res = frag.clone()
        self.assertEqual(res.first_string, "a string")
        self.assertEqual(res.second_uint, 64)

    def test_read_empty(self):
        frag = TestFragment(self.dbytes_empty)
        self.assertEqual(frag.first_string, "default_str")
        self.assertEqual(frag.second_uint, 12)
        check_exceptions(frag)

    def test_read_empty_nondefault(self):
        frag = NondefaultFragment(self.dbytes_empty)
        self.assertEqual(None, frag.first_string)
        self.assertEqual(None, frag.second_uint)
        check_exceptions(frag)


class TestFragment2Test(unittest.TestCase):

    def test_create_defaults(self):
        frag = TestFragment()
        self.assertEqual(frag.first_string, "default_str")
        self.assertEqual(frag.second_uint, 12)

    def test_create_partial_default(self):
        frag = TestFragment(second_uint=23)
        self.assertEqual(frag.first_string, "default_str")
        self.assertEqual(frag.second_uint, 23)

    def test_write_partial_default(self):
        frag = TestFragment(second_uint=23)
        res, db = write_read(frag)
        self.assertEqual(res.first_string, "default_str")
        self.assertEqual(res.second_uint, 23)
        check_exceptions(res)

    def test_create(self):
        frag = TestFragment(first_string="created", second_uint=32)
        self.assertEqual(frag.first_string, "created")
        self.assertEqual(frag.second_uint, 32)

    def test_clone_created(self):
        orig = TestFragment(first_string="text", second_uint=23)
        res = orig.clone()
        self.assertEqual(res.first_string, "text")
        self.assertEqual(res.second_uint, 23)

    def test_read_error(self):
        db = DstBytes.in_memory()
        with db.write_section(test_section):
            db.write_str("the string")
        db.seek(0)

        frag = TestFragment.maybe(db)

        self.assertIsInstance(frag.exception, ValueError)
        self.assertIsInstance(frag.exception.__cause__, ConstructError)

    def test_read_complex1(self):
        db = DstBytes.in_memory()
        with db.write_section(test_section):
            db.write_bytes(b'\0')
            db.write_bytes(b'\7')
        db.seek(0)

        frag = ComplexFragment(db)
        self.assertEqual(frag.type, 0)
        self.assertEqual(frag.value, 7)
        check_exceptions(frag)

    def test_read_complex2(self):
        db = DstBytes.in_memory()
        with db.write_section(test_section):
            db.write_bytes(b'\1')
            db.write_str("value string")
        db.seek(0)

        frag = ComplexFragment(db)
        self.assertEqual(frag.type, 1)
        self.assertEqual(frag.value, "value string")
        check_exceptions(frag)

    def test_write_complex1(self):
        db = DstBytes.in_memory()

        ComplexFragment(type=1, value="in value").write(db)

        db.seek(0)
        sec = Section(db)
        self.assertEqual(sec.to_key(), test_section.to_key())
        db.seek(sec.content_start)
        self.assertEqual(db.read_byte(), 1)
        self.assertEqual(db.read_str(), "in value")
        self.assertEqual(db.tell(), len(db.file.getbuffer()))

    def test_write_type_error(self):
        db = DstBytes.in_memory()
        frag = ComplexFragment(type=0, value="a string")
        self.assertRaises(FormatFieldError, frag.write, db)


# vim:set sw=4 ts=8 sts=4 et:
