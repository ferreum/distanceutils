"""Probe DstBytes for objects based on .bytes sections."""


import numbers
from collections import OrderedDict

from .bytes import DstBytes, BytesModel, Section, MAGIC_6, CATCH_EXCEPTIONS
from .lazy import LazySequence


class ProbeError(Exception):
    pass


class RegisterError(ValueError):
    pass


class BytesProber(object):

    def __init__(self, baseclass=BytesModel):
        self.baseclass = baseclass
        self._sections = {}
        self._funcs_by_tag = OrderedDict()
        self._funcs = self._funcs_by_tag.values()

    def transaction(self):
        return _ProberTransaction(self)

    def add_type(self, type, cls):
        self._sections[Section(MAGIC_6, type).to_key()] = cls

    def add_func(self, func, tag):
        self._funcs_by_tag[tag] = func

    def _add_fragment_for_section(self, cls, sec, any_version):
        key = sec.to_key(any_version=any_version)
        try:
            registered = self._sections[key]
        except KeyError:
            pass
        else:
            e = RegisterError(f"{sec} is already registered")
            e.registered = registered
            raise e
        self._sections[key] = cls

    def add_fragment(self, cls, *args,
                     any_version=False, versions=None, **kw):

        """Register a fragment.

        If additional arguments are specified, `cls` is registered for the
        `Section` specified by these arguments and the `any_version` argument.

        If there are no additional arguments and `versions` is specified,
        `cls` is registered for the given versions of the section specified
        by the `base_section` attribute of `cls`. If `versions` is not
        specified, the versions are instead taken from the `section_versions`
        attribute of `cls`.

        If `any_version` is specified, `cls` is registered to match any
        version of the specified section.

        """

        if not args and not kw:
            sec = cls.base_section
            if not any_version and versions is None:
                versions = cls.section_versions
        else:
            sec = Section(*args, any_version=any_version, **kw)
        if versions is not None:
            if any_version:
                raise ValueError("Cannot use parameter 'versions' with 'any_version'")
            if isinstance(versions, numbers.Integral):
                versions = [versions]
            for version in versions:
                s = Section(sec, version=version)
                self._add_fragment_for_section(cls, s, any_version)
        else:
            self._add_fragment_for_section(cls, sec, any_version)

    def func(self, tag):

        """Decorator for conveniently adding a function."""

        def decorate(func):
            self.add_func(func, tag)
            return func

        if callable(tag):
            raise ValueError("target passed as tag")

        return decorate

    def for_type(self, *types):

        """Decorator for conveniently adding a class for a type."""

        def decorate(cls):
            for t in types:
                self.add_type(t, cls)
            return cls
        return decorate

    def fragment(self, *args, **kw):

        """Decorator style method for `add_fragment`.

        The decorated class is passed to `add_fragment` in addition to
        the parameters passed to this method.

        If no parameters are needed (except for the class), the class can
        be passsed directly to this method, meaning the "()" can be omitted
        from the decorator expression.

        """

        # Handle being used as decorator without "()": check that we
        # only have one argument, and that it's callable (the class).
        if len(args) == 1 and not kw and callable(args[0]):
            self.add_fragment(args[0])
            return args[0]

        def decorate(cls):
            self.add_fragment(cls, *args, **kw)
            return cls

        return decorate

    def extend_from(self, other):
        self._sections.update(((k, v) for k, v in other._sections.items()
                               if k not in self._sections))
        self._funcs_by_tag.update(other._funcs_by_tag)


    # support old method name
    extend = extend_from


    def _probe_sections(self, sec):
        cls = self._sections.get(sec.to_key(), None)
        if cls is not None:
            return cls
        return self._sections.get(sec.to_key(any_version=True), None)

    def _get_from_funcs(self, sec):
        for func in self._funcs:
            cls = func(sec)
            if cls is not None:
                return cls
        return None

    def probe_section(self, sec):
        cls = self._probe_sections(sec)
        if cls is not None:
            return cls
        cls = self._get_from_funcs(sec)
        if cls is not None:
            return cls
        return self.baseclass

    def probe(self, dbytes, probe_section=None):
        if probe_section is None:
            sec = Section(dbytes, seek_end=False)
        else:
            sec = probe_section
        cls = self.probe_section(sec)
        return cls, {'container': sec}

    def read(self, dbytes, probe_section=None, **kw):
        dbytes = DstBytes.from_arg(dbytes)
        cls, add_kw = self.probe(dbytes, probe_section=probe_section)
        kw.update(add_kw)
        obj = cls(plain=True)
        obj.read(dbytes, **kw)
        return obj

    def maybe(self, dbytes, probe_section=None, **kw):
        dbytes = DstBytes.from_arg(dbytes)
        try:
            cls, add_kw = self.probe(dbytes, probe_section=probe_section)
        except ProbeError:
            raise
        except CATCH_EXCEPTIONS as e:
            ins = self.baseclass()
            ins.exception = e
            ins.sane_end_pos = False
            return ins
        kw.update(add_kw)
        return cls.maybe(dbytes, **kw)

    def iter_n_maybe(self, dbytes, n, *args, **kw):
        dbytes = DstBytes.from_arg(dbytes)
        if 'probe_section' in kw:
            raise TypeError("probe_section not supported")
        for _ in range(n):
            obj = self.maybe(dbytes, *args, **kw)
            yield obj
            if not obj.sane_end_pos:
                break

    def iter_maybe(self, dbytes, *args, max_pos=None, **kw):
        dbytes = DstBytes.from_arg(dbytes)
        if 'probe_section' in kw:
            raise TypeError("probe_section not supported")
        while max_pos is None or dbytes.tell() < max_pos:
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
        if n <= 0:
            return ()
        # stable_iter seeks for us
        kw['seek_end'] = False
        dbytes = DstBytes.from_arg(dbytes)
        gen = self.iter_n_maybe(dbytes, n, *args, **kw)
        return LazySequence(dbytes.stable_iter(gen, start_pos=start_pos), n)


class _ProberTransaction(BytesProber):

    def __init__(self, target):
        super().__init__()
        self._target = target

    def commit(self):

        target = self._target

        for sec, cls in self._sections.items():
            try:
                targetcls = target._sections[sec]
            except KeyError:
                pass
            else:
                if targetcls.__module__ != cls.__module__:
                    raise RegisterError(
                        f"Cannot override class of different module.")

        target._sections.update(self._sections)
        target._funcs_by_tag.update(self._funcs_by_tag)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
