import unittest

from distance.bytes import DstBytes, Magic, Section


class DstBytesTest(unittest.TestCase):

    def test_from_arg_dstbytes(self):
        with open("tests/in/customobject/2cubes.bytes", 'rb') as f:
            dbytes = DstBytes(f)

            res = DstBytes.from_arg(dbytes)

            self.assertIs(dbytes, res)

    def test_from_arg_filename(self):
        res = DstBytes.from_arg("tests/in/customobject/2cubes.bytes")

        self.assertEqual(Magic[6], res.read_uint())

    def test_from_arg_file(self):
        with open("tests/in/customobject/2cubes.bytes", 'rb') as f:

            res = DstBytes.from_arg(f)

            self.assertEqual(Magic[6], res.read_uint())

    def test_from_arg_checks_file_mode(self):
        with open("tests/in/customobject/2cubes.bytes") as f:
            with self.assertRaises(IOError) as cm:
                DstBytes.from_arg(f)
            msg = str(cm.exception)
            self.assertTrue("'b' mode" in msg, msg=f"actual message: {msg!r}")


class SectionTest(unittest.TestCase):

    def test_from_key_magic9(self):
        key = Section(Magic[9], 'A Level').to_key()

        sec = Section.from_key(key)

        self.assertEqual(sec.magic, Magic[9])
        self.assertEqual(sec.name, None)


# vim:set sw=4 ts=8 sts=4 et:
