import unittest

from distance.lazy import LazySequence


class LazySequenceTest(unittest.TestCase):

    def setUp(self):
        self.orig = [10, 11, 12, 13, 14]
        self.iter = iter(self.orig)
        self.lazy = LazySequence(self.iter, 5)

    def _test_compare(self, *indices):
        for index in indices:
            with self.subTest(index=index):
                self.assertEqual(self.orig.__getitem__(index),
                                 self.lazy.__getitem__(index))

    def assertIndex(self, expect, index):
        """Compare with expect and with result of native list."""
        self.assertEqual(self.orig.__getitem__(index),
                         self.lazy.__getitem__(index))
        self.assertEqual(expect,
                         self.lazy.__getitem__(index))

    def test_inst(self):
        self.assertIndex(10, 0)
        self.assertEqual(11, next(self.iter))

    def test_memo(self):
        self.assertIndex(10, 0)
        self.assertIndex(10, 0)
        self.assertEqual(11, next(self.iter))

    def test_skip(self):
        self.assertIndex(12, 2)

    def test_skip_memo(self):
        self.assertIndex(12, 2)
        self.assertIndex(10, 0)
        self.assertEqual(13, next(self.iter))

    def test_slice(self):
        self.assertIndex([10, 11], slice(0, 2))
        self.assertEqual(12, next(self.iter))

    def test_slice_emptyend(self):
        self.assertIndex([11, 12, 13, 14], slice(1, None))

    def test_slice_emptystart(self):
        self.assertIndex([10, 11], slice(None, 2))
        self.assertEqual(12, next(self.iter))

    def test_slice_all(self):
        self.assertIndex([10, 11, 12, 13, 14], slice(None))

    def test_slice_empty(self):
        self.assertIndex([], slice(0))
        self.assertEqual(10, next(self.iter))

    def test_slice_empty_2(self):
        self.assertIndex([], slice(3, 2))
        self.assertEqual(10, next(self.iter))

    def test_slice_oob(self):
        self.assertIndex([], slice(7, 9))
        self.assertEqual(10, next(self.iter))

    def test_slice_oob_2(self):
        self.assertIndex([], slice(-12, -10))
        self.assertEqual(10, next(self.iter))

    def test_stride(self):
        self.assertIndex([11, 13], slice(1, 4, 2))
        self.assertEqual(14, next(self.iter))

    def test_stride_oob(self):
        self.assertIndex([10, 13], slice(0, 6, 3))
        self.assertEqual(14, next(self.iter))

    def test_stride_oob_2(self):
        self.assertIndex([11, 13], slice(1, 6, 2))
        self.assertEqual(14, next(self.iter))

    def test_stride_reverse(self):
        self.assertIndex([13, 12], slice(3, 1, -1))
        self.assertEqual(14, next(self.iter))

    def test_stride_reverse_2(self):
        self.assertIndex([13, 11], slice(3, 0, -2))
        self.assertEqual(14, next(self.iter))

    def test_stride_reverse_oob(self):
        self.assertIndex([14, 11], slice(5, 0, -3))

    def test_stride_reverse_oob_2(self):
        self.assertIndex([], slice(11, 12, -3))
        self.assertEqual(10, next(self.iter))

    def test_len(self):
        self.assertEqual(5, len(self.lazy))

    def test_earlyexit(self):
        next(self.iter) # steal an item
        self.assertEqual([11, 12, 13, 14], self.lazy[:])
        self.assertEqual(4, len(self.lazy))


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
