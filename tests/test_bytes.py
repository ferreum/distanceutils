import unittest
from contextlib import contextmanager

from distance.bytes import DstBytes, MAGIC_6


class DstBytesTest(unittest.TestCase):

    def test_from_arg_dstbytes(self):
        with open("tests/in/customobject/2cubes.bytes", 'rb') as f:
            dbytes = DstBytes(f)

            res = DstBytes.from_arg(dbytes)

            self.assertIs(dbytes, res)

    def test_from_arg_filename(self):
        res = DstBytes.from_arg("tests/in/customobject/2cubes.bytes")

        self.assertEqual(MAGIC_6, res.read_int(4))

    def test_from_arg_file(self):
        with open("tests/in/customobject/2cubes.bytes", 'rb') as f:

            res = DstBytes.from_arg(f)

            self.assertEqual(MAGIC_6, res.read_int(4))

    def test_from_arg_checks_file_mode(self):
        with open("tests/in/customobject/2cubes.bytes") as f:
            self.assertRaises(IOError, DstBytes.from_arg, f)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0: