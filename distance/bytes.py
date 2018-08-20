""".bytes file reading and writing primitives."""


import sys
from io import BytesIO
from struct import Struct
from contextlib import contextmanager
from collections import namedtuple

from .printing import PrintContext
from ._argtaker import ArgTaker
from .lazy import LazySequence
from trampoline import trampoline

import codecs

UTF_16_DECODE = codecs.getdecoder('utf-16-le')
UTF_16_ENCODE = codecs.getencoder('utf-16-le')

S_COLOR_RGBA = Struct("<4f")

S_FLOAT = Struct("<f")
S_DOUBLE = Struct("<d")

S_FLOAT3 = Struct("<fff")
S_FLOAT4 = Struct("<ffff")

S_BYTE = Struct('b')
S_INT = Struct('<i')
S_LONG = Struct('<q')
S_UINT = Struct('<I')
S_ULONG = Struct('<Q')

S_UINT2 = Struct("<II")
S_UINT3 = Struct("<III")

SKIP_BYTES = b'\xFD\xFF\xFF\x7F'

"""Used for some properties"""
MAGIC_1 = 11111111

"""Data container"""
MAGIC_2 = 22222222

"""Data container"""
MAGIC_3 = 33333333

"""Subobject list container"""
MAGIC_5 = 55555555

"""Container for most objects"""
MAGIC_6 = 66666666

"""Level layer container"""
MAGIC_7 = 77777777

"""Levelinfo found in some v1 levels"""
MAGIC_8 = 88888888

"""Level container"""
MAGIC_9 = 99999999

MAGIC_12 = 12121212

MAGIC_32 = 32323232


"""Dict containing all the magics. Easier than importing single magics."""
Magic = {
    1: MAGIC_1,
    2: MAGIC_2,
    3: MAGIC_3,
    5: MAGIC_5,
    6: MAGIC_6,
    7: MAGIC_7,
    8: MAGIC_8,
    9: MAGIC_9,
    12: MAGIC_12,
    32: MAGIC_32,
}


CATCH_EXCEPTIONS = (ValueError, EOFError)


class ErrorPosition(namedtuple('_ErrorPosition', ['start', 'error'])):

    def __repr__(self):
        return f"{type(self).__name__}(start=0x{self.start:x}, error=0x{self.error:x})"

    @classmethod
    def get(cls, ex):
        return [a for a in ex.args if isinstance(a, cls)]

    @classmethod
    def first(cls, ex):
        return cls.get(ex)[0]


class BytesModel(object):

    """Represents a set amount of data in .bytes files."""

    __slots__ = ('exception', 'start_pos', 'end_pos', 'sane_end_pos')

    @classmethod
    def maybe(cls, dbytes, **kw):

        """Read a new instance of this class even if an error occurs.

        The object is read from the current file position of `dbytes` using the
        `read` method.

        If an error occurs, return the partially read object. The exception is
        stored in the object's `exception` attribute.

        Parameters
        ----------
        dbytes : see DstBytes.from_arg
            The source to read from.

        Additional keyword arguments are passed to the new instance's `read`
        method.

        Returns
        -------
        obj : cls
            The newly read object.

        """

        dbytes = DstBytes.from_arg(dbytes)
        obj = cls(plain=True)
        try:
            obj.read(dbytes, **kw)
        except CATCH_EXCEPTIONS as e:
            obj.exception = e
        return obj

    @classmethod
    def iter_n_maybe(cls, dbytes, n, **kw):

        """Create an iterator for reading a given number of instances.

        One instance is read from the current file position on each iteration
        using the `maybe` method. The same exception handling applies.

        The iterator exits after reading `n` objects or if the previous
        instance's `sane_end_pos` is False.

        Parameters
        ----------
        dbytes : see DstBytes.from_arg
            The source to read from.
        n : int
            The number of objects the iterator should read.

        Additional keyword arguments are passed to each new instance's `read`
        method.

        Returns
        -------
        i : iterator
            The created iterator.

        """

        dbytes = DstBytes.from_arg(dbytes)
        for _ in range(n):
            obj = cls.maybe(dbytes, **kw)
            yield obj
            if not obj.sane_end_pos:
                break

    @classmethod
    def lazy_n_maybe(cls, dbytes, n, *, start_pos=None, **kw):

        """Create a lazy sequence of instances from given source.

        Each object is read using the `maybe` method at the end position of the
        previously read instance.

        The returned sequence reads objects only once and only on first access.
        This means errors may occur when accessing elements as with `maybe`.
        See also `distance.lazy.LazySequence`.

        Parameters
        ----------
        dbytes : see DstBytes.from_arg
            The source to read from.
        n : int
            The length of the sequence.
        start_pos : int
            The start position of the first object inside the file. If None,
            the file position of `dbytes` when calling this method is used.

        Additional keyword arguments are passed to each new instance's `read`
        method.

        Returns
        -------
        seq : lazy sequence
            The new sequence of instances.

        """

        if n <= 0:
            return ()
        # stable_iter seeks for us
        kw['seek_end'] = False
        dbytes = DstBytes.from_arg(dbytes)
        gen = cls.iter_n_maybe(dbytes, n, **kw)
        return LazySequence(dbytes.stable_iter(gen, start_pos=start_pos), n)

    def __init__(self, dbytes=None, **kw):

        """Initializer.

        If `dbytes` is set, also call the `read` method with the given `dbytes`
        and all additional keyword arguments.

        If `dbytes` is unset or `None`, set all additional keyword arguments as
        attributes on the new object. Only attributes that exist on the class
        can be set this way.

        Parameters
        ----------
        dbytes : see DstBytes.from_arg
            The source to read from.

        Raises
        ------
        AttributeError
            When trying to set an attribute not existing on the class.

        """

        self.exception = None
        if dbytes is not None:
            self.read(dbytes, **kw)
        else:
            plain = kw.pop('plain', False)
            if not plain:
                self._init_defaults()
            cls = type(self)
            for k, v in kw.items():
                if not hasattr(cls, k):
                    raise AttributeError(
                        f"{cls.__name__!r} object has no attribute {k!r}")
                setattr(self, k, v)
            if not plain:
                self._after_init()

    def read(self, dbytes, *, seek_end=True, **kw):

        """Read data of this object from `dbytes`.

        Subclasses need to implement the `_read` method. Subclasses should
        never override `read`.

        After the `_read` method call, regardless of whether an exception was
        raised, it is attempted to seek `dbytes` to the position reported  by
        the `end_pos` attribute of this object, if it is non-None. If this is
        successful, the `sane_end_pos` attribute of this object is set to True.

        Parameters
        ----------
        dbytes : see DstBytes.from_arg
            Anything accepted by `DstBytes.from_arg()`.
        seek_end : bool
            Whether to seek to the end of the object after reading. Setting to
            False is useful for reading `Section`, which positions it at the
            start of its content. Default: True.

        Additional keyword arguments are passed to the `_read` method.

        Raises
        ------
        Any exception raised by `_read`. These exceptions gain the following
        attributes:

        start_pos : int
            `start_pos` of `container`, if set. Otherwise, the file position of
            `dbytes` when entering this method.
        exc_pos : int
            File position of `dbytes` when the exception occurred.

        """

        dbytes = DstBytes.from_arg(dbytes)
        container = kw.get('container', None)
        if container:
            start_pos = container.start_pos
        else:
            start_pos = dbytes.tell()
        self.start_pos = start_pos
        self.end_pos = None
        self.sane_end_pos = False
        try:
            self._read(dbytes, **kw)
            end = self.end_pos
            if end is None:
                self.end_pos = dbytes.tell()
            elif seek_end:
                dbytes.seek(end - 1)
                dbytes.read_bytes(1)
            self.sane_end_pos = True
            # Catching BaseEsception, because we re-raise everything.
        except BaseException as e:
            exc_pos = dbytes.tell()
            e.args += (ErrorPosition(start_pos, exc_pos),)
            e.start_pos = start_pos
            e.exc_pos = exc_pos
            end = self.end_pos
            if end is None:
                self.end_pos = exc_pos
            elif seek_end and isinstance(e, CATCH_EXCEPTIONS):
                try:
                    dbytes.seek(end - 1)
                    dbytes.read_bytes(1)
                    self.sane_end_pos = True
                except EOFError:
                    pass
            raise e

    def _read(self, dbytes):
        raise NotImplementedError(
            "Subclass needs to override _read(self, dbytes)")

    def _init_defaults(self):
        pass

    def _after_init(self):
        pass

    def write(self, dbytes, **kw):

        """Write this object to `dbytes`.

        Subclasses need to implement `visit_write()` for this to work.

        """

        return trampoline(DstBytes._write_arg(self, dbytes, **kw))

    def visit_write(self, dbytes):
        """Write this object (trampolined).

        Parameters
        ----------
        dbytes : DstBytes
            The DstBytes to write to.

        """

        raise NotImplementedError(
            "Subclass needs to override write(self, dbytes)")

    def __repr__(self):
        return f"<{type(self).__name__}{self._repr_detail()}>"

    def _repr_detail(self):
        try:
            return f" at 0x{self.start_pos:x}"
        except AttributeError:
            return ""

    def print(self, file=None, flags=(), p=None):

        """Print this object.

        Parameters
        ----------
        file : writable file
            The file to write to. If None, sys.stdout is used.
        flags : sequence of str
            List of options to customize output.
        p : PrintContext
            The context used to print. Cannot be specified at the same time as
            file or flags.

        A new temporary PrintContext is created from `file` and `flags` if `p`
        is None.

        """

        if p is None:
            if file is None:
                file = sys.stdout
            p = PrintContext(file, flags)
        else:
            if file or flags:
                raise TypeError("p must be the single argument")
        trampoline(self.visit_print(p))

    def visit_print(self, p):
        "Print this object using the given PrintContext (trampolined)."
        self._print_type(p)
        if 'class' in p.flags:
            cls = type(self)
            p(f"Class: <{cls.__module__}.{cls.__name__}>")
        if 'offset' in p.flags or 'size' in p.flags:
            self._print_offset(p)
        yield self._visit_print_data(p)
        yield self._visit_print_children(p)
        if self.exception:
            p(f"Exception occurred:")
            p.print_exception(self.exception)

    def _print_type(self, p):
        pass

    def _print_offset(self, p):
        try:
            start = self.start_pos
            end = self.end_pos
        except AttributeError:
            # we don't have a position
            return
        if 'offset' in p.flags:
            p(f"Data offset: 0x{start:08x} to 0x{end:08x} (0x{end - start:x} bytes)")
        else:
            p(f"Data size: 0x{end - start:x} bytes")

    def _visit_print_data(self, p):
        "Print data of this object (trampolined)."
        return
        yield

    def _visit_print_children(self, p):
        "Print children of this object (trampolined)."
        return
        yield


# section magic (I) + size (Q)
S_SEC_BASE = Struct("<IQ")


class Section(BytesModel):

    __slots__ = ('magic', 'type', 'version', 'id',
                 'content_start', 'content_size',
                 'count', 'name')

    MIN_SIZE = 12 # 4b (magic) + 8b (data_size)

    @classmethod
    def base(cls, *args, **kw):
        return cls(*args, any_version=True, **kw)

    def __init__(self, *args, **kw):
        self.exception = None
        if args:
            if not isinstance(args[0], (int, Section)):
                self.read(*args, **kw)
                return
        if not kw.pop('plain', False):
            self._init_from_args(*args, **kw)
        elif kw or args:
            raise TypeError(f"Invalid arguments: {args!r}, {kw!r}")

    def _init_from_args(self, *args, any_version=False, base=None, **kw):
        if args and isinstance(args[0], Section):
            if base is not None:
                raise TypeError("base cannot be set if first arg is Section")
            base = args[0]
            args = args[1:]
        arg = ArgTaker(*args, **kw)

        if base is not None:
            arg.fallback_object(base)

        self.magic = magic = arg(0, 'magic')
        if magic in (MAGIC_2, MAGIC_3):
            self.type = arg(1, 'type')
            if not any_version:
                self.version = arg(2, 'version')
            else:
                self.version = None
            self.id = arg(3, 'id', default=None)
        elif magic == MAGIC_5:
            pass # no data
        elif magic == MAGIC_6:
            self.type = arg(1, 'type')
            self.id = arg(2, 'id', default=None)
        elif magic == MAGIC_7:
            self.name = arg(1, 'name', default=None)
        elif magic == MAGIC_8:
            pass # no data
        elif magic == MAGIC_9:
            self.name = arg(1, 'name', default=None)
            self.count = arg(2, 'count', default=None)
            self.version = arg(3, 'version', default=3)
        else:
            raise ValueError(f"invalid magic: {magic} (0x{magic:08x})")

        arg.verify()

    def __repr__(self):
        try:
            magic = self.magic
        except AttributeError:
            argstr = "<invalid>"
        else:
            argstr = str(magic)
            if magic in (MAGIC_2, MAGIC_3):
                argstr += f", type=0x{self.type:x}, version={self.version}"
            elif magic == MAGIC_6:
                argstr += f", {self.type!r}"
            elif magic == MAGIC_9:
                argstr += f", name={self.name!r}, count={self.count}, version={self.version}"
        return f"Section({argstr})"

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(repr(key))

    @property
    def content_end(self):
        return self.content_start + self.content_size

    def to_key(self, noversion=False):
        """Create a key of this section's type identity."""
        magic = self.magic
        if magic in (MAGIC_2, MAGIC_3):
            if noversion:
                return (magic, self.type, None)
            else:
                return (magic, self.type, self.version)
        elif magic == MAGIC_6:
            return (magic, self.type)
        else:
            return magic

    @classmethod
    def from_key(cls, key):
        if isinstance(key, tuple):
            return cls(*key)
        else:
            return cls(key)

    def has_version(self):
        return self.magic in (MAGIC_2, MAGIC_3)

    def _read(self, dbytes):
        magic, data_size = dbytes.read_struct(S_SEC_BASE)
        self.magic = magic
        data_start = self.start_pos + 12
        data_end = data_start + data_size
        self.end_pos = data_end

        if magic in (MAGIC_2, MAGIC_3):
            self.type, self.version, self.id = dbytes.read_struct(S_UINT3)
            cstart = data_start + 12
        elif magic == MAGIC_5:
            self.count = dbytes.read_uint4()
            cstart = data_start + 4
        elif magic == MAGIC_6:
            self.type = dbytes.read_str()
            dbytes.read_bytes(1) # unknown, always 0
            self.id, self.count = dbytes.read_struct(S_UINT2)
            cstart = dbytes.tell()
        elif magic == MAGIC_7:
            self.name = dbytes.read_str()
            self.count = dbytes.read_uint4()
            cstart = dbytes.tell()
        elif magic == MAGIC_9:
            self.name = dbytes.read_str()
            self.count, self.version = dbytes.read_struct(S_UINT2)
            cstart = dbytes.tell()
        elif magic in (MAGIC_8, MAGIC_32):
            cstart = data_start
        else:
            raise ValueError(f"unknown section: {magic} (0x{magic:08x})")

        self.content_start = cstart
        self.content_size = data_end - cstart

    @contextmanager
    def _write_header(self, dbytes):
        magic = self.magic
        dbytes.write_int(4, magic)
        if magic in (MAGIC_2, MAGIC_3):
            with dbytes.write_size():
                dbytes.write_int(4, self.type)
                dbytes.write_int(4, self.version)
                dbytes.write_id(getattr(self, 'id', None))
                yield
        elif magic == MAGIC_5:
            with dbytes.write_size():
                with dbytes.write_num_subsections():
                    yield
        elif magic == MAGIC_6:
            with dbytes.write_size():
                dbytes.write_str(self.type)
                dbytes.write_bytes(b'\x00') # unknown, always 0
                dbytes.write_id(getattr(self, 'id', None))
                with dbytes.write_num_subsections():
                    yield
        elif magic == MAGIC_7:
            with dbytes.write_size():
                dbytes.write_str(self.name)
                with dbytes.write_num_subsections():
                    yield
        elif magic == MAGIC_8:
            with dbytes.write_size():
                yield
        elif magic == MAGIC_9:
            with dbytes.write_size():
                dbytes.write_str(self.name)
                dbytes.write_int(4, self.count)
                dbytes.write_int(4, self.version)
                yield
        elif magic == MAGIC_32:
            with dbytes.write_size():
                yield
        else:
            raise NotImplementedError(f"cannot write section {self.magic}")

    def _print_type(self, p):
        type_str = ""
        magic = self.magic
        if magic in (MAGIC_2, MAGIC_3, MAGIC_6):
            if magic == MAGIC_6:
                if self.type is not None:
                    type_str += f" type {self.type!r}"
            else:
                if self.type is not None:
                    type_str += f" type 0x{self.type:02x}"
                if self.version is not None:
                    type_str += f" ver {self.version}"
        try:
            type_str += f" id {self.id}"
        except AttributeError:
            pass
        p(f"Section: {self.magic}{type_str}")

    def _print_offset(self, p):
        try:
            start = self.content_start
            size = self.content_size
        except AttributeError:
            pass # don't have a size
        else:
            if 'offset' in p.flags:
                p(f"Content offset: 0x{start:08x} to 0x{start + size:08x} (0x{size:x} bytes)")
            else:
                p(f"Content size: 0x{size:x} bytes")


class DstBytes(object):

    """File wrapper for reading and writing data of .bytes files.

    Using an instance as context manager saves the current position on enter
    and restores it on exit.

    """

    num_subsections = 0
    section_counter = 0x10000000

    def __init__(self, file):
        self.file = file
        self.tell = file.tell
        self.seek = file.seek
        self._pos_stack = []

    def __repr__(self):
        pos = self.tell()
        if isinstance(self.file, BytesIO):
            fstr = f"<memory size 0x{len(self.file.getbuffer()):x}> "
        else:
            try:
                fstr = f"{self.file.name!r} "
            except AttributeError:
                fstr = ''
        return f"<{type(self).__name__} {fstr}at 0x{pos:x}>"

    @classmethod
    def in_memory(cls):
        """Create an empty in-memory instance."""
        return DstBytes(BytesIO())

    @classmethod
    def from_data(cls, data):
        """Create a new instance for reading the given bytes object."""
        return DstBytes(BytesIO(data))

    @classmethod
    def from_arg(cls, arg):

        """Get a readable instance according to the given argument.

        If `arg` is an instance of this class, it is returned as-is.

        If `arg` is a `str` or `bytes`, it is used as a file name. The file at
        this path is then read completely into a `io.BytesIO`, which is then
        wrapped with a new instance.

        Otherwise, `arg` is assumed to be a binary file, and is wrapped with a
        new instance of this class.

        Returns
        -------
        dbytes : cls
            The instance of this class.

        """

        if isinstance(arg, cls):
            return arg
        if isinstance(arg, (str, bytes)):
            # We open the file and read it completely into memory.
            # This actually speeds up I/O because we perform many small
            # operations which are faster on BytesIO.
            with open(arg, 'rb') as f:
                data = f.read()
            return cls(BytesIO(data))
        arg.read # raises if arg has no read method
        try:
            file_mode = arg.mode
        except AttributeError:
            # If we can't find the mode, assume we're fine.
            # If not, error will occur on first read.
            pass
        else:
            if not 'b' in file_mode:
                raise IOError(f"File needs be opened with 'b' mode.")
        return cls(arg)

    @classmethod
    def _write_arg(cls, obj, arg, write_mode='wb'):
        if isinstance(arg, cls):
            return (yield obj.visit_write(arg))
        if isinstance(arg, (str, bytes)):
            tmpdb = DstBytes.in_memory()
            yield obj.visit_write(tmpdb)
            with open(arg, write_mode) as f:
                return f.write(tmpdb.file.getbuffer())
        try:
            file_mode = arg.mode
        except AttributeError:
            pass
        else:
            if not 'b' in file_mode:
                raise IOError(f"File needs to be opened with 'b' mode.")
        tmpdb = DstBytes.in_memory()
        yield obj.visit_write(tmpdb)
        return arg.write(tmpdb.file.getbuffer())

    def __enter__(self):
        """Save the position on enter and restore it on exit."""
        self._pos_stack.append(self.tell())

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.seek(self._pos_stack.pop(-1))
        return False

    def read_bytes(self, n):

        """Read the given number of bytes.

        Parameters
        ----------
        n : int
            The number of bytes to read.

        Raises
        ------
        EOFError
            If less than the given number of bytes could be read.
        ValueError
            If `n` is negative.

        """

        if n < 0:
            raise ValueError("n must be positive")
        result = self.file.read(n)
        if len(result) != n:
            raise EOFError
        return result

    def read_byte(self):
        return self.read_bytes(1)[0]

    def read_var_int(self):
        n = 0
        bits = 0
        while True:
            b = self.read_byte()
            if b & 0x80:
                n |= (b & 0x7f) << bits
                bits += 7
            else:
                return n | (b << bits)

    def read_int(self, length, signed=False):
        data = self.read_bytes(length)
        return int.from_bytes(data, 'little', signed=signed)

    # faster variants for common ints
    def read_int4(self):
        return S_INT.unpack(self.read_bytes(4))[0]

    def read_int8(self):
        return S_LONG.unpack(self.read_bytes(8))[0]

    def read_uint4(self):
        return S_UINT.unpack(self.read_bytes(4))[0]

    def read_uint8(self):
        return S_ULONG.unpack(self.read_bytes(8))[0]

    def read_struct(self, st):
        data = self.read_bytes(st.size)
        return st.unpack(data)

    def read_str(self):
        length = self.read_var_int()
        data = self.read_bytes(length)
        return UTF_16_DECODE(data, 'surrogateescape')[0]

    def read_id(self):
        return self.read_uint4()

    def write_bytes(self, data):
        """Write the given bytes."""
        self.file.write(data)

    def write_int(self, length, value, signed=False):
        self.write_bytes(value.to_bytes(length, 'little', signed=signed))

    def write_var_int(self, value):
        l = []
        while value >= 0x80:
            l.append((value & 0x7f) | 0x80)
            value >>= 7
        l.append(value)
        self.write_bytes(bytes(l))

    def require_equal_uint4(self, expect):
        value = self.read_uint4()
        if value != expect:
            raise ValueError(f"Unexpected data: {value!r}")

    def write_str(self, s):
        data = UTF_16_ENCODE(s, 'surrogateescape')[0]
        self.write_var_int(len(data))
        self.write_bytes(data)

    def write_id(self, id_):
        if id_ is None:
            id_ = self.section_counter + 1
            self.section_counter = id_
        self.write_int(4, id_)

    def stable_iter(self, source, *, start_pos=None):

        """Wrap the BytesModel-yielding `source` for safe iteration.

        The returned iterator seeks to `end_pos` of the previous object on
        every iteration, before invoking the wrapped iterator.

        The returned iterator exits if `source` exits, or if the previous
        object's `sane_end_pos` attribute is False.

        Parameters
        ----------
        source : iterator
            The iterator to wrap.
        start_pos : int
            The file position to read the first object from. If `None`, the
            current position when calling this method is used. If it is
            callable, it is called on the first iteration without arguments and
            the result is used as the starting position.

        Returns
        -------
        i : iterator
            Iterator that yields the objects yielded by `source`.

        """

        if start_pos is None:
            start_pos = self.tell()
        def gen():
            iterator = iter(source)
            if callable(start_pos):
                pos = start_pos()
            else:
                pos = start_pos
            while True:
                self.seek(pos)
                try:
                    obj = next(iterator)
                except StopIteration:
                    break
                yield obj
                if not obj.sane_end_pos:
                    break
                pos = obj.end_pos
        return gen()

    @contextmanager
    def write_size(self):
        """Write the size of the data written inside this context."""
        start = self.tell()
        self.write_bytes(b'\x00' * 8)
        try:
            yield
        finally:
            end = self.tell()
            with self:
                self.seek(start)
                self.write_int(8, end - start - 8)

    @contextmanager
    def write_num_subsections(self):

        """Write the number of sections written inside this context.

        Only sections written using the `write_section` method are counted.

        """

        start = self.tell()
        self.write_bytes(b'\x00' * 4)
        try:
            yield
        finally:
            with self:
                self.seek(start)
                self.write_int(4, self.num_subsections)

    @contextmanager
    def write_section(self, *args, **kw):

        """Write the given section.

        Section data is written inside this context.

        Parameters
        ----------
        Either a single argument containing a `Section` to be written or any
        arguments to be passed to `Section()` to specify the section to write.

        """

        # add this section and save the counter
        old_count = self.num_subsections + 1
        self.num_subsections = 0
        try:
            if args and not isinstance(args[0], int):
                sec = args[0]
            else:
                sec = Section(*args, **kw)
            with sec._write_header(self):
                yield sec
        finally:
            self.num_subsections = old_count


# vim:set sw=4 ts=8 sts=4 et:
