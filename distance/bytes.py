#!/usr/bin/python
# File:        bytes.py
# Description: bytes
# Created:     2017-06-24


import struct

from .common import format_bytes


S_COLOR_RGBA = struct.Struct("4f")


SECTION_LEVEL = 99999999
SECTION_TYPE = 66666666
SECTION_UNK_3 = 33333333
SECTION_UNK_2 = 22222222
SECTION_UNK_1 = 11111111


class BytesModel(object):

    unknown = ()
    sections = None

    def __init__(self, dbytes, sections=None, **kw):
        if sections is not None:
            self.sections = sections
        self.dbytes = dbytes
        self.parse(dbytes, **kw)

    def parse(self, dbytes):
        raise NotImplementedError(
            "Subclass needs to override parse(self, dbytes)")

    def print_data(self, file, unknown=False):
        if unknown:
            for s_list in self.sections.values():
                for i, s in enumerate(s_list):
                    if s.unknown:
                        print(f"Section {s.ident}-{i} unknown: {format_bytes(s.unknown)}",
                              file=file)
            if self.unknown:
                print(f"Unknown: {format_bytes(self.unknown)}", file=file)

    def read_sections_to(self, to, index=None):
        sections = self.sections
        if sections is None:
            self.sections = sections = {}
        return Section.read_to_map(self.dbytes, to, index=index, dest=sections)

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
            if ts.filetype != expect:
                raise IOError(f"Invalid bytes filetype: {ts.filetype}")
        else:
            if not expect(ts.filetype):
                raise IOError(f"Invalid bytes filetype: {ts.filetype}")
        return ts

    def require_section(self, ident, index=0):
        s = self.get_section(ident, index)
        if s is not None:
            return s
        self.read_sections_to(ident, index)
        return self.get_section(ident, index)

    def add_unknown(self, n):
        unknown = self.unknown
        if unknown is ():
            self.unknown = unknown = []
        unknown.append(self.dbytes.read_n(n))


class Section(BytesModel):

    def parse(self, dbytes):
        self.ident = ident = dbytes.read_fixed_number(4)
        self.unknown = []
        if ident == SECTION_TYPE:
            self.add_unknown(8)
            self.filetype = dbytes.read_string()
            self.add_unknown(9)
        elif ident == SECTION_UNK_3:
            self.add_unknown(20)
        elif ident == SECTION_UNK_2:
            self.add_unknown(12)
            self.version = dbytes.read_byte()
            self.add_unknown(3)
        elif ident == SECTION_LEVEL:
            self.add_unknown(8)
            self.level_name = dbytes.read_string()
            self.add_unknown(8)
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
    def iter_all(dbytes):
        while True:
            yield Section(dbytes)

    @staticmethod
    def read_to_map(dbytes, to, index=None, dest=None):
        if dest is None:
            dest = {}
        for section in Section.iter_all(dbytes):
            section.put_into(dest)
            if section.ident == to:
                if index is None or len(dest[section.ident]) >= index:
                    return dest
        return dest


class DstBytes(object):

    def __init__(self, source):
        self.source = source

    @property
    def pos(self):
        return self.source.tell()

    @pos.setter
    def pos(self, newpos):
        self.source.seek(newpos)

    def read_n(self, n):
        result = self.source.read(n)
        if len(result) != n:
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

    def read_fixed_number(self, length):
        data = self.read_n(length)
        n = 0
        for i, b in enumerate(data):
            n |= b << (i * 8)
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
