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
        if index >= self._length:
            raise IndexError(f"{index} >= {self._length}")
        if index < 0:
            raise IndexError(f"{index} < 0")
        l = self._list
        current = len(l)
        if isinstance(index, slice):
            if index.step < 0:
                end = index.start
            else:
                end = index.stop
        else:
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
