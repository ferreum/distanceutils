"""Lazy structures."""


from collections import Sequence
from itertools import islice


class BaseLazySequence(Sequence):

    """Base class of lazy sequences.

    Subclasses need to implement `_inflate_slice(start, stop, stride)` and
    `__len__`. Additionally, the backing list needs to be stored in `_list`.

    """

    def __getitem__(self, index):
        mylen = len(self)
        if isinstance(index, slice):
            start, stop, stride = index.indices(mylen)
            if stride < 0:
                if start <= stop:
                    return []
                wantmin = stop + 1
                wantmax = start + 1
            else:
                if start >= stop:
                    return []
                wantmin = start
                wantmax = stop
                if stride > 1:
                    wantmax -= (wantmax - 1 - wantmin) % stride
            mylen = self._inflate_slice(wantmin, wantmax, abs(stride))
            index = slice(*index.indices(mylen))
        else:
            want = index
            if want < 0:
                want += mylen
            if want >= mylen:
                raise IndexError(f"{want} >= {mylen}")
            if want < 0:
                raise IndexError(f"{want} < 0")
            mylen = self._inflate_slice(want, want + 1, 1)
            if index < 0:
                index += mylen
        return self._list[index]

    def _inflate_slice(self, start, stop, stride):

        """Try to inflate the given slice in `self._list`.

        Returns the length of this sequence after inflation (like __len__).

        The default implementation raises `NotImplementedError`.

        """

        raise NotImplementedError


class LazySequence(BaseLazySequence):

    """Lazy sequence using an iterator as source."""

    __slots__ = ['_iterator', '_len', '_list']

    def __init__(self, source, length):
        if length <= 0:
            self._len = 0
            return
        self._iterator = iter(source)
        self._len = length
        self._list = []

    def __len__(self):
        return self._len

    def __repr__(self):
        l = self._list
        mylen = self._len
        curlen = len(l)
        if curlen != mylen:
            l = self._list
            remaining = mylen - curlen
            return f"<lazy seq {l!r}{remaining:+}>"
        else:
            return f"<lazy seq {l!r}>"

    def _inflate_slice(self, start, stop, stride):
        iterator = self._iterator
        if iterator is None:
            return self._len
        l = self._list
        current = len(l)
        needed = stop - current
        if needed <= 0:
            return self._len
        if needed == 1:
            # optimize single element inflation
            try:
                l.append(next(iterator))
                return self._len
            except StopIteration:
                pass # iterator ended early; fall through
        else:
            l.extend(islice(iterator, needed))
            current = len(l)
            if stop - 1 < current:
                return self._len
        # iterator ended earlier than the reported length.
        # Try to patch our length and hope no one notices.
        self._iterator = None
        self._len = current
        return current


UNSET = object()


class LazySequenceMapping(BaseLazySequence):

    """Lazy sequence yielding content of a sequence mapped by a function.

    The function is only called the first time an element is accessed.

    """

    __slots__ = ['_source', '_func', '_list']

    def __init__(self, source, func):
        self._source = source
        self._func = func
        self._list = [UNSET] * len(source)

    def __len__(self):
        return len(self._source)

    def __repr__(self):
        s = ', '.join('…' if i is UNSET else repr(i) for i in self._list)
        return f"<lazy map [{s}]>"

    def _inflate_slice(self, start, stop, stride):
        try:
            l = self._list
            if start == stop - 1:
                # optimize single element access
                elem = l[start]
                if elem is UNSET:
                    l[start] = self._func(self._source[start])
            else:
                source = self._source
                func = self._func
                for i in range(start, stop, stride):
                    elem = l[i]
                    if elem is UNSET:
                        l[i] = func(source[i])
        except IndexError:
            # source decided it's actually shorter.
            newlen = len(self._source)
            del l[newlen:]
            return newlen
        return len(l)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
