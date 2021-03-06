import unittest
from io import BytesIO
import struct

from distance.bytes import DstBytes


def new_bytes():
    buf = BytesIO()
    return buf, DstBytes(buf)


class WriteNumTest(unittest.TestCase):

    def _test_num(self, method, value, expect):
        buf, dbytes = new_bytes()

        method(dbytes, value)

        result = buf.getvalue()
        self.assertEqual(result, expect)

    def test_u4_small(self):
        self._test_num(DstBytes.write_uint, 0x12, b'\x12\x00\x00\x00')

    def test_u4_large(self):
        self._test_num(DstBytes.write_uint, 0x1234_5678, b'\x78\x56\x34\x12')

    def test_u4_max(self):
        self._test_num(DstBytes.write_uint, 0xFFFF_FFFF, b'\xFF\xFF\xFF\xFF')

    def test_u4_too_large(self):
        buf, dbytes = new_bytes()
        self.assertRaises(struct.error, dbytes.write_uint, 0x1_0000_0000)
        self.assertEqual(buf.getvalue(), b'')

    def test_u4_negative_raises(self):
        buf, dbytes = new_bytes()
        self.assertRaises(struct.error, dbytes.write_uint, -32)
        self.assertEqual(buf.getvalue(), b'')

    def test_i4_small(self):
        self._test_num(DstBytes.write_int, 0x12, b'\x12\x00\x00\x00')

    def test_i4_large(self):
        self._test_num(DstBytes.write_int, 0x1234_5678, b'\x78\x56\x34\x12')

    def test_i4_max(self):
        self._test_num(DstBytes.write_int, 0x7FFF_FFFF, b'\xFF\xFF\xFF\x7F')

    def test_i4_too_negative(self):
        buf, dbytes = new_bytes()
        with self.assertRaises(struct.error):
            dbytes.write_int(-0x8000_0001)
        self.assertEqual(buf.getvalue(), b'')

    def test_i4_too_large(self):
        buf, dbytes = new_bytes()
        with self.assertRaises(struct.error):
            dbytes.write_int(0x8000_0000)
        self.assertEqual(buf.getvalue(), b'')

    def test_i4_negative(self):
        self._test_num(DstBytes.write_int, -1, b'\xFF\xFF\xFF\xFF')

    def test_i8_small(self):
        self._test_num(DstBytes.write_long, 12, b'\x0c\x00\x00\x00\x00\x00\x00\x00')

    def test_i8_large(self):
        self._test_num(DstBytes.write_long, -128, b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF')


class WriteStringTest(unittest.TestCase):

    def _test_str(self, value, expect):
        buf, dbytes = new_bytes()

        dbytes.write_str(value)
        self.assertEqual(buf.getvalue(), expect)

    def test_empty(self):
        self._test_str("", b'\x00')

    def test_char(self):
        self._test_str("d", b"\x02d\x00")

    def test_more(self):
        self._test_str("WorkshopLevelInfos",
                       b'\x24W\x00o\x00r\x00k\x00s\x00h\x00o\x00p\x00'
                       b'L\x00e\x00v\x00e\x00l\x00I\x00n\x00f\x00o\x00s\x00')

    def test_nonascii(self):
        self._test_str("\u1234\u5678", b'\x04\x34\x12\x78\x56')

    def test_nonascii_2(self):
        self._test_str("\U00045678", b'\x04\xd5\xd8\x78\xde')

    def test_long(self):
        self._test_str("test" * 100,
                       b'\xa0\x06' + b't\x00e\x00s\x00t\x00' * 100)


class WriteSecnumTest(unittest.TestCase):

    def test_multiple(self):
        buf, dbytes = new_bytes()

        dbytes.write_id(1)
        dbytes.write_id(2)
        dbytes.write_id(3)

        self.assertEqual(buf.getvalue(),
                         b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00')


class WriteSizeTest(unittest.TestCase):

    def test_empty(self):
        buf, dbytes = new_bytes()

        with dbytes.write_size():
            pass

        self.assertEqual(buf.getvalue(),
                         b'\x00\x00\x00\x00\x00\x00\x00\x00')

    def test_withdata(self):
        buf, dbytes = new_bytes()

        with dbytes.write_size():
            dbytes.write_bytes(b'test')

        self.assertEqual(buf.getvalue(),
                         b'\x04\x00\x00\x00\x00\x00\x00\x00test')


# vim:set sw=4 ts=8 sts=4 et:
