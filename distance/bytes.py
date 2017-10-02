""".bytes file reading and writing primitives."""


import struct
from struct import Struct
from contextlib import contextmanager

from .printing import PrintContext, format_unknown
from .argtaker import ArgTaker
from .lazy import LazySequence


S_COLOR_RGBA = Struct("4f")

S_FLOAT = Struct("f")
S_DOUBLE = Struct("d")

S_FLOAT3 = Struct("fff")
S_FLOAT4 = Struct("ffff")

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


class UnexpectedEOFError(Exception):
    pass


CATCH_EXCEPTIONS = (ValueError, EOFError, UnexpectedEOFError)


class BytesModel(object):

    """Base object representing a set amount of data in .bytes files."""

    unknown = ()
    sections = ()
    exception = None
    _reported_end_pos = None
    container = None
    sane_end_pos = False
    opts = None

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
        stored in the object's `exception` attribute. The iterator exits
        after reading `n` objects or if a read object has non-sane end-pos.

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

        if dbytes is not None:
            self.read(dbytes, **kw)
        else:
            if not kw.pop('plain', False):
                self._init_defaults()
            for k, v in kw.items():
                setattr(self, k, v)

    def _handle_opts(self, opts):
        pass

    def read(self, dbytes, container=None, opts=None, **kw):

        """Read data of this object from `dbytes`.

        Subclasses need to implement `_read()` for this to work. Subclasses
        should never override `read()`.

        Exceptions raised in `_read()` gain the following attributes:

        `start_pos`      - `start_pos` of `container`, if set. Otherwise,
                           `dbytes` position when entering this method.
        `exc_pos`        - `dbytes` position where the exception occurred.

        `EOFError` occuring in `_read()` are converted to
        `UnexpectedEOFError` if any data has been read from `dbytes`.

        After `_read()`, regardless of whether an exception was raised,
        it is attempted to `dbytes.seek()` to the position reported
        (if it was) with `_report_end_pos()`. If this is successful,
        `dbytes` position is considered sane.

        """

        dbytes = DstBytes.from_arg(dbytes)
        if container:
            self.container = container
            start_pos = container.start_pos
        else:
            start_pos = dbytes.tell()
        self.start_pos = start_pos
        self.dbytes = dbytes
        if opts:
            self.opts = opts
            self._handle_opts(opts)
        try:
            self._read(dbytes, **kw)
            self.__apply_end_pos(dbytes)
            self.end_pos = dbytes.tell()
            self.sane_end_pos = True
            # Catching BaseEsception, because we re-raise everything.
        except BaseException as e:
            orig_e = e
            exc_pos = dbytes.tell()
            if exc_pos != start_pos and isinstance(e, EOFError):
                e = UnexpectedEOFError()
            e.args += (('start_pos', start_pos), ('exc_pos', exc_pos))
            e.start_pos = start_pos
            e.exc_pos = exc_pos
            # prevent I/O for non-whitelisted exceptions
            if isinstance(e, CATCH_EXCEPTIONS):
                self.sane_end_pos = self.__apply_end_pos(dbytes, or_to_eof=True)
            self.end_pos = exc_pos
            raise e from orig_e

    def _read(self, dbytes):
        raise NotImplementedError(
            "Subclass needs to override _read(self, dbytes)")

    def _init_defaults(self):
        pass

    def _report_end_pos(self, pos):
        self._reported_end_pos = pos

    def __apply_end_pos(self, dbytes, or_to_eof=False):
        end_pos = self._reported_end_pos
        if end_pos is not None:
            current_pos = dbytes.tell()
            if current_pos == end_pos:
                return True
            if current_pos > end_pos:
                dbytes.seek(end_pos)
                return True
            wanted = end_pos - current_pos
            remain = self._add_unknown(wanted, or_to_eof=or_to_eof)
            return len(remain) == wanted
        return False

    def write(self, dbytes):

        """Write this object to `dbytes`.

        Subclasses need to implement this method.

        """

        raise NotImplementedError(
            "Subclass needs to override write(self, dbytes)")

    def print_data(self, file=None, flags=(), p=None):
        if p is None:
            p = PrintContext(file, flags)
        else:
            if file or flags:
                raise TypeError("p must be the single argument")

        self._print_type(p)
        if 'offset' in p.flags or 'size' in p.flags:
            self._print_offset(p)
        if 'sections' in p.flags:
            if self.container is not None:
                p(f"Container:")
                with p.tree_children():
                    p.print_data_of(self.container)
            if self.sections:
                p(f"Sections: {len(self.sections)}")
                with p.tree_children():
                    for sec in self.sections:
                        p.tree_next_child()
                        p.print_data_of(sec)
        if 'unknown' in p.flags and self.unknown:
            p(f"Unknown: {format_unknown(self.unknown)}")
        self._print_data(p)
        self._print_children(p)
        if self.exception:
            p(f"Exception occurred:")
            p.print_exception(self.exception)

    def _print_type(self, p):
        container = self.container
        if container and container.magic == MAGIC_6:
            type_str = container.type
            p(f"Object type: {type_str!r}")

    def _print_offset(self, p):
        start = self.start_pos
        end = self.end_pos
        if 'offset' in p.flags:
            p(f"Data offset: 0x{start:08x} to 0x{end:08x} (0x{end - start:x} bytes)")
        else:
            p(f"Data size: 0x{end - start:x} bytes")

    def _print_data(self, p):
        pass

    def _print_children(self, p):
        pass

    def _get_container(self):
        sec = self.container
        if not sec:
            self.container = sec = Section(self.dbytes)
        return sec

    def _require_type(self, expect):
        ts = self._get_container()
        if not ts:
            raise ValueError("Missing type information")
        if isinstance(expect, str):
            if ts.type != expect:
                raise ValueError(f"Invalid object type: {ts.type}")
        else:
            if not expect(ts.type):
                raise ValueError(f"Invalid object type: {ts.type}")
        return ts

    def _add_unknown(self, nbytes=None, value=None, or_to_eof=False):
        unknown = self.unknown
        if unknown is ():
            self.unknown = unknown = []
        if value is None:
            value = self.dbytes.read_bytes(nbytes, or_to_eof=or_to_eof)
        unknown.append(value)
        return value

    def _require_equal(self, expect, nbytes=None, value=None):
        if nbytes is not None:
            value = self.dbytes.read_int(nbytes)
        if value != expect:
            raise ValueError(f"Unexpected data: {value!r}")


class Section(BytesModel):

    MIN_SIZE = 12 # 4b (magic) + 8b (data_size)

    layer_name = None
    level_name = None
    num_objects = None
    layer_flags = ()
    data_start = None
    data_size = None
    type = None
    version = None
    num_sections = None
    raw_data = None
    id = None

    @classmethod
    def iter_n_maybe(clazz, dbytes, *args, **kw):
        """Wraps `BytesModel.iter_n_maybe` to enable section iteration."""
        # TODO refactor Section for clean iter
        gen = super().iter_n_maybe(dbytes, *args, **kw)
        for sec in gen:
            yield sec
            dbytes.seek(sec.data_end)

    def __init__(self, *args, **kw):
        if args:
            if not isinstance(args[0], (int, Section)):
                self.read(*args, **kw)
                return
        if not kw.get('plain', False):
            self._init_from_args(*args, **kw)

    def _init_from_args(self, *args, **kw):
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
            self.version = arg(2, 'version')
            self.id = arg(3, 'id', default=None)
        elif magic == MAGIC_5:
            pass # no data
        elif magic == MAGIC_6:
            self.type = arg(1, 'type')
            self.id = arg(2, 'id', default=None)
        elif magic == MAGIC_7:
            self.layer_name = arg(1, 'layer_name', default=None)
            self.num_objects = arg(2, 'num_objects', default=None)
        elif magic == MAGIC_8:
            pass # no data
        elif magic == MAGIC_9:
            self.level_name = arg(1, 'level_name', default=None)
            self.num_layers = arg(2, 'num_layers', default=None)
            self.version = arg(3, 'version', default=3)
        else:
            raise ValueError(f"invalid magic: {magic} (0x{magic:08x})")

        arg.verify()

    def __repr__(self):
        magic = self.magic
        argstr = str(magic)
        if magic in (MAGIC_2, MAGIC_3):
            argstr += f", type=0x{self.type:x}, version={self.version}"
        elif magic == MAGIC_6:
            argstr += f", {self.type!r}"
        return f"Section({argstr})"

    def to_key(self):
        """Create a key of this section's type identity."""
        magic = self.magic
        if magic in (MAGIC_2, MAGIC_3):
            return (magic, self.type, self.version)
        elif magic == MAGIC_6:
            return (magic, self.type)
        else:
            return magic

    def _read(self, dbytes):
        self.magic = magic = dbytes.read_int(4)
        if magic == MAGIC_2:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.tell()
            self.type = dbytes.read_int(4)
            self.version = dbytes.read_int(4)
            self.id = dbytes.read_id()
        elif magic == MAGIC_3:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.tell()
            self.type = dbytes.read_int(4)
            self.version = dbytes.read_int(4)
            self.id = dbytes.read_id()
        elif magic == MAGIC_5:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.tell()
            self.num_objects = dbytes.read_int(4)
            self.children_start = dbytes.tell()
        elif magic == MAGIC_6:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.tell()
            self.type = dbytes.read_str()
            self._add_unknown(1) # unknown, always 0
            self.id = dbytes.read_id()
            self.num_sections = dbytes.read_int(4)
        elif magic == MAGIC_7:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.tell()
            self.layer_name = dbytes.read_str()
            self.num_objects = dbytes.read_int(4)
        elif magic == MAGIC_9:
            self.data_size = dbytes.read_int(8)
            self.level_name = dbytes.read_str()
            self.num_layers = dbytes.read_int(4)
            self.version = dbytes.read_int(4)
        elif magic == MAGIC_8:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.tell()
        elif magic == MAGIC_32:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.tell()
        else:
            raise ValueError(f"unknown section: {magic} (0x{magic:08x})")

    def read_raw_data(self, dbytes):
        """Save this section's raw data in its `raw_data` attribute."""
        self.raw_data = dbytes.read_bytes(self.data_end - dbytes.tell(),
                                          or_to_eof=True)

    def match(self, magic, type=None, version=None):
        """Match the section's type information."""
        if magic != self.magic:
            return False
        if type is not None and type != self.type:
            return False
        if version is not None and version != self.version:
            return False
        return True

    @contextmanager
    def _write_header(self, dbytes):
        magic = self.magic
        dbytes.write_int(4, magic)
        if magic in (MAGIC_2, MAGIC_3):
            with dbytes.write_size():
                dbytes.write_int(4, self.type)
                dbytes.write_int(4, self.version)
                dbytes.write_id(self.id)
                yield
        elif magic == MAGIC_5:
            with dbytes.write_size():
                with dbytes.write_num_subsections():
                    yield
        elif magic == MAGIC_6:
            with dbytes.write_size():
                dbytes.write_str(self.type)
                dbytes.write_bytes(b'\x00') # unknown, always 0
                dbytes.write_id(self.id)
                with dbytes.write_num_subsections():
                    yield
        elif magic == MAGIC_7:
            with dbytes.write_size():
                dbytes.write_str(self.layer_name)
                dbytes.write_int(4, self.num_objects)
                yield
        elif magic == MAGIC_8:
            with dbytes.write_size():
                yield
        elif magic == MAGIC_9:
            with dbytes.write_size():
                dbytes.write_str(self.level_name)
                dbytes.write_int(4, self.num_layers)
                dbytes.write_int(4, self.version)
                yield
        elif magic == MAGIC_32:
            with dbytes.write_size():
                yield
        else:
            raise NotImplementedError(f"cannot write section {self.magic}")

    @property
    def data_end(self):
        start = self.data_start
        size = self.data_size
        if start is None or size is None:
            return None
        return start + size

    def _print_type(self, p):
        type_str = ""
        magic = self.magic
        if magic in (MAGIC_2, MAGIC_3):
            if self.type is not None:
                type_str += f" type 0x{self.type:02x}"
        elif magic == MAGIC_6:
            if self.type is not None:
                type_str += f" type {self.type!r}"
        if self.version is not None:
            type_str += f" ver {self.version}"
        if self.id is not None:
            type_str += f" id {self.id}"
        p(f"Section: {self.magic}{type_str}")

    def _print_offset(self, p):
        start = self.data_start
        end = self.data_end
        if start is not None and end is not None:
            if 'offset' in p.flags:
                p(f"Data offset: 0x{start:08x} to 0x{end:08x} (0x{end - start:x} bytes)")
            else:
                p(f"Data size: 0x{end - start:x} bytes")


class DstBytes(object):

    """File wrapper for reading and writing data of .bytes files."""

    _max_pos = None
    _expect_overread = False
    num_subsections = 0
    section_counter = 0x10000000

    def __init__(self, file):
        self.file = file
        self.tell = file.tell
        self.seek = file.seek

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

    @contextmanager
    def limit(self, max_pos, expect_overread=False):
        """Limit the read position to the given maximum."""
        old_max = self._max_pos
        if old_max is not None and max_pos > old_max:
            raise ValueError("cannot extend max_pos")
        self._expect_overread = expect_overread
        self._max_pos = max_pos
        try:
            yield
        except EOFError:
            if not self._expect_overread:
                raise
        finally:
            self._max_pos = old_max

    def read_bytes(self, n, or_to_eof=False):

        """Read the given number of bytes.

        This is the single method for reading data of the wrapped file. All
        `read_` methods use this method to access data.

        """

        if n == 0:
            return b''
        if n < 0:
            raise ValueError("n must be positive")
        max_pos = self._max_pos
        if max_pos is not None and self.tell() + n > max_pos:
            raise EOFError
        result = self.file.read(n)
        if not or_to_eof and len(result) != n:
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

    def read_struct(self, st):
        if isinstance(st, str):
            st = struct.Struct(st)
        data = self.read_bytes(st.size)
        return st.unpack(data)

    def read_str(self):
        length = self.read_var_int()
        data = self.read_bytes(length)
        return data.decode('utf-16', 'surrogateescape')

    def read_id(self):
        return self.read_int(4)

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

    def write_str(self, s):
        data = s.encode('utf-16-le')
        self.write_var_int(len(data))
        self.write_bytes(data)

    def write_id(self, id_):
        if id_ is None:
            id_ = self.section_counter + 1
            self.section_counter = id_
        self.write_int(4, id_)

    def stable_iter(self, source, start_pos=None):

        """Wrap the `source` for safe iteration using this instance.

        The returned iterator restores the saved position before every call to
        `__next__` and saves it afterwards.

        `start_pos` specifies the position before the first iteration. If
        `start_pos` is unset or `None`, the current position at the time of
        this call is used.

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
                with self.saved_pos(pos):
                    try:
                        obj = next(iterator)
                    except StopIteration:
                        break
                    pos = self.tell()
                yield obj
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
            with self.saved_pos(start):
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
            with self.saved_pos(start):
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
                yield
        finally:
            self.num_subsections = old_count

    @contextmanager
    def saved_pos(self, set_to=None):

        """Save the position on enter and restore it on exit.

        If set and not `None`, set the position to `set_to` on enter.

        """

        old_pos = self.tell()
        if set_to is not None:
            self.seek(set_to)
        try:
            yield
        finally:
            self.seek(old_pos)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
