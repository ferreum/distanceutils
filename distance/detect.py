#!/usr/bin/python
# File:        detect.py
# Description: detect
# Created:     2017-06-28


from .bytes import Section, SECTION_TYPE


class BytesProber(object):

    def __init__(self, types=None, funcs=None):
        self._types = types or {}
        self._funcs = funcs or []

    def add_type(self, type, cls):
        self._types[type] = cls

    def add_func(self, func):
        self._funcs.append(func)

    def _get_from_funcs(self, section):
        for func in self._funcs:
            cls = func(section)
            if cls is not None:
                return cls
        return None

    def detect_class(self, dbytes):
        sections = {}
        section = Section(dbytes).put_into(sections)
        if section.ident == SECTION_TYPE:
            filetype = section.filetype
            cls = self._types.get(filetype, None)
            if cls is None:
                cls = self._get_from_funcs(section)
            if cls is None:
                raise IOError(f"Unknown filetype: {filetype!r}")
        else:
            cls = self._get_from_funcs(section)
        if cls is None:
            raise IOError(f"Unknown initial section: {section.ident}")
        return cls, sections

    def parse(self, dbytes):
        cls, sections = self.detect_class(dbytes)
        return cls(dbytes, sections=sections)

    def parse_maybe_partial(self, dbytes):
        cls, sections = self.detect_class(dbytes)
        return cls.maybe_partial(dbytes, sections=sections)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
