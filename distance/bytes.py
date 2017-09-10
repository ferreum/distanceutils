# File:        bytes.py
# Description: bytes
# Created:     2017-06-24


import struct
from struct import Struct
from contextlib import contextmanager

from .printing import PrintContext
from .common import format_unknown


S_COLOR_RGBA = Struct("4f")

S_FLOAT = Struct("f")
S_DOUBLE = Struct("d")

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

    @classmethod
    def maybe(clazz, *args, **kw):
        try:
            return clazz(*args, **kw), True, None
        except Exception as e:
            try:
                obj = e.partial_object
            except AttributeError:
                raise e
            else:
                return obj, obj.sane_end_pos, e

    @classmethod
    def iter_maybe(clazz, dbytes, *args, max_pos=None, **kw):
        try:
            while max_pos is None or dbytes.pos < max_pos:
                yield clazz.maybe(dbytes, *args, **kw)
        except EOFError:
            pass

    @classmethod
    def read_all_maybe(clazz, *args, **kw):
        entries = []
        try:
            sane = True
            for entry, sane, exc in clazz.iter_maybe(*args, **kw):
                entries.append(entry)
                if not sane:
                    break
            return entries, sane, None
        except Exception as e:
            return entries, False, e

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
            self.sections = [start_section]
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
                    self._read_section_data(dbytes, sec)
                dbytes.pos = sec.data_end

    def _read_section_data(self, dbytes, sec):
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
            self.sections = [sec]
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
    num_objects = None
    layer_flags = ()
    data_start = None
    data_size = None
    type = None
    ident = None
    version = None
    num_sections = None

    def _read(self, dbytes):
        self.magic = magic = dbytes.read_int(4)
        self.recoverable = True
        if magic == MAGIC_6:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.type = dbytes.read_str()
            self._add_unknown(1) # unknown, always 0
            dbytes.pos += 4 # secnum
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
            dbytes.pos += 4 # secnum
        elif magic == MAGIC_2:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
            self.ident = dbytes.read_int(4)
            self.version = dbytes.read_int(4)
            dbytes.pos += 4 # secnum
        elif magic == MAGIC_7:
            self.data_size = dbytes.read_int(8)
            self.data_start = data_start = dbytes.pos
            self.layer_name = dbytes.read_str()
            self.num_objects = dbytes.read_int(4)
        elif magic == MAGIC_9:
            self._add_unknown(8)
            self.level_name = dbytes.read_str()
            self._add_unknown(8)
        elif magic == MAGIC_8:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
        elif magic == MAGIC_32:
            self.data_size = dbytes.read_int(8)
            self.data_start = dbytes.pos
        else:
            raise IOError(f"unknown section: {magic} (0x{magic:08x})")

    @staticmethod
    @contextmanager
    def write_header(dbytes, magic, *args, **kw):
        maxarg = -1
        def arg(pos, name):
            nonlocal maxarg
            maxarg = max(maxarg, pos)
            if pos < len(args):
                return args[pos]
            else:
                try:
                    return kw.pop(name)
                except KeyError:
                    raise ValueError(f"missing argument: {name!r}")

        dbytes.write_int(4, magic)
        if magic in (MAGIC_3, MAGIC_2):
            with dbytes.write_size():
                dbytes.write_int(4, arg(0, 'ident'))
                dbytes.write_int(4, arg(1, 'version'))
                dbytes.write_secnum()
                yield
        elif magic == MAGIC_6:
            with dbytes.write_size():
                dbytes.write_str(arg(0, 'type'))
                dbytes.write_bytes(b'\x00') # unknown, always 0
                dbytes.write_secnum()
                with dbytes.write_num_subsections():
                    yield

        if len(args) > maxarg + 1:
            raise ValueError(f"too many arguments (expected {maxarg})")
        if kw:
            raise ValueError(f"invalid kwargs: {kw}")

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
    def write_section(self, magic, *args, **kw):
        # add this section and save the counter
        old_count = self.num_subsections + 1
        self.num_subsections = 0
        try:
            with Section.write_header(self, magic, *args, **kw):
                yield
        finally:
            self.num_subsections = old_count


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
