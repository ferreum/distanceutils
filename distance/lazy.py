"""Lazy structures."""


from collections import Sequence


class LazySequence(Sequence):

    def __init__(self, iterator, length):
        self._iterator = iterator
        self._length = length
        self._list = []

    def __len__(self):
        return self._length

    def __getitem__(self, index):
        l = self._list
        current = len(l)
        mylen = self._length
        if isinstance(index, slice):
            start, stop, stride = index.indices(mylen)
            if stride < 0:
                if start <= stop:
                    return []
                end = start
            else:
                if stop <= start:
                    return []
                end = stop - 1
                end -= (mylen - end) % stride
        else:
            if index < 0:
                index = mylen + index
            if index >= mylen:
                raise IndexError(f"{index} >= {mylen}")
            if index < 0:
                raise IndexError(f"{index} < 0")
            end = index
        if end >= current:
            iterator = self._iterator
            try:
                for _ in range(end - current + 1):
                    l.append(next(iterator))
            except StopIteration:
                # This means the iterator ended earlier than the
                # reported length.
                self._iterator = None
                self._length = len(l)
        return l[index]


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
