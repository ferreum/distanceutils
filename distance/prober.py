"""Probe DstBytes for objects based on .bytes sections."""


import os
import numbers
import importlib
from collections import OrderedDict

from .bytes import DstBytes, BytesModel, Section, Magic, CATCH_EXCEPTIONS
from .lazy import LazySequence


do_autoload = os.environ.get("DISTANCEUTILS_AUTOLOAD", "") != "0"


class ProbeError(Exception):
    pass


class RegisterError(ValueError):
    pass


class AutoloadError(Exception):
    pass


def fragment_property(tag, name, default=None, doc=None):
    def fget(self):
        frag = self.fragment_by_tag(tag)
        return getattr(frag, name, default)
    def fset(self, value):
        frag = self.fragment_by_tag(tag)
        setattr(frag, name, value)
    if doc is None:
        doc = f"property forwarded to {tag!r}"
    return property(fget, fset, doc=doc)


class BytesProber(object):

    def __init__(self, baseclass=BytesModel, key=None, keys=()):
        self.baseclass = baseclass
        if key is not None:
            keys = keys + (key,)
        self._keys = keys
        self._sections = {}
        self._autoload_sections = {}
        self._classes = {}
        self._funcs_by_tag = OrderedDict()
        self._funcs = self._funcs_by_tag.values()

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

        if versions and any_version:
            raise ValueError("Cannot use parameter 'versions' with 'any_version'")

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
            if isinstance(versions, numbers.Integral):
                versions = [versions]
            for version in versions:
                s = Section(sec, version=version)
                self._add_fragment_for_section(cls, s, any_version)
        else:
            versions = [sec.version] if sec.has_version() and not any_version else None
            self._add_fragment_for_section(cls, sec, any_version)
        tag = cls.class_tag
        if callable(tag):
            tag = tag()
        if tag is not None:
            self._add_class(cls, tag, sec, versions)

    def add_object(self, type, cls):
        sec = Section(Magic[6], type)
        self._sections[sec.to_key()] = cls
        self._add_class(cls, type, sec)

    def add_func(self, func, tag):
        self._funcs_by_tag[tag] = func

    def add_info(self, *args, tag=None):
        def decorate(cls):
            nonlocal tag
            if tag is None:
                tag = cls.class_tag
                if callable(tag):
                    tag = tag()
            self._add_class(cls, tag)
            return cls
        if len(args) == 1:
            return decorate(args[0])
        else:
            return decorate

    def _add_fragment_for_section(self, cls, sec, any_version):
        if any_version:
            key = sec.to_key(noversion=True)
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

    def func(self, tag):

        """Decorator for conveniently adding a function."""

        def decorate(func):
            self.add_func(func, tag)
            return func

        if callable(tag):
            raise ValueError("target passed as tag")

        return decorate

    def object(self, *args):

        """Decorator for conveniently adding a class for a type."""

        def decorate(cls):
            for t in types:
                self.add_object(t, cls)
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
        _update_class_info(self._classes, other._classes)
        self._autoload_sections.update((k, v) for k, v in other._autoload_sections.items()
                                       if k not in self._autoload_sections)
        self._keys += tuple(k for k in other._keys
                            if k not in self._keys)

    def _add_class(self, cls, tag, container=None, versions=None):
        if type(tag) != str:
            raise ValueError(f"type of tag has to be exactly builtins.str, not {type(tag)!r}")

        fields_map = getattr(cls, '_fields_map', None)
        if callable(fields_map):
            fields_map = fields_map()

        base_container = None
        if container is not None:
            base_container = container.to_key(noversion=True)

        class_spec = (cls.__module__, cls.__name__)
        if versions is None:
            it = iter([None])
        else:
            it = iter(versions)
        ver_map = {}
        for ver in it:
            prev = ver_map.get(ver, None)
            if prev is not None and prev != class_spec:
                raise RegisterError(f"version {ver!r} is already registered for {prev!r}")
            ver_map[ver] = class_spec

        _merge_class_info(self._classes, tag, {
            'base_container': base_container,
            'versions': ver_map,
            'fields': fields_map,
        })

    def _get_by_key(self, key):
        cls = self._sections.get(key, None)
        if cls is not None:
            return cls
        info = self._autoload_sections.get(key, None)
        if info is not None:
            self._autoload_impl_module(key, info)
            return self._sections.get(key, None)
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
        if sec.has_version():
            cls = self._get_by_key(sec.to_key(noversion=True))
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

    def base_container_key(self, tag):
        info = self._classes[tag]
        base = info.get('base_container', None)
        if base is None:
            raise TypeError(f"Class with tag {tag!r} has no container information")
        return base

    def fragment_attrs(self, *tags):
        def decorate(cls):
            from .base import default_fragments
            containers = []
            for tag in tags:
                info = self._classes[tag]
                fields = info['fields']
                container_key = info['base_container']
                if container_key is not None:
                    container = Section.from_key(container_key)
                    if container.has_version():
                        container.version = max(info['versions'])
                    containers.append(container)
                if fields is None:
                    raise TypeError(f"No field information for tag {tag!r}")
                for name, default in fields.items():
                    setattr(cls, name, fragment_property(tag, name, default))
            default_fragments.add_sections_to(cls, *containers)
            return cls
        return decorate

    def klass(self, tag):
        info = self._classes[tag]
        versions = info['versions']
        try:
            clsdef = versions[None]
        except KeyError:
            clsdef = versions[max(versions)]
        modname, clsname = clsdef
        mod = importlib.import_module(modname)
        return getattr(mod, clsname)

    def create(self, tag, *args, **kw):
        return self.klass(tag)(*args, **kw)

    def is_section_interesting(self, sec):
        cls = self._sections.get(sec, None)
        if cls is not None:
            return cls.is_interesting
        info = self._autoload_sections.get(sec.to_key())
        if info is not None:
            modname, classname, is_interesting = info
            return is_interesting
        return False

    def _load_autoload_content(self, content):
        self._autoload_sections.update(content['sections'])
        self._classes.update(content['classes'])

    def _generate_autoload_content(self):
        return {
            'sections': {key: (cls.__module__, cls.__name__, getattr(cls, 'is_interesting', False))
                         for key, cls in self._sections.items()},
            'classes': dict(self._classes),
        }

    def _get_current_autoload_content(self):
        return {
            'sections': dict(self._autoload_sections),
            'classes': dict(self._classes),
        }

    def _autoload_impl_module(self, sec_key, info):
        impl_module, classname, is_interesting = info
        mod = importlib.import_module(impl_module)
        for key in self._keys:
            prober = getattr(mod.Probers, key)
            self._load_impl(prober, False)

    def _load_impl(self, prober, update_classes):
        self._sections.update(((k, v) for k, v in prober._sections.items()
                               if k not in self._sections))
        self._funcs_by_tag.update(prober._funcs_by_tag)
        if update_classes:
            _update_class_info(self._classes, prober._classes)


class ProberGroup(object):

    def __init__(self):
        self._probers = {}

    def __getattr__(self, name):
        try:
            return self._probers[name]
        except KeyError:
            prober = BytesProber()
            self._probers[name] = prober
            return prober

    def __dir__(self):
        return super().__dir__() + list(self._probers.keys())


class ProbersRegistry(object):

    def __init__(self):
        self._autoload_modules = {}
        self._probers = {}

    def get_or_create(self, name):
        try:
            return self._probers[name]
        except KeyError:
            prober = BytesProber(key=name)
            self._probers[name] = prober
            return prober

    def __getattr__(self, name):
        try:
            return self._probers[name]
        except KeyError:
            raise AttributeError(f"No such prober: {name!r}")

    def __dir__(self):
        return super().__dir__() + list(self._probers.keys())

    def autoload_modules(self, module_name, impl_modules):
        if module_name in self._autoload_modules:
            raise Exception(f"Autoload of {module_name!r} is already defined")
        self._autoload_modules[module_name] = impl_modules
        if do_autoload:
            try:
                _load_autoload_module(self._probers, module_name)
                return
            except ImportError:
                pass
        _load_impls_to_probers(self._probers, impl_modules)

    def write_autoload_module(self, module_name):
        try:
            impl_modules = self._autoload_modules[module_name]
        except KeyError:
            raise KeyError(f"Autoload module is not defined: {module_name!r}")
        from distance._autoload_gen import write_autoload_module
        write_autoload_module(module_name, impl_modules, self._probers.keys())

    def _verify_autoload(self, verify_autoload=True):
        actual_probers = {k: BytesProber(key=k) for k in self._probers}
        autoload_probers = {k: BytesProber(key=k) for k in self._probers}
        for autoload_module, impl_modules in self._autoload_modules.items():
            _load_impls_to_probers(actual_probers, impl_modules)
            _load_autoload_module(autoload_probers, autoload_module)
        if verify_autoload:
            if not do_autoload:
                raise Exception(f"Autoload is disabled")
            actual_content = {}
            loaded_content = {}
            for key in self._probers.keys():
                actual_content[key] = actual_probers[key]._generate_autoload_content()
                loaded_content[key] = autoload_probers[key]._get_current_autoload_content()
            return actual_content, loaded_content


def _update_class_info(target, other):
    for tag, oinfo in other.items():
        _merge_class_info(target, tag, oinfo)


def _merge_class_info(classes, tag, info):
    try:
        prev = classes[tag]
    except KeyError:
        classes[tag] = info
    else:
        classes[tag] = _merged_info(tag, prev, info)


def _merged_info(tag, prev, new):
    base_container = prev['base_container']
    if new['base_container'] != base_container:
        raise RegisterError(
            f"Class tag {tag!r} is already registered for base container"
            f" {base_container!r}, not {new['base_container']!r}")

    new_vers = new['versions']
    new_fields = new['fields']

    if not new_vers and not new_fields:
        return prev

    prev_vers = prev['versions']
    prev_fields = prev['fields']

    if new_vers:
        if not prev_vers:
            prev_vers = new_vers
        else:
            for over, ocls in new_vers.items():
                tcls = prev_vers.get(over, None)
                if ocls != tcls:
                    raise RegisterError(f"Tag {tag!r} version {over!r} already"
                                        f" registered for {tcls.__module__}.{tcls.__name__}")
                prev_vers[over] = ocls

    if new_fields:
        if not prev_fields:
            prev_fields = new_fields
        else:
            prev_fields = dict(prev_fields)
            prev_fields.update(new_fields)

    return {
        'base_container': base_container,
        'versions': prev_vers,
        'fields': prev_fields,
    }


def _load_autoload_module(probers, module_name):
    mod = importlib.import_module(module_name)
    content_map = mod.content_map
    for key, content in content_map.items():
        probers[key]._load_autoload_content(content)


def _load_impls_to_probers(probers, impl_modules):
    if callable(impl_modules):
        impl_modules = impl_modules()
    for name in impl_modules:
        mod = importlib.import_module(name)
        try:
            for key, prober in mod.Probers._probers.items():
                try:
                    dest = probers[key]
                except KeyError as e:
                    raise AutoloadError(f"Prober in module {name!r} does not exist: {key!r}") from e
                dest._load_impl(prober, True)
        except AutoloadError:
            raise
        except Exception as e:
            raise AutoloadError(f"Failed to load probers of module {name!r}") from e


# vim:set sw=4 ts=8 sts=4 et:
