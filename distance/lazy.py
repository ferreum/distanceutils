"""Lazy structures."""


from collections import Sequence


class LazySequence(Sequence):

    def __init__(self, source, length):
        self._iterator = iter(source)
        self._len = length
        self._list = []

    def __len__(self):
        return self._len

    def __getitem__(self, index):
        mylen = self._len
        if isinstance(index, slice):
            start, stop, stride = index.indices(mylen)
            if stride < 0:
                if start <= stop:
                    return []
                last = start
            else:
                if stop <= start:
                    return []
                last = stop - 1
                last -= (mylen - last) % stride
        else:
            last = index
            if last < 0:
                last += mylen
            if last >= mylen:
                raise IndexError(f"{last} >= {mylen}")
            if last < 0:
                raise IndexError(f"{last} < 0")
        mylen = self._inflate_index(last)
        if isinstance(index, slice):
            if start < 0:
                start += mylen
            if stop < 0:
                stop += mylen
            index = slice(start, stop, stride)
        else:
            if index < 0:
                index += mylen
        return self._list[index]

    def __repr__(self):
        l = self._list
        mylen = self._len
        curlen = len(l)
        if curlen != mylen:
            l = self._list
            remaining = mylen - curlen
            return f"<lazy {l!r}{remaining:+}>"
        else:
            return f"<lazy {l!r}>"

    def _inflate_index(self, index):
        """Tries to inflate the given index in the backing list.

        Updates self._len if iterator exits early.
        Returns the new value of self._len.

        """
        iterator = self._iterator
        if iterator is None:
            return self._len
        l = self._list
        try:
            for _ in range(index - len(l) + 1):
                l.append(next(iterator))
            return self._len
        except StopIteration:
            # iterator ended earlier than the reported length.
            # Try to patch our length and hope no one notices.
            self._iterator = None
            mylen = len(l)
            self._len = mylen
            return mylen

# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
