"""Probe DstBytes for objects based on .bytes sections."""


from .bytes import BytesModel, Section, MAGIC_6
from .lazy import LazySequence


class ProbeError(Exception):
    pass


class BytesProber(object):

    def __init__(self, types=None, fragments=None, funcs=None,
                 baseclass=BytesModel):
        self.baseclass = baseclass
        self._types = types or {}
        self._fragments = fragments or {}
        self._funcs = funcs or []

    def add_type(self, type, cls):
        self._types[type] = cls

    def add_func(self, func, high_prio=False):
        if high_prio:
            self._funcs.insert(0, func)
        else:
            self._funcs.append(func)

    def add_fragment(self, cls, *args, **kw):
        if not kw and len(args) == 1 and isinstance(args[0], Section):
            sec = args[0]
        else:
            sec = Section(*args, **kw)
        key = sec.to_key()
        if key in self._fragments:
            raise ValueError(f"{sec} is already registered")
        self._fragments[key] = cls

    def func(self, *args, high_prio=False):

        """Decorator for conveniently adding a function."""

        def decorate(func):
            self.add_func(func, high_prio=high_prio)
            return func

        if args:
            func = args[0]
            return decorate(func)
        else:
            return decorate

    def for_type(self, *types):

        """Decorator for conveniently adding a class for a type."""

        def decorate(cls):
            for t in types:
                self.add_type(t, cls)
            return cls
        return decorate

    def fragment(self, *args, **kw):

        """Decorator for matching a section."""

        def decorate(cls):
            self.add_fragment(cls, *args, **kw)
            return cls

        return decorate

    def extend(self, other):
        self._types.update(((k, v) for k, v in other._types.items()
                            if k not in self._types))
        self._fragments.update(((k, v) for k, v in other._fragments.items()
                                if k not in self._fragments))
        self._funcs.extend(other._funcs)

    def _probe_fragment(self, section):
        return self._fragments.get(section.to_key(), None)

    def _get_from_funcs(self, section):
        for func in self._funcs:
            cls = func(section)
            if cls is not None:
                return cls
        return None

    def probe_section(self, section):
        if section.magic == MAGIC_6:
            cls = self._types.get(section.type, None)
            if cls is not None:
                return cls
        cls = self._probe_fragment(section)
        if cls is not None:
            return cls
        cls = self._get_from_funcs(section)
        if cls is not None:
            return cls
        if section.magic == MAGIC_6:
            raise ProbeError(f"Unknown object type: {section.type!r}")
        raise ProbeError(f"Unknown object section: {section}")

    def probe(self, dbytes, probe_section=None):
        if probe_section is None:
            section = Section(dbytes)
        else:
            section = probe_section
        cls = self.probe_section(section)
        return cls, {'start_section': section}

    def read(self, dbytes, probe_section=None, **kw):
        cls, add_kw = self.probe(dbytes, probe_section=probe_section)
        kw.update(add_kw)
        obj = cls(plain=True)
        obj.read(dbytes, **kw)
        return obj

    def maybe(self, dbytes, probe_section=None, **kw):
        try:
            cls, add_kw = self.probe(dbytes, probe_section=probe_section)
        except ProbeError:
            raise
        except Exception as e:
            ins = self.baseclass()
            ins.exception = e
            return ins
        kw.update(add_kw)
        return cls.maybe(dbytes, **kw)

    def iter_n_maybe(self, dbytes, n, *args, **kw):
        if 'probe_section' in kw:
            raise TypeError("probe_section not supported")
        for _ in range(n):
            obj = self.maybe(dbytes, *args, **kw)
            yield obj
            if not obj.sane_end_pos:
                break

    def iter_maybe(self, dbytes, *args, max_pos=None, **kw):
        if 'probe_section' in kw:
            raise TypeError("probe_section not supported")
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
