""".bytes file reading and writing primitives."""


from struct import Struct
from contextlib import contextmanager

from .printing import PrintContext
from ._argtaker import ArgTaker
from .lazy import LazySequence

import codecs

UTF_16_DECODE = codecs.getdecoder('utf-16-le')
UTF_16_ENCODE = codecs.getencoder('utf-16-le')

S_COLOR_RGBA = Struct("<4f")

S_FLOAT = Struct("<f")
S_DOUBLE = Struct("<d")

S_FLOAT3 = Struct("<fff")
S_FLOAT4 = Struct("<ffff")

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


CATCH_EXCEPTIONS = (ValueError, EOFError)


class BytesModel(object):

    """Represents a set amount of data in .bytes files."""

    __slots__ = ('exception', 'start_pos', 'end_pos', 'sane_end_pos')

    @classmethod
    def maybe(clazz, dbytes, **kw):

        """Read an object as far as possible.

        If an error occurs, return the partially read object. The exception is
        stored in the object's `exception` attribute.

        """

        dbytes = DstBytes.from_arg(dbytes)
        obj = clazz(plain=True)
        try:
            obj.read(dbytes, **kw)
        except CATCH_EXCEPTIONS as e:
            obj.exception = e
        return obj

    @classmethod
    def iter_n_maybe(clazz, dbytes, n, **kw):

        """Create an iterator for reading the given number of objects.

        If an error occurs, yield the partially read object. The exception is
        stored in the object's `exception` attribute. The iterator exits after
        reading `n` objects or if a read object's `sane_end_pos` is False.

        """

        dbytes = DstBytes.from_arg(dbytes)
        for _ in range(n):
            obj = clazz.maybe(dbytes, **kw)
            yield obj
            if not obj.sane_end_pos:
                break

    @classmethod
    def iter_maybe(clazz, dbytes, max_pos=None, **kw):
        """Like `iter_n_maybe()`, but do not limit the number of objects."""
        dbytes = DstBytes.from_arg(dbytes)
        while max_pos is None or dbytes.tell() < max_pos:
            obj = clazz.maybe(dbytes, **kw)
            yield obj
            if not obj.sane_end_pos:
                break

    @classmethod
    def read_n_maybe(clazz, dbytes, *args, **kw):

        """Read a list of objects from `dbytes` as far as possible.

        If an error occurs, return the partially read list. The exception is
        stored in the last object's `exception` attribute.

        """

        dbytes = DstBytes.from_arg(dbytes)
        objs = []
        for obj in clazz.iter_n_maybe(dbytes, *args, **kw):
            objs.append(obj)
        return objs

    @classmethod
    def lazy_n_maybe(clazz, dbytes, n, *args, start_pos=None, **kw):

        """Like `read_n_maybe()`, but create a `LazySequence`.

        The returned sequence reads objects only on first access. This means
        errors may occur when accessing an element. See
        `distance.lazy.LazySequence`.

        """

        if n <= 0:
            return ()
        # stable_iter seeks for us
        kw['seek_end'] = False
        dbytes = DstBytes.from_arg(dbytes)
        gen = clazz.iter_n_maybe(dbytes, n, *args, **kw)
        return LazySequence(dbytes.stable_iter(gen, start_pos=start_pos), n)

    def __init__(self, dbytes=None, **kw):

        """Constructor.

        If `dbytes` is set, also call `self.read()` with the given `dbytes` and
        all optional `**kw` parameters.

        If `dbytes` is unset or `None`, set the given `**kw` parameters as
        attributes on the new object.

        """

        self.exception = None
        if dbytes is not None:
            self.read(dbytes, **kw)
        else:
            plain = kw.pop('plain', False)
            if not plain:
                self._init_defaults()
            for k, v in kw.items():
                setattr(self, k, v)
            if not plain:
                self._after_init()

    def read(self, dbytes, seek_end=True, **kw):

        """Read data of this object from `dbytes`.

        Subclasses need to implement `_read()` for this to work. Subclasses
        should never override `read()`.

        Exceptions raised in `_read()` gain the following attributes:

        `start_pos`      - `start_pos` of `container`, if set. Otherwise,
                           `dbytes` position when entering this method.
        `exc_pos`        - `dbytes` position where the exception occurred.

        After `_read()`, regardless of whether an exception was raised,
        it is attempted to `dbytes.seek()` to the position reported
        (if it was) by setting the `end_pos` attribute. If this is
        successful, the `sane_end_pos` attribute is set to True.

        Arguments:
        `dbytes` - Anything accepted by `DstBytes.from_arg()`.
        `container` - The already read container section. `dbytes` needs to
                      be positioned at the start of this section's content if
                      set. (this argument needs to be supported by the
                      `_read()` implementation)
        `seek_end` - Whether to seek to the end of the object after
                     reading. Mainly useful for reading `Section`, which
                     positions it at the start of its content if False.
                     Default: True.

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
            e.args += (('start_pos', start_pos), ('exc_pos', exc_pos))
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

        Subclasses need to implement _write() for this to work.

        """

        return DstBytes._write_arg(self, dbytes, **kw)

    def _write(self, dbytes):
        raise NotImplementedError(
            "Subclass needs to override write(self, dbytes)")

    def __repr__(self):
        return f"<{type(self).__name__}{self._repr_detail()}>"

    def _repr_detail(self):
        try:
            return f" at 0x{self.start_pos:x}"
        except AttributeError:
            return ""

    def print_data(self, file=None, flags=(), p=None):
        if p is None:
            p = PrintContext(file, flags)
        else:
            if file or flags:
                raise TypeError("p must be the single argument")

        self._print_type(p)
        if 'offset' in p.flags or 'size' in p.flags:
            self._print_offset(p)
        self._print_data(p)
        self._print_children(p)
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

    def _print_data(self, p):
        pass

    def _print_children(self, p):
        pass


# section magic (I) + size (Q)
S_SEC_BASE = Struct("<IQ")


class Section(BytesModel):

    __slots__ = ('magic', 'type', 'version', 'id',
                 'content_start', 'content_size',
                 'count', 'name')

    MIN_SIZE = 12 # 4b (magic) + 8b (data_size)

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

    def _init_from_args(self, *args, any_version=False, **kw):
        if not kw and len(args) == 1 and isinstance(args[0], Section):
            other = args[0]
            if other.magic not in (MAGIC_2, MAGIC_3, MAGIC_32):
                raise TypeError(f"Cannot copy {other}")
            self.magic = other.magic
            self.type = other.type
            self.version = other.version
            return
        arg = ArgTaker(*args, **kw)

        self.magic = magic = arg(0, 'magic')
        if magic in (MAGIC_2, MAGIC_3):
            self.type = arg(1, 'type')
            if not any_version:
                self.version = arg(2, 'version')
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

    def to_key(self, any_version=False):
        """Create a key of this section's type identity."""
        magic = self.magic
        if magic in (MAGIC_2, MAGIC_3):
            if any_version:
                return (magic, self.type)
            else:
                return (magic, self.type, self.version)
        elif magic == MAGIC_6:
            return (magic, self.type)
        else:
            return magic

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

    @classmethod
    def in_memory(cls):
        """Create an empty in-memory instance."""
        from io import BytesIO
        return DstBytes(BytesIO())

    @classmethod
    def from_data(cls, data):
        """Create a new instance for reading the given bytes object."""
        from io import BytesIO
        return DstBytes(BytesIO(data))

    @classmethod
    def from_arg(cls, arg):

        """Get a readable instance according to the given argument.

        If `arg` is an instance of this class, it is returned as-is.

        If `arg` is a `str` or `bytes`, it is used as a file name. The file at
        this path is then read completely into a `io.BytesIO`, which is then
        wrapped with a new instance.

        Otherwise, `arg` is assumed to be a binary file, and is wrapped with a
        new instance.

        """


        if isinstance(arg, cls):
            return arg
        if isinstance(arg, (str, bytes)):
            # We open the file and read it completely into memory.
            # This actually speeds up I/O because we perform many small
            # operations which are faster on BytesIO.
            from io import BytesIO
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
            return obj._write(arg)
        if isinstance(arg, (str, bytes)):
            tmpdb = DstBytes.in_memory()
            obj._write(tmpdb)
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
        obj._write(tmpdb)
        return arg.write(tmpdb.file.getbuffer())

    def __enter__(self):
        """Save the position on enter and restore it on exit."""
        self._pos_stack.append(self.tell())

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.seek(self._pos_stack.pop(-1))
        return False

    def read_bytes(self, n):

        """Read the given number of bytes.

        This is the single method for reading data of the wrapped file. All
        `read_` methods use this method to access data.

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

        """Writes the given bytes.

        This is the single method for writing data to the wrapped file. All
        `write_` methods use this method to write data.

        """

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

    def stable_iter(self, source, start_pos=None):

        """Wrap the BytesModel-yielding `source` for safe iteration.

        The returned iterator seeks to `end_pos` of the previous object before
        every call to `__next__`. If the previous object's `sane_end_pos` is
        False, the returned iterator exits.

        `start_pos` specifies the position before the first iteration. If
        `start_pos` is unset or `None`, the current position when calling this
        method is used. If `start_pos` is callable, it is called without
        arguments and the result is used as the starting position.

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

        Only sections written with `write_section()` are counted.

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

        Section data is written inside this context. Arguments are either a
        single parameter containing a `Section` to be written or arguments to
        be passed to `Section()`.

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


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
