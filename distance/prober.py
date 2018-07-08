"""Probe DstBytes for objects based on .bytes sections."""


import os
import numbers
from collections import OrderedDict

from .bytes import DstBytes, BytesModel, Section, Magic, CATCH_EXCEPTIONS
from .lazy import LazySequence


do_autoload = os.environ.get("DISTANCEUTILS_AUTOLOAD", "") != "0"


class ProbeError(Exception):
    pass


class RegisterError(ValueError):
    pass


class BytesProber(object):

    def __init__(self, baseclass=BytesModel, key=None):
        self.baseclass = baseclass
        self.key = key
        self._sections = {}
        self._autoload_sections = {}
        self._funcs_by_tag = OrderedDict()
        self._funcs = self._funcs_by_tag.values()

    def transaction(self):
        return _ProberTransaction(self)

    def add_type(self, type, cls):
        self._sections[Section(Magic[6], type).to_key()] = cls

    def add_func(self, func, tag):
        self._funcs_by_tag[tag] = func

    def _add_fragment_for_section(self, cls, sec, any_version):
        if any_version:
            key = sec.to_noversion_key()
            if key is None:
                raise ValueError(f"Cannot use any_version with {sec!r}")
        else:
            key = sec.to_key()
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
        by the `base_container` attribute of `cls`. If `versions` is not
        specified, the versions are instead taken from the `container_versions`
        attribute of `cls`. If the `base_container` attribute is None, the
        fragment is registered for the section specified by the
        `default_container` attribute of `cls`.

        If `any_version` is specified, `cls` is registered to match any
        version of the specified section.

        """

        if not args and not kw:
            sec = cls.base_container
            if sec is not None:
                if not any_version and versions is None:
                    versions = cls.container_versions
            else:
                sec = cls.default_container
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

    def for_type(self, *args):

        """Decorator for conveniently adding a class for a type."""

        def decorate(cls):
            for t in types:
                self.add_type(t, cls)
            return cls

        if len(args) == 1 and callable(args[0]):
            types = [args[0].type]
            return decorate(args[0])
        else:
            types = args
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


    def _get_by_key(self, key):
        cls = self._sections.get(key, None)
        if cls is not None:
            return cls
        info = self._autoload_sections.get(key, None)
        if info is not None:
            return self._autoload_impl_module(key, info)
        return None

    def _get_from_funcs(self, sec):
        for func in self._funcs:
            cls = func(sec)
            if cls is not None:
                return cls
        return None

    def probe_section(self, sec):
        cls = self._get_by_key(sec.to_key())
        if cls is not None:
            return cls
        nover_key = sec.to_noversion_key()
        if nover_key is not None:
            cls = self._get_by_key(nover_key)
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
        return cls, sec

    def read(self, dbytes, probe_section=None, **kw):
        dbytes = DstBytes.from_arg(dbytes)
        cls, con = self.probe(dbytes, probe_section=probe_section)
        obj = cls(plain=True)
        obj.read(dbytes, container=con, **kw)
        return obj

    def maybe(self, dbytes, probe_section=None, **kw):
        dbytes = DstBytes.from_arg(dbytes)
        try:
            cls, con = self.probe(dbytes, probe_section=probe_section)
        except ProbeError:
            raise
        except CATCH_EXCEPTIONS as e:
            ins = self.baseclass()
            ins.exception = e
            ins.sane_end_pos = False
            return ins
        return cls.maybe(dbytes, container=con, **kw)

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

    def autoload_modules(self, module_name, *impl_modules):
        if do_autoload:
            try:
                self._load_autoload_module(module_name)
                return
            except ImportError:
                pass
        for name in impl_modules:
            self._load_impl_module(name)

    def _write_autoload_module(self, file):
        self._autoload_all()
        file.write("autoload_sections = {\n")
        for key, cls in self._sections.items():
            file.write(f"    {key}: ({cls.__module__!r}, {cls.__name__!r}),\n")
        file.write("}\n")

    def _autoload_all(self):
        for module_name in set(info[0] for info in self._autoload_sections):
            self._load_impl_module(module_name)

    def _autoload_impl_module(self, sec_key, info):
        import importlib
        impl_module, classname = info
        mod = importlib.import_module(impl_module)
        prober = getattr(mod.Probers, self.key)
        self.extend_from(prober)
        return prober.probe_section(sec_key)

    def _load_autoload_module(self, module_name):
        import importlib
        mod = importlib.import_module(module_name)
        sections = mod.autoload_sections
        self._autoload_sections.update(sections)

    def _load_impl_module(self, module_name):
        import importlib
        mod = importlib.import_module(module_name)
        try:
            prober = getattr(mod.Probers, self.key)
        except AttributeError:
            pass
        else:
            self.extend_from(prober)


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


# vim:set sw=4 ts=8 sts=4 et:
