#!/usr/bin/python
# File:        bytes.py
# Description: bytes
# Created:     2017-06-24


import struct
from struct import Struct
import traceback

from .common import format_unknown


S_COLOR_RGBA = Struct("4f")

S_FLOAT = Struct("f")

SECTION_LEVEL = 99999999
SECTION_TYPE = 66666666
SECTION_LAYER = 77777777
SECTION_LEVEL_INFO = 88888888
SECTION_UNK_3 = 33333333
SECTION_UNK_2 = 22222222
SECTION_UNK_1 = 11111111


class UnexpectedEOFError(Exception):
    pass


def print_exception(exc, file, p):
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=file)
    p(f"Exception start: 0x{exc.start_pos:08x}")
    p(f"Exception pos:   0x{exc.exc_pos:08x}")


class BytesModel(object):

    unknown = ()
    sections = None
    exception = None
    __end_pos = None
    recoverable = False

    @classmethod
    def maybe_partial(clazz, *args, **kw):
        try:
            return clazz(*args, **kw), True, None
        except Exception as e:
            try:
                return e.partial_object, e.sane_final_pos, e
            except AttributeError:
                pass
            raise e

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
            for entry, sane, exc in clazz.iter_maybe_partial(*args, **kw):
                entries.append(entry)
                if not sane:
                    break
            return entries, sane, None
        except Exception as e:
            return entries, False, e

    def __init__(self, dbytes, sections=None, **kw):
        if sections is not None:
            self.sections = sections
        start_pos = dbytes.pos
        self.dbytes = dbytes
        try:
            self.parse(dbytes, **kw)
            self.apply_end_pos(dbytes)
        except Exception as e:
            orig_e = e
            exc_pos = dbytes.pos
            if exc_pos != start_pos and isinstance(e, EOFError):
                e = UnexpectedEOFError().with_traceback(e.__traceback__)
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
            e.sane_final_pos = self.apply_end_pos(dbytes, or_to_eof=True)
            raise e from orig_e

    def parse(self, dbytes):
        raise NotImplementedError(
            "Subclass needs to override parse(self, dbytes)")

    def report_end_pos(self, pos):
        self.recoverable = True
        self.__end_pos = pos

    def apply_end_pos(self, dbytes, or_to_eof=False):
        end_pos = self.__end_pos
        if end_pos is not None:
            current_pos = dbytes.pos
            if current_pos != end_pos:
                remain = self.add_unknown(end_pos - current_pos, or_to_eof=or_to_eof)
                return len(remain) == current_pos
        return False

    def print_data(self, file, flags=()):
        def p(*args, **kwargs):
            print(*args, file=file, **kwargs)
        p.flags = flags
        if 'unknown' in flags:
            if self.sections is not None:
                for s_list in self.sections.values():
                    for i, s in enumerate(s_list):
                        if s.unknown:
                            p(f"Section {s.ident}-{i} unknown: {format_unknown(s.unknown)}")
            if self.unknown:
                p(f"Unknown: {format_unknown(self.unknown)}")
        self._print_data(file, p)
        if self.exception:
            p(f"Error when parsing:")
            print_exception(self.exception, file, p)

    def _print_data(self, file, p):
        pass

    def read_sections_to(self, to, index=None, **kw):
        sections = self.sections
        if sections is None:
            self.sections = sections = {}
        return Section.read_to_map(self.dbytes, to, index=index, dest=sections, **kw)

    def get_section(self, ident, index=0):
        sections = self.sections
        if sections is None:
            return None
        s_list = self.sections.get(ident, ())
        if index <= len(s_list) - 1:
            return s_list[index]
        return None

    def require_type(self, expect):
        ts = self.require_section(SECTION_TYPE)
        if not ts:
            raise IOError("Missing type information")
        if isinstance(expect, str):
            if ts.type != expect:
                raise IOError(f"Invalid object type: {ts.type}")
        else:
            if not expect(ts.type):
                raise IOError(f"Invalid object type: {ts.type}")
        return ts

    def require_section(self, ident, index=0, **kw):
        s = self.get_section(ident, index)
        if s is not None:
            return s
        self.read_sections_to(ident, index, **kw)
        return self.get_section(ident, index)

    def add_unknown(self, nbytes=None, value=None, or_to_eof=False):
        unknown = self.unknown
        if unknown is ():
            self.unknown = unknown = []
        if value is None:
            value = self.dbytes.read_n(nbytes, or_to_eof=or_to_eof)
        unknown.append(value)
        return value


class Section(BytesModel):

    layer_name = None
    num_objects = None
    layer_flags = ()

    layer_flag_names = ({0: "Inactive", 1: "Active"},
                        {0: "Unfrozen", 1: "Frozen"},
                        {0: "Invisible", 1: "Visible"})

    def parse(self, dbytes, shared_info=None):
        self.ident = ident = dbytes.read_fixed_number(4)
        self.recoverable = True
        if ident == SECTION_TYPE:
            self.size = dbytes.read_fixed_number(8)
            self.data_start = dbytes.pos
            self.type = dbytes.read_string()
            self.add_unknown(9)
        elif ident == SECTION_UNK_3:
            self.add_unknown(20)
        elif ident == SECTION_UNK_2:
            self.size = dbytes.read_fixed_number(8)
            self.add_unknown(4)
            self.version = dbytes.read_byte()
            self.add_unknown(3)
        elif ident == SECTION_LAYER:
            self.size = size = dbytes.read_fixed_number(8)
            self.data_start = data_start = dbytes.pos
            self.layer_name = dbytes.read_string()
            self.num_objects = dbytes.read_fixed_number(4)

            pos = dbytes.pos
            if pos + 4 >= data_start + size:
                # Happens with empty old layer sections, this prevents error
                # with empty layer at end of file.
                return
            tmp = dbytes.read_fixed_number(4)
            dbytes.pos = pos
            if tmp == 0 or tmp == 1:
                self.add_unknown(4)
                self.layer_flags = dbytes.read_struct("bbb")
                if tmp == 1:
                    self.add_unknown(1)
        elif ident == SECTION_LEVEL:
            self.add_unknown(8)
            self.level_name = dbytes.read_string()
            self.add_unknown(8)
        elif ident == SECTION_LEVEL_INFO:
            self.size = dbytes.read_fixed_number(8)
            self.data_start = dbytes.pos
        else:
            raise IOError(f"unknown section: {ident} (0x{ident:08x})")

    def put_into(self, dest):
        try:
            prev = dest[self.ident]
        except KeyError:
            dest[self.ident] = [self]
        else:
            prev.append(self)
        return self

    @staticmethod
    def iter_all(*args, **kw):
        while True:
            yield Section(*args, **kw)

    @staticmethod
    def read_to_map(dbytes, to, index=None, dest=None, **kw):
        if dest is None:
            dest = {}
        for section in Section.iter_all(dbytes, **kw):
            section.put_into(dest)
            if section.ident == to:
                if index is None or len(dest[section.ident]) >= index:
                    return dest
        return dest

    def _print_data(self, file, p):
        if self.ident == SECTION_LAYER:
            p(f"Layer name: {self.layer_name}")
            p(f"Layer object count: {self.num_objects}")
            if self.layer_flags:
                flag_str = ', '.join(names.get(f, f"Unknown({f})") for f, names
                                     in zip(self.layer_flags,
                                            self.layer_flag_names))
                p(f"Layer flags: {flag_str}")


class DstBytes(object):

    def __init__(self, source):
        self.source = source

    @property
    def pos(self):
        return self.source.tell()

    @pos.setter
    def pos(self, newpos):
        self.source.seek(newpos)

    def read_n(self, n, or_to_eof=False):
        result = self.source.read(n)
        if not or_to_eof and len(result) != n:
            raise EOFError
        return result

    def read_byte(self):
        return self.read_n(1)[0]

    def read_number(self):
        n = 0
        bits = 0
        while True:
            b = self.read_byte()
            if b & 0x80:
                n |= (b & 0x7f) << bits
                bits += 7
            else:
                return n | (b << bits)

    def read_fixed_number(self, length, signed=False):
        data = self.read_n(length)
        n = 0
        for i, b in enumerate(data):
            n |= b << (i * 8)
        if signed:
            bit = 1 << (length * 8 - 1)
            if n & bit:
                n -= (bit << 1)
        return n

    def read_struct(self, st):
        if isinstance(st, str):
            st = struct.Struct(st)
        data = self.read_n(st.size)
        return st.unpack(data)

    def read_string(self):
        length = self.read_number()
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


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
