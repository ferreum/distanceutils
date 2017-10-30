"""Lazy structures."""


from collections import Sequence
from itertools import islice


class BaseLazySequence(Sequence):

    """Base class of lazy sequences.

    Subclasses need to implement `_inflate_slice(start, stop, stride)` and
    `__len__`. Additionally, the backing list needs to be stored in `_list`.

    Subclasses need to implement `_inflate_slice(len_, start, stop, stride)`
    which inflates the given slice in `self._list`. The result is the length
    of the sequence after inflation (like __len__).

    """

    __slots__ = ()

    def __getitem__(self, index):
        len_ = len(self)
        if isinstance(index, slice):
            start, stop, stride = index.indices(len_)
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
            len_ = self._inflate_slice(len_, wantmin, wantmax, abs(stride))
            index = slice(*index.indices(len_))
        else:
            want = index
            if want < 0:
                want += len_
            len_ = self._inflate_slice(len_, want, want + 1, 1)
            if index < 0:
                index += len_
        return self._list[index]


class LazySequence(BaseLazySequence):

    """Lazy sequence using an iterator as source.

    If the iterator stops, the reported length of this sequence is adjusted
    to the number of values yielded up to that point.

    This affects indexing operations, and can result in IndexErrors for ranges
    that are within the length reported before the iterator stopped.

    Conversely, if the iterator yields more values, these values may be
    accessed by iterating this sequence or by indexing beyond the reported
    length.

    """

    __slots__ = ('_iterator', '_len', '_list')

    def __init__(self, source, length):
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

    def __iter__(self):

        """Iterate this sequence.

        May yield more or less values than the reported length of this
        sequence. Iteration is only stopped when the wrapped iterator exits.

        """

        iterator = self._iterator
        l = self._list
        if iterator is None:
            yield from l
            return
        i = 0
        try:
            while True:
                try:
                    yield l[i]
                except IndexError:
                    v = next(iterator)
                    l.append(v)
                    yield v
                i += 1
        except StopIteration:
            # reached the real end of the iterator
            self._iterator = None
            self._len = i

    def _inflate_slice(self, len_, start, stop, stride):
        l = self._list
        current = len(l)
        needed = stop - current
        if needed <= 0:
            return len_
        iterator = self._iterator
        if iterator is None:
            return len_
        if needed == 1:
            # optimize single element inflation
            try:
                l.append(next(iterator))
                return len_
            except StopIteration:
                pass # iterator ended early; fall through
        else:
            l.extend(islice(iterator, needed))
            current = len(l)
            if stop - 1 < current:
                return len_
        # iterator ended earlier than the reported length.
        # Try to patch our length and hope no one notices.
        self._iterator = None
        self._len = current
        return current


UNSET = object()


class LazyMappedSequence(BaseLazySequence):

    """Lazy sequence yielding content of a sequence mapped by a function.

    The function is only called the first time an element is accessed.

    """

    __slots__ = ('_source', '_func', '_list')

    def __init__(self, source, func):
        self._source = source
        self._func = func
        self._list = [UNSET] * len(source)

    def __len__(self):
        return len(self._list)

    def __repr__(self):
        s = ', '.join('…' if i is UNSET else repr(i) for i in self._list)
        return f"<lazy map [{s}]>"

    def __iter__(self):
        l = self._list
        source = self._source
        if source is None:
            yield from l
            return
        func = self._func
        i = 0
        try:
            for v in l:
                if v is UNSET:
                    v = func(source[i])
                    l[i] = v
                yield v
                i += 1
        except IndexError:
            del l[i:]
        # All entries are now inflated.
        self._source = None

    def _inflate_slice(self, len_, start, stop, stride):
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
            return len_
        except IndexError:
            # source decided it's actually shorter.
            newlen = len(self._source)
            del l[newlen:]
            return newlen


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
