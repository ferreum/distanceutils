""".bytes file reading and writing primitives."""


import struct
from struct import Struct
from contextlib import contextmanager

from .printing import PrintContext, format_unknown, format_transform
from .argtaker import ArgTaker


S_COLOR_RGBA = Struct("4f")

S_FLOAT = Struct("f")
S_DOUBLE = Struct("d")

S_FLOAT3 = Struct("fff")
S_FLOAT4 = Struct("ffff")

SKIP_BYTES = b'\xFD\xFF\xFF\x7F'

"""Level container"""
MAGIC_9 = 99999999

"""Container for most objects"""
MAGIC_6 = 66666666

"""Level layer container"""
MAGIC_7 = 77777777

"""Levelinfo found in some v1 levels"""
MAGIC_8 = 88888888

"""Subobject list container"""
MAGIC_5 = 55555555

"""Data container"""
MAGIC_3 = 33333333

"""Data container"""
MAGIC_2 = 22222222

"""Used for some properties"""
MAGIC_1 = 11111111

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

    def read(self, dbytes, start_section=None,
             start_pos=None, **kw):

        """Read data of this object from the given dbytes.

        Subclasses need to implement self._read() for this to work.
        Subclasses should never override self.read().

        Exceptions raised in self._read() gain the following attributes:

        start_pos - dbytes.pos before starting self._read(), or parameter
                    start_pos, if set.
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
        if start_pos is None:
            start_pos = dbytes.pos
        self.start_pos = start_pos
        self.dbytes = dbytes
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
        return False

    def _write_sections(self, dbytes):
        for sec in self.sections:
            with dbytes.write_section(sec):
                if not self._write_section_data(dbytes, sec):
                    data = sec.raw_data
                    if data is None:
                        raise ValueError(
                            f"Raw data not available for {sec}")
                    dbytes.write_bytes(data)

    def _write_section_data(self, dbytes, sec):
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
        if 'sections' in p.flags and self.sections:
            if self.start_section is not None:
                p(f"Container:")
                with p.tree_children():
                    p.print_data_of(self.start_section)
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
            value = self.dbytes.read_n(nbytes, or_to_eof=or_to_eof)
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
        if magic in (MAGIC_3, MAGIC_2):
            self.ident = arg(1, 'ident')
            self.version = arg(2, 'version')
        elif magic == MAGIC_6:
            self.type = arg(1, 'type')
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
        if magic == MAGIC_6:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.type = dbytes.read_str()
            self._add_unknown(1) # unknown, always 0
            dbytes.read_n(4) # secnum
            self.num_sections = dbytes.read_int(4)
        elif magic == MAGIC_5:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.num_objects = dbytes.read_int(4)
            self.children_start = dbytes.pos
        elif magic == MAGIC_3:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.ident = dbytes.read_int(4)
            self.version = dbytes.read_int(4)
            dbytes.read_n(4) # secnum
        elif magic == MAGIC_2:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.ident = dbytes.read_int(4)
            self.version = dbytes.read_int(4)
            dbytes.read_n(4) # secnum
        elif magic == MAGIC_7:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.layer_name = dbytes.read_str()
            self.num_objects = dbytes.read_int(4)
        elif magic == MAGIC_9:
            self.data_size = dbytes.read_int(8)
            self.level_name = dbytes.read_str()
            self.num_layers = dbytes.read_int(4)
            dbytes.read_n(4) # secnum
        elif magic == MAGIC_8:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
        elif magic == MAGIC_32:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
        else:
            raise IOError(f"unknown section: {magic} (0x{magic:08x})")

    def read_raw_data(self, dbytes):
        self.raw_data = dbytes.read_n(self.data_end - dbytes.pos)

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
        if magic in (MAGIC_3, MAGIC_2):
            with dbytes.write_size():
                dbytes.write_int(4, self.ident)
                dbytes.write_int(4, self.version)
                dbytes.write_secnum()
                yield
        elif magic == MAGIC_6:
            with dbytes.write_size():
                dbytes.write_str(self.type)
                dbytes.write_bytes(b'\x00') # unknown, always 0
                dbytes.write_secnum()
                with dbytes.write_num_subsections():
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
        p(f"Section: {self.magic}{type_str}")

    def _print_offset(self, p):
        start = self.data_start
        end = self.data_end
        if start is not None and end is not None:
            p(f"Data offset: 0x{start:08x} to 0x{end:08x} (0x{end - start:x} bytes)")


TRANSFORM_MIN_SIZE = 12


def read_transform(dbytes):
    def read_float():
        return dbytes.read_struct(S_FLOAT)[0]
    f = dbytes.read_n(4)
    if f == SKIP_BYTES:
        pos = ()
    else:
        pos = (S_FLOAT.unpack(f)[0], read_float(), read_float())
    f = dbytes.read_n(4)
    if f == SKIP_BYTES:
        rot = ()
    else:
        rot = (S_FLOAT.unpack(f)[0], read_float(), read_float(), read_float())
    f = dbytes.read_n(4)
    if f == SKIP_BYTES:
        scale = ()
    else:
        scale = (S_FLOAT.unpack(f)[0], read_float(), read_float())
    return pos, rot, scale


def write_transform(dbytes, trans):
    if trans is None:
        trans = ()
    if len(trans) > 0 and len(trans[0]):
        pos = trans[0]
        dbytes.write_bytes(S_FLOAT3.pack(*pos))
    else:
        dbytes.write_bytes(SKIP_BYTES)
    if len(trans) > 1 and len(trans[1]):
        rot = trans[1]
        dbytes.write_bytes(S_FLOAT4.pack(*rot))
    else:
        dbytes.write_bytes(SKIP_BYTES)
    if len(trans) > 2 and len(trans[2]):
        scale = trans[2]
        dbytes.write_bytes(S_FLOAT3.pack(*scale))
    else:
        dbytes.write_bytes(SKIP_BYTES)


class SectionObject(BytesModel):

    """Base class of objects represented by a MAGIC_6 section."""

    child_prober = None
    is_object_group = False

    transform = None
    _children = None
    has_children = False
    children_section = None

    default_sections = (
        Section(MAGIC_3, 0x01, 0),
    )

    def _read(self, dbytes):
        ts = self._get_start_section()
        self.type = ts.type
        self._report_end_pos(ts.data_end)
        self._read_sections(ts.data_end)

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_3, 0x01):
            end = sec.data_end
            if dbytes.pos + TRANSFORM_MIN_SIZE < end:
                self.transform = read_transform(dbytes)
            if dbytes.pos + Section.MIN_SIZE < end:
                self.children_section = Section(dbytes)
                self.has_children = True
            return True
        return BytesModel._read_section_data(self, dbytes, sec)

    def write(self, dbytes):
        if self.sections is ():
            self.sections = self._init_sections()
        with dbytes.write_section(MAGIC_6, self.type):
            self._write_sections(dbytes)

    def _init_sections(self):
        return self.default_sections

    def _write_section_data(self, dbytes, sec):
        if sec.match(MAGIC_3, 0x01):
            transform = self.transform
            children = self.children
            has_children = self.has_children or children
            if self.transform or has_children:
                write_transform(dbytes, self.transform)
            if self.has_children or self.children:
                dbytes.write_int(4, MAGIC_5)
                with dbytes.write_size():
                    dbytes.write_int(4, len(self.children))
                    for obj in self.children:
                        obj.write(dbytes)
            return True
        return BytesModel._write_section_data(self, dbytes, sec)

    @property
    def children(self):
        objs = self._children
        if objs is None:
            s5 = self.children_section
            if s5 and s5.num_objects:
                self._children = objs = []
                dbytes = self.dbytes
                with dbytes.saved_pos():
                    dbytes.pos = s5.children_start
                    objs = self.child_prober.read_n_maybe(
                        dbytes, s5.num_objects)
                    self._children = objs
            else:
                self._children = objs = ()
        return objs

    @children.setter
    def children(self, objs):
        self._children = objs

    def iter_children(self, ty=None, name=None):
        for obj in self.children:
            if ty is None or isinstance(obj, ty):
                if name is None or obj.type == name:
                    yield obj

    def _print_data(self, p):
        if 'transform' in p.flags:
            p(f"Transform: {format_transform(self.transform)}")

    def _print_children(self, p):
        if self.children:
            num = len(self.children)
            p(f"Children: {num}")
            with p.tree_children():
                for obj in self.children:
                    p.tree_next_child()
                    p.print_data_of(obj)


class DstBytes(object):

    """File wrapper providing methods for reading and writing common data
    types used in .bytes files.

    """

    _max_pos = None
    _expect_overread = False
    section_counter = 0
    num_subsections = 0

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

    def read_n(self, n, or_to_eof=False):
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
        return self.read_n(1)[0]

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
        data = self.read_n(length)
        return int.from_bytes(data, 'little', signed=signed)

    def read_struct(self, st):
        if isinstance(st, str):
            st = struct.Struct(st)
        data = self.read_n(st.size)
        return st.unpack(data)

    def read_str(self):
        length = self.read_var_int()
        data = self.read_n(length)
        return data.decode('utf-16', 'surrogateescape')

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

    def write_secnum(self):
        n = self.section_counter
        n += 1
        self.section_counter = n
        self.write_int(4, n)

    @contextmanager
    def write_size(self):
        start = self.pos
        self.write_bytes(b'\x00' * 8)
        try:
            yield
        finally:
            end = self.pos
            try:
                self.pos = start
                self.write_int(8, end - start - 8)
            finally:
                self.pos = end

    @contextmanager
    def write_num_subsections(self):
        start = self.pos
        self.write_bytes(b'\x00' * 4)
        try:
            yield
        finally:
            end = self.pos
            try:
                self.pos = start
                self.write_int(4, self.num_subsections)
            finally:
                self.pos = end

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
    def saved_pos(self):
        old_pos = self.pos
        try:
            yield
        finally:
            self.pos = old_pos


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
