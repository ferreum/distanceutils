import unittest

import construct as Con
from construct import ConstructError, FormatFieldError

from distance.bytes import DstBytes, Magic, Section, SKIP_BYTES
from distance.construct import (
    BaseConstructFragment,
    Byte, UInt, Long, DstString,
    Struct, Default, DstOptional, Remainder,
)
from tests.common import write_read, check_exceptions


test_section = Section(Magic[2], 0x1337, 42)


class TestFragment(BaseConstructFragment):

    default_container = test_section

    _construct = Struct(
        first_string = Default(DstString, "default_str"),
        second_uint = Default(UInt, 12),
    )


class NondefaultFragment(BaseConstructFragment):

    default_container = test_section

    _construct = Struct(
        first_string = DstString,
        second_uint = UInt,
    )


class ComplexFragment(BaseConstructFragment):

    default_container = test_section

    _construct = Struct(
        type = Byte,
        value = Con.IfThenElse(Con.this.type == 0, Byte, DstString)
    )


class OptionalFragment(BaseConstructFragment):

    default_container = test_section

    _construct = Struct(
        value = DstOptional(DstString)
    )


class RemainderFragment(BaseConstructFragment):

    default_container = test_section

    _construct = Struct(
        value = DstString,
        rem = Remainder,
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

    def test_remainder_empty(self):
        db = DstBytes.in_memory()
        with db.write_section(test_section):
            db.write_str("test")
        db.seek(0)

        frag = RemainderFragment(db)

        self.assertEqual(frag.rem, b'')

    def test_remainder_write_read(self):
        frag = RemainderFragment(self.dbytes)

        res, rdb = write_read(frag)

        self.assertEqual(res.value, "a string")
        self.assertEqual(res.rem, b'\x40\0\0\0')

    def test_remainder_modify_write_read(self):
        frag = RemainderFragment(self.dbytes)
        frag.value = "new str"

        res, rdb = write_read(frag)

        self.assertEqual(res.value, "new str")
        self.assertEqual(res.rem, b'\x40\0\0\0')

    def test_remainder_create_write_read(self):
        frag = RemainderFragment(value="test str", rem=b'')

        res, rdb = write_read(frag)

        self.assertEqual(res.value, "test str")
        self.assertEqual(res.rem, b'')


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
        self.assertEqual(db.file.read(), b'')

    def test_write_type_error(self):
        db = DstBytes.in_memory()
        frag = ComplexFragment(type=0, value="a string")
        self.assertRaises(FormatFieldError, frag.write, db)

    def test_single_exposed_field(self):
        class TestFragment(BaseConstructFragment):
            _exposed_fields = 'a_uint'
            _construct = Struct(
                a_uint = UInt,
                a_string = DstString,
            )
        self.assertTrue(hasattr(TestFragment, 'a_uint'))
        self.assertFalse(hasattr(TestFragment, 'a_string'))

    def test_exposed_fields(self):
        class TestFragment(BaseConstructFragment):
            _exposed_fields = 'a_uint', 'a_string'
            _construct = Struct(
                a_uint = UInt,
                a_string = DstString,
                a_long = Long,
            )
        self.assertTrue(hasattr(TestFragment, 'a_uint'))
        self.assertTrue(hasattr(TestFragment, 'a_string'))
        self.assertFalse(hasattr(TestFragment, 'a_long'))

    def test_compiled(self):
        class TestFragment(BaseConstructFragment):
            _construct = 'my_struct' / Struct(
                uint = UInt,
            ).compile()
        db = DstBytes.in_memory()
        with db.write_section(test_section):
            db.write_int(4, 135)
        db.seek(0)

        frag = TestFragment(db)

        self.assertEqual(frag.uint, 135)


class OptionalTest(unittest.TestCase):

    def test_read_subcon(self):
        db = DstBytes.in_memory()
        with db.write_section(test_section):
            db.write_str("test string")
        db.seek(0)

        frag = OptionalFragment(db)

        self.assertEqual(frag.value, "test string")
        check_exceptions(frag)

    def test_read_subcon_short(self):
        db = DstBytes.in_memory()
        with db.write_section(test_section):
            db.write_str("")
        db.seek(0)

        frag = OptionalFragment(db)

        self.assertEqual(frag.value, "")
        check_exceptions(frag)

    def test_read_absent(self):
        db = DstBytes.in_memory()
        with db.write_section(test_section):
            db.write_bytes(SKIP_BYTES)
        db.seek(0)

        frag = OptionalFragment(db)

        self.assertEqual(frag.value, None)
        check_exceptions(frag)

    def test_read_empty(self):
        db = DstBytes.in_memory()
        with db.write_section(test_section):
            pass
        db.seek(0)

        frag = OptionalFragment(db)

        self.assertEqual(frag.value, None)

    def test_write_subcon(self):
        db = DstBytes.in_memory()

        OptionalFragment(value="test").write(db)

        db.seek(0)
        sec = Section(db)
        db.seek(sec.content_start)
        self.assertEqual(db.read_str(), "test")
        self.assertEqual(db.file.read(), b'')

    def test_write_absent(self):
        db = DstBytes.in_memory()

        OptionalFragment(value=None).write(db)

        db.seek(0)
        sec = Section(db)
        db.seek(sec.content_start)
        self.assertEqual(db.file.read(), SKIP_BYTES)


# vim:set sw=4 ts=8 sts=4 et:
