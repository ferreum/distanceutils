#!/usr/bin/python
# File:        section.py
# Description: section
# Created:     2017-06-27


SECTION_TYPE = 66666666
SECTION_UNK_3 = 33333333
SECTION_UNK_2 = 22222222
SECTION_UNK_1 = 11111111


class Section(object):

    def __init__(self, ident, dbytes):
        self.ident = ident
        self.unknown = unknown = []
        if ident == SECTION_TYPE:
            unknown.append(dbytes.read_n(8))
            self.filetype = dbytes.read_string()
            unknown.append(dbytes.read_n(9))
        elif ident == SECTION_UNK_3:
            unknown.append(dbytes.read_n(20))
        elif ident == SECTION_UNK_2:
            unknown.append(dbytes.read_n(12))
            self.version = dbytes.read_byte()
            unknown.append(dbytes.read_n(3))
        else:
            raise IOError(f"unknown section: {ident} (0x{ident:08x})")

    @staticmethod
    def iter_to(dbytes, to):
        while True:
            ident = dbytes.read_fixed_number(4)
            yield Section(ident, dbytes)
            if ident == to:
                break

    @staticmethod
    def read_to_map(dbytes, to, dest=None):
        if dest is None:
            dest = {}
        for section in Section.iter_to(dbytes, to):
            try:
                prev = dest[section.ident]
            except KeyError:
                dest[section.ident] = [section]
            else:
                prev.append(section)
        return dest


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
