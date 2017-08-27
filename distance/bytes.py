#!/usr/bin/python
# File:        bytes.py
# Description: bytes
# Created:     2017-06-24


import struct
from struct import Struct
import traceback
from contextlib import contextmanager

from .common import format_unknown


S_COLOR_RGBA = Struct("4f")

S_FLOAT = Struct("f")
S_DOUBLE = Struct("d")

SECTION_LEVEL = 99999999
SECTION_TYPE = 66666666
SECTION_LAYER = 77777777
SECTION_LEVEL_INFO = 88888888
SECTION_5 = 55555555
SECTION_3 = 33333333
SECTION_2 = 22222222
SECTION_1 = 11111111
SECTION_32 = 32323232


LAYER_FLAG_NAMES = ({0: "", 1: "Active"},
                    {0: "", 1: "Frozen"},
                    {0: "Invisible", 1: ""})


def format_flag(gen):
    for flag, names in gen:
        name = names.get(flag, f"Unknown({flag})")
        if name:
            yield name


class UnexpectedEOFError(Exception):
    pass


class PrintContext(object):

    def __init__(self, file, flags):
        self.file = file
        self.flags = flags
        # buffered lines, object finished
        self._tree_data = [], []

    @classmethod
    def for_test(clazz, file=None, flags=()):
        p = PrintContext(file=file, flags=flags)
        def print_exc(e):
            raise e
        p.print_exception = print_exc
        return p

    def __call__(self, text):
        buf, ended = self._tree_data
        if buf:
            last = buf[-1]
            if ended[-1]:
                self.tree_push_up(last, False)
                last.clear()
            last.extend(text.split('\n'))
        else:
            f = self.file
            if f is not None:
                print(text, file=f)

    def tree_push_up(self, lines, last):
        if not lines:
            return
        buf, ended = self._tree_data
        ended[-1] = False
        if len(buf) > 1:
            dest = buf[-2]
            push_line = dest.append
        else:
            f = self.file
            def push_line(line):
                if f is not None:
                    print(line, file=f)
        it = iter(lines)
        if last:
            prefix = "└─ "
        else:
            prefix = "├─ "
        push_line(prefix + next(it))
        if last:
            prefix = "   "
        else:
            prefix = "│  "
        for line in it:
            push_line(prefix + line)

    @contextmanager
    def tree_children(self, num_children):
        buf, ended = self._tree_data
        lines = []
        buf.append(lines)
        ended.append(False)
        try:
            yield
        finally:
            self.tree_push_up(lines, True)
            buf.pop()
            ended.pop()

    def tree_next_child(self):
        buf, ended = self._tree_data
        if buf and buf[-1]:
            ended[-1] = True

    def print_data_of(self, obj):
        obj.print_data(p=self)

    def print_exception(self, exc):
        exc_str = traceback.format_exception(type(exc), exc, exc.__traceback__)
        for part in exc_str:
            if part.endswith('\n'):
                part = part[:-1]
            for line in part.split('\n'):
                self(line)
        try:
            self(f"Exception start: 0x{exc.start_pos:08x}")
            self(f"Exception pos:   0x{exc.exc_pos:08x}")
        except AttributeError:
            pass


class BytesModel(object):

    unknown = ()
    sections = None
    exception = None
    reported_end_pos = None
    recoverable = False

    @classmethod
    def maybe_partial(clazz, *args, **kw):
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
    def iter_maybe_partial(clazz, dbytes, *args, max_pos=None, **kw):
        try:
            while max_pos is None or dbytes.pos < max_pos:
                yield clazz.maybe_partial(dbytes, *args, **kw)
        except EOFError:
            pass

    @classmethod
    def read_all_maybe_partial(clazz, *args, **kw):
        entries = []
        try:
            sane = True
            for entry, sane, exc in clazz.iter_maybe_partial(*args, **kw):
                entries.append(entry)
                if not sane:
                    break
            return entries, sane, None
        except Exception as e:
            return entries, False, e

    def __init__(self, dbytes=None, **kw):
        if dbytes is not None:
            self.read(dbytes, **kw)
        elif kw:
            for k, v in kw.items():
                setattr(self, k, v)

    def read(self, dbytes, start_section=None,
             start_pos=None, **kw):
        self.start_section = start_section
        if start_pos is None:
            start_pos = dbytes.pos
        self.start_pos = start_pos
        self.dbytes = dbytes
        try:
            self._read(dbytes, **kw)
            self.apply_end_pos(dbytes)
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
                self.exception_info = (start_pos, exc_pos)
                self.exception = e
            else:
                try:
                    del e.partial_object
                except AttributeError:
                    pass
            self.sane_end_pos = self.apply_end_pos(dbytes, or_to_eof=True)
            self.end_pos = dbytes.pos
            raise e from orig_e

    def _read(self, dbytes):
        raise NotImplementedError(
            "Subclass needs to override _read(self, dbytes)")

    def _read_sections(self, end):
        dbytes = self.dbytes
        with dbytes.limit(end):
            while dbytes.pos < end:
                sec = Section(dbytes)
                with dbytes.limit(sec.data_end):
                    self._read_section_data(dbytes, sec)
                dbytes.pos = sec.data_end

    def _read_section_data(self, dbytes, sec):
        return False

    def report_end_pos(self, pos):
        self.recoverable = True
        self.reported_end_pos = pos

    def apply_end_pos(self, dbytes, or_to_eof=False):
        end_pos = self.reported_end_pos
        if end_pos is not None:
            current_pos = dbytes.pos
            if current_pos > end_pos:
                dbytes.pos = end_pos
                return True
            if current_pos != end_pos:
                wanted = end_pos - current_pos
                remain = self.add_unknown(wanted, or_to_eof=or_to_eof)
                return len(remain) == wanted
        return False

    def write(self, dbytes):
        raise NotImplementedError(
            "Subclass needs to override write(self, dbytes)")

    def print_data(self, file=None, flags=(), p=None):
        if p is None:
            p = PrintContext(file, flags)
        else:
            if file or flags:
                raise TypeError("p must be the single argument")

        if 'unknown' in p.flags:
            if self.sections is not None:
                for s_list in self.sections.values():
                    for i, s in enumerate(s_list):
                        if s.unknown:
                            p(f"Section {s.ident}-{i} unknown: {format_unknown(s.unknown)}")
            if self.unknown:
                p(f"Unknown: {format_unknown(self.unknown)}")
        if 'offset' in p.flags:
            start = self.start_pos
            end = self.end_pos
            p(f"Data offset: 0x{start:08x} to 0x{end:08x} (0x{end - start:x} bytes)")
        if 'size' in p.flags:
            p(f"Data size: 0x{self.end_pos - self.start_pos:x}")
        self._print_data(p)
        if self.exception:
            p(f"Error when parsing:")
            p.print_exception(self.exception)

    def _print_data(self, p):
        pass

    def get_start_section(self):
        sec = self.start_section
        if not sec:
            self.start_section = sec = Section(self.dbytes)
        return sec

    def require_type(self, expect):
        ts = self.get_start_section()
        if not ts:
            raise IOError("Missing type information")
        if isinstance(expect, str):
            if ts.type != expect:
                raise IOError(f"Invalid object type: {ts.type}")
        else:
            if not expect(ts.type):
                raise IOError(f"Invalid object type: {ts.type}")
        return ts

    def add_unknown(self, nbytes=None, value=None, or_to_eof=False):
        unknown = self.unknown
        if unknown is ():
            self.unknown = unknown = []
        if value is None:
            value = self.dbytes.read_n(nbytes, or_to_eof=or_to_eof)
        unknown.append(value)
        return value

    def require_equal(self, expect, nbytes=None, value=None):
        if nbytes is not None:
            value = self.dbytes.read_num(nbytes)
        if value != expect:
            raise IOError(f"Unexpected data: {value!r}")


class Section(BytesModel):

    MIN_SIZE = 12 # 4b (ident) + 8b (data_size)

    layer_name = None
    num_objects = None
    layer_flags = ()

    def _read(self, dbytes):
        self.ident = ident = dbytes.read_num(4)
        self.recoverable = True
        if ident == SECTION_TYPE:
            self.size = dbytes.read_num(8)
            self.data_start = dbytes.pos
            self.type = dbytes.read_string()
            self.add_unknown(1)
            self.number = dbytes.read_num(4)
            self.version = dbytes.read_num(4)
        elif ident == SECTION_5:
            self.size = dbytes.read_num(8)
            self.data_start = dbytes.pos
            self.num_objects = dbytes.read_num(4)
            self.subobjects_start = dbytes.pos
        elif ident == SECTION_3:
            self.size = dbytes.read_num(8)
            self.data_start = dbytes.pos
            self.value_id = dbytes.read_num(4)
            dbytes.pos += 4 # secnum
            self.number = dbytes.read_num(4)
        elif ident == SECTION_2:
            self.size = dbytes.read_num(8)
            self.data_start = dbytes.pos
            self.value_id = dbytes.read_num(4)
            self.version = dbytes.read_num(4)
            dbytes.pos += 4 # secnum
        elif ident == SECTION_LAYER:
            self.size = size = dbytes.read_num(8)
            self.data_start = data_start = dbytes.pos
            self.layer_name = dbytes.read_string()
            self.num_objects = dbytes.read_num(4)

            pos = dbytes.pos
            if pos + 4 >= data_start + size:
                # Happens with empty old layer sections, this prevents error
                # with empty layer at end of file.
                return
            tmp = dbytes.read_num(4)
            dbytes.pos = pos
            if tmp == 0 or tmp == 1:
                self.add_unknown(4)
                flags = dbytes.read_struct("bbb")
                if tmp == 0:
                    frozen = 1 if flags[0] == 0 else 0
                    self.layer_flags = (flags[1], frozen, flags[2])
                else:
                    self.layer_flags = flags
                    self.add_unknown(1)
            self.objects_start = dbytes.pos
        elif ident == SECTION_LEVEL:
            self.add_unknown(8)
            self.level_name = dbytes.read_string()
            self.add_unknown(8)
        elif ident == SECTION_LEVEL_INFO:
            self.size = dbytes.read_num(8)
            self.data_start = dbytes.pos
        elif ident == SECTION_32:
            self.size = dbytes.read_num(8)
            self.data_start = dbytes.pos
        else:
            raise IOError(f"unknown section: {ident} (0x{ident:08x})")

    @property
    def data_end(self):
        return self.data_start + self.size

    def _print_data(self, p):
        if self.ident == SECTION_LAYER:
            p(f"Layer name: {self.layer_name!r}")
            p(f"Layer object count: {self.num_objects}")
            if self.layer_flags:
                flag_str = ', '.join(
                    format_flag(zip(self.layer_flags, LAYER_FLAG_NAMES)))
                if not flag_str:
                    flag_str = "None"
                p(f"Layer flags: {flag_str}")


class DstBytes(object):

    max_pos = None
    expect_overread = False
    section_counter = 0

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
        old_max = self.max_pos
        if old_max is not None and max_pos > old_max:
            raise IOError("cannot extend max_pos")
        self.expect_overread = expect_overread
        self.max_pos = max_pos
        try:
            yield
        except EOFError:
            if not self.expect_overread:
                raise
        finally:
            self.max_pos = old_max

    def read_n(self, n, or_to_eof=False):
        if n == 0:
            return b''
        if n < 0:
            raise ValueError("n must be positive")
        max_pos = self.max_pos
        if max_pos is not None and self.pos + n > max_pos:
            raise EOFError
        result = self.file.read(n)
        if not or_to_eof and len(result) != n:
            raise EOFError
        return result

    def read_byte(self):
        return self.read_n(1)[0]

    def read_var_num(self):
        n = 0
        bits = 0
        while True:
            b = self.read_byte()
            if b & 0x80:
                n |= (b & 0x7f) << bits
                bits += 7
            else:
                return n | (b << bits)

    def read_num(self, length, signed=False):
        data = self.read_n(length)
        return int.from_bytes(data, 'little', signed=signed)

    def read_struct(self, st):
        if isinstance(st, str):
            st = struct.Struct(st)
        data = self.read_n(st.size)
        return st.unpack(data)

    def read_string(self):
        length = self.read_var_num()
        data = self.read_n(length)
        return data.decode('utf-16', 'surrogateescape')

    def find_long_long(self, number):
        data = struct.pack('q', number)
        return self.find_bytes(data)

    def find_bytes(self, data):
        while True:
            pos = 0
            b = self.read_byte()
            while b == data[pos]:
                pos += 1
                if pos >= len(data):
                    self.pos -= len(data)
                    return
                b = self.read_byte()

    def write_bytes(self, data):
        self.file.write(data)

    def write_num(self, length, value, signed=False):
        self.write_bytes(value.to_bytes(length, 'little', signed=signed))

    def write_var_num(self, value):
        l = []
        while value >= 0x80:
            l.append((value & 0x7f) | 0x80)
            value >>= 7
        l.append(value)
        self.write_bytes(bytes(l))

    def write_str(self, s):
        data = s.encode('utf-16-le')
        self.write_var_num(len(data))
        self.write_bytes(data)

    def write_secnum(self):
        n = self.section_counter
        n += 1
        self.section_counter = n
        self.write_num(4, n)

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
                self.write_num(8, end - start - 8)
            finally:
                self.pos = end


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
