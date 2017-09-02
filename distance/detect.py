# File:        detect.py
# Description: detect
# Created:     2017-06-28


from .bytes import Section, SECTION_6


class BytesProber(object):

    def __init__(self, types=None, funcs=None):
        self._types = types or {}
        self._funcs = funcs or []

    def add_type(self, type, cls):
        self._types[type] = cls

    def add_func(self, func):
        self._funcs.append(func)

    def func(self, func):

        """Decorator for conveniently adding a function."""

        self.add_func(func)
        return func

    def for_type(self, *types):

        """Decorator for conveniently adding a class for a type."""

        def decorate(cls):
            for t in types:
                self.add_type(t, cls)
            return cls
        return decorate

    def extend(self, other):
        self._types.update(((k, v) for k, v in other._types.items()
                            if k not in self._types))
        self._funcs.extend(other._funcs)

    def _get_from_funcs(self, section):
        for func in self._funcs:
            cls = func(section)
            if cls is not None:
                return cls
        return None

    def detect_class(self, dbytes):
        start_pos = dbytes.pos
        section = Section(dbytes)
        start_section = section
        if section.magic == SECTION_6:
            ty = section.type
            cls = self._types.get(ty, None)
            if cls is None:
                cls = self._get_from_funcs(section)
            if cls is None:
                raise IOError(f"Unknown object type: {ty!r}")
        else:
            cls = self._get_from_funcs(section)
        if cls is None:
            raise IOError(f"Unknown object section: {section.magic}")
        return cls, {'start_section': start_section, 'start_pos': start_pos}

    def read(self, dbytes, **kw):
        cls, add_kw = self.detect_class(dbytes)
        kw.update(add_kw)
        obj = cls()
        obj.read(dbytes, **kw)
        return obj

    def maybe(self, dbytes, **kw):
        cls, add_kw = self.detect_class(dbytes)
        kw.update(add_kw)
        return cls.maybe(dbytes, **kw)

    def iter_maybe(self, dbytes, *args, max_pos=None, **kw):
        try:
            while max_pos is None or dbytes.pos < max_pos:
                yield self.maybe(dbytes, *args, **kw)
        except EOFError:
            pass


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
