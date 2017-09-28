"""Lazy structures."""


from collections import Sequence


class LazySequence(Sequence):

    def __init__(self, source, length):
        self._iterator = iter(source)
        self._length = length
        self._list = []

    def __len__(self):
        return self._length

    def __getitem__(self, index):
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
            end = index
            if end < 0:
                end += mylen
            if end >= mylen:
                raise IndexError(f"{end} >= {mylen}")
            if end < 0:
                raise IndexError(f"{end} < 0")
        l = self._list
        if end >= len(l):
            mylen = self._inflate_index(end)
        if isinstance(index, slice):
            if start < 0:
                start += mylen
            if stop < 0:
                stop += mylen
            index = slice(start, stop, stride)
        else:
            if index < 0:
                index += mylen
        return l[index]

    def __repr__(self):
        l = self._list
        mylen = self._length
        curlen = len(l)
        if curlen != mylen:
            l = self._list
            remaining = mylen - curlen
            return f"<lazy {l!r}{remaining:+}>"
        else:
            return f"<lazy {l!r}>"

    def _inflate_index(self, end):
        """Tries to inflate the given index in the backing list.

        Updates self._length if iterator exits early.
        Returns the new value of self._length.

        """
        iterator = self._iterator
        if iterator is None:
            return self._length
        l = self._list
        current = len(l)
        try:
            for _ in range(end - current + 1):
                l.append(next(iterator))
            return self._length
        except StopIteration:
            # iterator ended earlier than the reported length.
            # Try to patch our length and hope no one notices.
            self._iterator = None
            mylen = len(l)
            self._length = mylen
            return mylen

# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
