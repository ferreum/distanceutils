"""Probe DstBytes for objects based on .bytes sections."""


from .bytes import BytesModel, Section, MAGIC_6
from .lazy import LazySequence


class BytesProber(object):

    def __init__(self, types=None, funcs=None, baseclass=BytesModel):
        self.baseclass = baseclass
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

    def probe(self, dbytes):
        start_pos = dbytes.pos
        section = Section(dbytes)
        start_section = section
        if section.magic == MAGIC_6:
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
        cls, add_kw = self.probe(dbytes)
        kw.update(add_kw)
        obj = cls()
        obj.read(dbytes, **kw)
        return obj

    def maybe(self, dbytes, **kw):
        try:
            cls, add_kw = self.probe(dbytes)
        except Exception as e:
            ins = self.baseclass()
            ins.exception = e
            return ins
        kw.update(add_kw)
        return cls.maybe(dbytes, **kw)

    def iter_n_maybe(self, dbytes, n, *args, **kw):
        for _ in range(n):
            obj = self.maybe(dbytes, *args, **kw)
            yield obj
            if not obj.sane_end_pos:
                break

    def iter_maybe(self, dbytes, *args, max_pos=None, **kw):
        while max_pos is None or dbytes.pos < max_pos:
            obj = self.maybe(dbytes, *args, **kw)
            yield obj
            if not obj.sane_end_pos:
                break

    def read_n_maybe(self, *args, **kw):
        objs = []
        for obj in self.iter_n_maybe(*args, **kw):
            objs.append(obj)
        return objs

    def lazy_n_maybe(self, dbytes, n, *args, start_pos=None, **kw):
        gen = self.iter_n_maybe(dbytes, n, *args, **kw)
        return LazySequence(dbytes.stable_iter(gen, start_pos=start_pos), n)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
