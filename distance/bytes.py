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


class BytesModel(object):

    """Base object representing a set amount of data in .bytes files."""

    unknown = ()
    sections = ()
    exception = None
    reported_end_pos = None
    recoverable = False
    start_section = None
    sane_end_pos = False
    opts = None

    default_sections = ()

    @classmethod
    def maybe(clazz, dbytes, **kw):

        """Read an object as far as possible.

        If an error occurs, return the partially read object.
        The exception is stored in the object's `exception` attribute."""

        obj = clazz()
        try:
            obj.read(dbytes, **kw)
        except Exception as e:
            obj.exception = e
        return obj

    @classmethod
    def iter_n_maybe(clazz, dbytes, n, **kw):
        for _ in range(n):
            obj = clazz.maybe(dbytes, **kw)
            yield obj
            if not obj.sane_end_pos:
                break

    @classmethod
    def iter_maybe(clazz, dbytes, max_pos=None, **kw):
        while max_pos is None or dbytes.pos < max_pos:
            obj = clazz.maybe(dbytes, **kw)
            yield obj
            if not obj.sane_end_pos:
                break

    @classmethod
    def read_n_maybe(clazz, *args, **kw):
        objs = []
        for obj in clazz.iter_n_maybe(*args, **kw):
            objs.append(obj)
        return objs

    @classmethod
    def lazy_n_maybe(clazz, dbytes, n, *args, start_pos=None, **kw):
        gen = clazz.iter_n_maybe(dbytes, n, *args, **kw)
        return LazySequence(dbytes.stable_iter(gen, start_pos=start_pos), n)

    def __init__(self, dbytes=None, **kw):

        """Constructor.

        If dbytes is set, also call self.read() with the given dbytes and all
        optional **kw parameters.

        If dbytes is unset or None, set the given **kw parameters as
        attributes on the new object.

        """

        if dbytes is not None:
            self.read(dbytes, **kw)
        elif kw:
            for k, v in kw.items():
                setattr(self, k, v)

    def _handle_opts(self, opts):
        pass

    def read(self, dbytes, start_section=None, opts=None, **kw):

        """Read data of this object from the given dbytes.

        Subclasses need to implement self._read() for this to work.
        Subclasses should never override self.read().

        Exceptions raised in self._read() gain the following attributes:

        start_pos - dbytes.pos when entering this method, or start_pos of
                    parameter start_section, if set.
        exc_pos   - dbytes.pos where the exception occurred.
        sane_end_pos - Whether dbytes.pos is considered sane (see below).
        partial_object - Set to self only if self.recoverable is set to true.

        EOFError occuring in self._read() are converted to
        UnexpectedEOFError if any data has been read from dbytes.

        After _read(), regardless of whether an exception was raised,
        it is attempted to set dbytes.pos to the position reported
        (if it was) with _report_end_pos(). If this is successful,
        the dbytes.pos is considered sane.

        """

        if start_section:
            self.start_section = start_section
            start_pos = start_section.start_pos
        else:
            start_pos = dbytes.pos
        self.start_pos = start_pos
        self.dbytes = dbytes
        if opts:
            self.opts = opts
            self._handle_opts(opts)
        try:
            self._read(dbytes, **kw)
            self.__apply_end_pos(dbytes)
            self.end_pos = dbytes.pos
            self.sane_end_pos = True
        except Exception as e:
            orig_e = e
            exc_pos = dbytes.pos
            if exc_pos != start_pos and isinstance(e, EOFError):
                e = UnexpectedEOFError()
            e.args += (('start_pos', start_pos), ('exc_pos', exc_pos))
            e.start_pos = start_pos
            e.exc_pos = exc_pos
            if self.recoverable:
                e.partial_object = self
                self.exception = e
            else:
                try:
                    # delete attr set for inner recoverable object
                    del e.partial_object
                except AttributeError:
                    pass
            self.sane_end_pos = self.__apply_end_pos(dbytes, or_to_eof=True)
            self.end_pos = dbytes.pos
            raise e from orig_e

    def _read(self, dbytes):
        raise NotImplementedError(
            "Subclass needs to override _read(self, dbytes)")

    def _read_sections(self, end):
        dbytes = self.dbytes
        sections = self.sections
        if sections is ():
            self.sections = sections = []
        with dbytes.limit(end):
            while dbytes.pos < end:
                sec = Section(dbytes)
                sections.append(sec)
                with dbytes.limit(sec.data_end):
                    prevpos = dbytes.pos
                    if not self._read_section_data(dbytes, sec):
                        dbytes.pos = prevpos
                        sec.read_raw_data(dbytes)
                dbytes.pos = sec.data_end

    def _read_section_data(self, dbytes, sec):

        """Reads the data of the given section.

        Returns `True` if the raw section data is not needed.

        Returns `False` to indicate that raw data of the section
        shall be saved (e.g. for _write_section_data).

        """

        return False

    def _write_sections(self, dbytes):
        for sec in self.sections:
            self._write_section(dbytes, sec)

    def _write_section(self, dbytes, sec):
        with dbytes.write_section(sec):
            if not self._write_section_data(dbytes, sec):
                data = sec.raw_data
                if data is None:
                    raise ValueError(
                        f"Raw data not available for {sec}")
                dbytes.write_bytes(data)

    def _write_section_data(self, dbytes, sec):

        """Write the data of the given section.

        Returns `True` if the section has been written.

        Returns `False` if the raw section data shall be copied
        from the source that this object has been read from. This
        is an error if raw data has not been saved for the section
        (e.g. by returning False from _read_section_data).

        """

        return False

    def _report_end_pos(self, pos):
        self.recoverable = True
        self.reported_end_pos = pos

    def __apply_end_pos(self, dbytes, or_to_eof=False):
        end_pos = self.reported_end_pos
        if end_pos is not None:
            current_pos = dbytes.pos
            if current_pos == end_pos:
                return True
            if current_pos > end_pos:
                dbytes.pos = end_pos
                return True
            wanted = end_pos - current_pos
            remain = self._add_unknown(wanted, or_to_eof=or_to_eof)
            return len(remain) == wanted
        return False

    def write(self, dbytes):

        """Writes this object to the given dbytes.

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
        if 'offset' in p.flags:
            self._print_offset(p)
        if 'sections' in p.flags:
            if self.start_section is not None:
                p(f"Container:")
                with p.tree_children():
                    p.print_data_of(self.start_section)
            if self.sections:
                p(f"Subections: {len(self.sections)}")
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
        start_sec = self.start_section
        if start_sec and start_sec.magic == MAGIC_6:
            type_str = start_sec.type
            p(f"Object type: {type_str!r}")

    def _print_offset(self, p):
        start = self.start_pos
        end = self.end_pos
        p(f"Data offset: 0x{start:08x} to 0x{end:08x} (0x{end - start:x} bytes)")

    def _print_data(self, p):
        pass

    def _print_children(self, p):
        pass

    def _get_start_section(self):
        sec = self.start_section
        if not sec:
            self.start_section = sec = Section(self.dbytes)
        return sec

    def _require_type(self, expect):
        ts = self._get_start_section()
        if not ts:
            raise IOError("Missing type information")
        if isinstance(expect, str):
            if ts.type != expect:
                raise IOError(f"Invalid object type: {ts.type}")
        else:
            if not expect(ts.type):
                raise IOError(f"Invalid object type: {ts.type}")
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
            raise IOError(f"Unexpected data: {value!r}")


class Section(BytesModel):

    MIN_SIZE = 12 # 4b (magic) + 8b (data_size)

    layer_name = None
    level_name = None
    num_objects = None
    layer_flags = ()
    data_start = None
    data_size = None
    type = None
    ident = None
    version = None
    num_sections = None
    raw_data = None
    id = None

    def __init__(self, *args, **kw):
        if args:
            first = args[0]
            if not isinstance(first, int):
                self.read(*args, **kw)
                return
        if args or kw:
            self._init_from_args(*args, **kw)

    def _init_from_args(self, *args, **kw):
        arg = ArgTaker(*args, **kw)

        self.magic = magic = arg(0, 'magic')
        if magic in (MAGIC_2, MAGIC_3):
            self.ident = arg(1, 'ident')
            self.version = arg(2, 'version')
            self.id = arg(3, 'id', default=None)
        elif magic == MAGIC_5:
            pass # no data
        elif magic == MAGIC_6:
            self.type = arg(1, 'type')
            self.id = arg(2, 'id', default=None)
        elif magic == MAGIC_7:
            self.layer_name = arg(1, 'layer_name')
            self.num_objects = arg(2, 'num_objects')
        elif magic == MAGIC_9:
            self.level_name = arg(1, 'level_name')
            self.num_layers = arg(2, 'num_layers')
            self.version = arg(3, 'version', default=3)
        else:
            raise ValueError(f"invalid magic: {magic} (0x{magic:08x})")

        arg.verify()

    def __repr__(self):
        magic = self.magic
        argstr = str(magic)
        if magic in (MAGIC_2, MAGIC_3):
            argstr += f", ident=0x{self.ident:x}, version={self.version}"
        elif magic == MAGIC_6:
            argstr += f", {self.type!r}"
        return f"Section({argstr})"

    def _read(self, dbytes):
        self.magic = magic = dbytes.read_int(4)
        self.recoverable = True
        if magic == MAGIC_2:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.ident = dbytes.read_int(4)
            self.version = dbytes.read_int(4)
            self.id = dbytes.read_id()
        elif magic == MAGIC_3:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.ident = dbytes.read_int(4)
            self.version = dbytes.read_int(4)
            self.id = dbytes.read_id()
        elif magic == MAGIC_5:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.num_objects = dbytes.read_int(4)
            self.children_start = dbytes.pos
        elif magic == MAGIC_6:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.type = dbytes.read_str()
            self._add_unknown(1) # unknown, always 0
            self.id = dbytes.read_id()
            self.num_sections = dbytes.read_int(4)
        elif magic == MAGIC_7:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.layer_name = dbytes.read_str()
            self.num_objects = dbytes.read_int(4)
        elif magic == MAGIC_9:
            self.data_size = dbytes.read_int(8)
            self.level_name = dbytes.read_str()
            self.num_layers = dbytes.read_int(4)
            self.version = dbytes.read_int(4)
        elif magic == MAGIC_8:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
        elif magic == MAGIC_32:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
        else:
            raise IOError(f"unknown section: {magic} (0x{magic:08x})")

    def read_raw_data(self, dbytes):
        self.raw_data = dbytes.read_bytes(self.data_end - dbytes.pos,
                                          or_to_eof=True)

    def match(self, magic, ident=None, version=None):
        if magic != self.magic:
            return False
        if ident is not None and ident != self.ident:
            return False
        if version is not None and version != self.version:
            return False
        return True

    @contextmanager
    def write_header(self, dbytes):
        magic = self.magic
        dbytes.write_int(4, magic)
        if magic in (MAGIC_2, MAGIC_3):
            with dbytes.write_size():
                dbytes.write_int(4, self.ident)
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
        if self.ident is not None:
            type_str += f" type 0x{self.ident:02x}"
        if self.version is not None:
            type_str += f" ver {self.version}"
        if self.id is not None:
            type_str += f" id {self.id}"
        p(f"Section: {self.magic}{type_str}")

    def _print_offset(self, p):
        start = self.data_start
        end = self.data_end
        if start is not None and end is not None:
            p(f"Data offset: 0x{start:08x} to 0x{end:08x} (0x{end - start:x} bytes)")


class DstBytes(object):

    """File wrapper providing methods for reading and writing common data
    types used in .bytes files.

    """

    _max_pos = None
    _expect_overread = False
    num_subsections = 0
    section_counter = 0x10000000

    def __init__(self, file):
        self.file = file

    @property
    def pos(self):
        return self.file.tell()

    @pos.setter
    def pos(self, newpos):
        self.file.seek(newpos)

    @contextmanager
    def limit(self, max_pos, expect_overread=False):
        old_max = self._max_pos
        if old_max is not None and max_pos > old_max:
            raise IOError("cannot extend max_pos")
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
        if n == 0:
            return b''
        if n < 0:
            raise ValueError("n must be positive")
        max_pos = self._max_pos
        if max_pos is not None and self.pos + n > max_pos:
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
        if start_pos is None:
            start_pos = self.pos
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
                    pos = self.pos
                yield obj
        return gen()

    @contextmanager
    def write_size(self):
        start = self.pos
        self.write_bytes(b'\x00' * 8)
        try:
            yield
        finally:
            end = self.pos
            with self.saved_pos(start):
                self.write_int(8, end - start - 8)

    @contextmanager
    def write_num_subsections(self):
        start = self.pos
        self.write_bytes(b'\x00' * 4)
        try:
            yield
        finally:
            with self.saved_pos(start):
                self.write_int(4, self.num_subsections)

    @contextmanager
    def write_section(self, *args, **kw):
        # add this section and save the counter
        old_count = self.num_subsections + 1
        self.num_subsections = 0
        try:
            if args and not isinstance(args[0], int):
                sec = args[0]
            else:
                sec = Section(*args, **kw)
            with sec.write_header(self):
                yield
        finally:
            self.num_subsections = old_count

    @contextmanager
    def saved_pos(self, set_to=None):
        old_pos = self.pos
        if set_to is not None:
            self.pos = set_to
        try:
            yield
        finally:
            self.pos = old_pos


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
