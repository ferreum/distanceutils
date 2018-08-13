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


class TagError(LookupError):
    "Given tag not found"

    def __init__(self, tag):
        LookupError.__init__(self, repr(tag))


def fragment_property(tag, name, default=None, doc=None):
    def fget(self):
        try:
            frag = self[tag]
        except KeyError:
            raise AttributeError(name)
        return getattr(frag, name, default)
    def fset(self, value):
        try:
            frag = self[tag]
        except KeyError:
            raise AttributeError(name)
        setattr(frag, name, value)
    if doc is None:
        doc = f"property forwarded to {tag!r}"
    return property(fget, fset, doc=doc)


class ClassCollector(object):

    def __init__(self, **kw):
        super().__init__(**kw)
        self._sections = {}
        self._interesting_sections = set()
        self._autoload_sections = {}
        self._classes = {}
        self._tags_by_base_key = {}

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
        fragment is registered for the section returned by the
        `get_default_container()` method of `cls`.

        If `any_version` is specified, `cls` is registered to match any
        version of the specified section.

        """

        if versions and any_version:
            raise ValueError("Cannot use parameter 'versions' with 'any_version'")

        if not args and not kw:
            sec = cls.base_container
            if not any_version and versions is None:
                versions = cls.container_versions
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
        if tag is not None:
            self._add_info(tag, cls=cls, container=sec, versions=versions)
        if cls.is_interesting:
            self._interesting_sections.add(sec.to_key(noversion=True))

    def add_object(self, type, cls):
        sec = Section(Magic[6], type)
        self._sections[sec.to_key()] = cls
        self._add_info(type, cls=cls, container=sec)

    def add_info(self, *args, tag=None):
        def decorate(cls):
            nonlocal tag
            if tag is None:
                tag = cls.class_tag
            self._add_info(tag, cls=cls)
            return cls
        if len(args) == 1:
            return decorate(args[0])
        else:
            return decorate

    def add_tag(self, tag, *args, **kw):
        self._add_info(tag, container=Section.base(*args, **kw))

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

    def _add_info(self, tag, cls=None, container=None, versions=None):
        if type(tag) is not str:
            raise ValueError(f"type of tag has to be exactly builtins.str, not {type(tag)!r}")

        info = {}

        if cls is not None:
            try:
                fields = cls._fields_
            except AttributeError:
                pass
            else:
                info['fields'] = fields

        if container is not None:
            base_key = container.to_key(noversion=True)
            info['base_container'] = base_key
            self._tags_by_base_key[base_key] = tag

        if cls is not None:
            class_spec = (cls.__module__, cls.__name__)
            if versions is None:
                info['noversion_cls'] = class_spec
            else:
                info['versions'] = dict.fromkeys(versions, class_spec)

        _merge_class_info(self._classes, tag, info)

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


class _BaseProber(object):
    """Base for probers.

    Subclasses need to implement `_probe_section_key` and
    optionally `_probe_fallback`.
    """

    def __init__(self, *, baseclass=BytesModel, **kw):
        super().__init__(**kw)
        self.baseclass = baseclass

    def _probe_section_key(self, key):
        "Return the class for the given section."
        raise NotImplementedError

    def _probe_fallback(self, sec):
        return None

    def probe_section(self, sec):
        key = sec.to_key()
        cls = self._probe_section_key(key)
        if cls is not None:
            return cls
        if sec.has_version():
            key = sec.to_key(noversion=True)
            cls = self._probe_section_key(key)
            if cls is not None:
                return cls
        cls = self._probe_fallback(sec)
        if cls is not None:
            return cls
        return self.baseclass

    def probe(self, dbytes, *, probe_section=None):
        if probe_section is None:
            sec = Section(dbytes, seek_end=False)
        else:
            sec = probe_section
        cls = self.probe_section(sec)
        return cls, sec

    def read(self, dbytes, *, probe_section=None, **kw):
        dbytes = DstBytes.from_arg(dbytes)
        cls, con = self.probe(dbytes, probe_section=probe_section)
        obj = cls(plain=True)
        obj.read(dbytes, container=con, **kw)
        return obj

    def maybe(self, dbytes, *, probe_section=None, **kw):
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

    def iter_n_maybe(self, dbytes, n, **kw):
        dbytes = DstBytes.from_arg(dbytes)
        if 'probe_section' in kw:
            raise TypeError("probe_section not supported")
        for _ in range(n):
            obj = self.maybe(dbytes, **kw)
            yield obj
            if not obj.sane_end_pos:
                break

    def lazy_n_maybe(self, dbytes, n, *, start_pos=None, **kw):
        if n <= 0:
            return ()
        # stable_iter seeks for us
        kw['seek_end'] = False
        dbytes = DstBytes.from_arg(dbytes)
        gen = self.iter_n_maybe(dbytes, n, **kw)
        return LazySequence(dbytes.stable_iter(gen, start_pos=start_pos), n)


class ClassCollection(_BaseProber, ClassCollector):
    "Collection and Prober of registered classes."

    def __init__(self, *, key=None, get_fallback_container=None, **kw):
        super().__init__(**kw)
        self.key = key
        self.get_fallback_container = get_fallback_container
        # We don't have funcs on ClassCollector because they don't need to be
        # lazy-loaded and there's no use for it yet.
        self._funcs_by_tag = OrderedDict()
        self._funcs = self._funcs_by_tag.values()

    def add_func(self, func, tag):
        self._funcs_by_tag[tag] = func

    def func(self, tag):
        "Decorator for conveniently adding a function."
        def decorate(func):
            self.add_func(func, tag)
            return func
        if callable(tag):
            raise TypeError("target passed as tag")
        return decorate

    def _probe_section_key(self, key):
        cls = self._sections.get(key)
        if cls is not None:
            return cls
        module = self._autoload_sections.get(key)
        if module is not None:
            self._autoload_impl_module(key, module)
            return self._sections.get(key)
        return None

    def _probe_fallback(self, sec):
        for func in self._funcs:
            cls = func(sec)
            if cls is not None:
                return cls
        return None

    def get_base_key(self, tag):
        try:
            info = self._classes[tag]
        except KeyError:
            raise TagError(tag)
        try:
            base = info['base_container']
        except KeyError:
            raise TypeError(f"No container information for tag {tag!r}")
        return base

    def get_tag(self, section):
        key = section.to_key(noversion=True)
        return self._tags_by_base_key[key]

    def get_tag_impl_info(self, tag):
        try:
            info = self._classes[tag]
        except KeyError:
            raise TagError(tag)
        try:
            base = info['base_container']
        except KeyError:
            raise TypeError(f"Class with tag {tag!r} has no container information")
        if info.get('noversion_cls') is not None:
            versions = 'all'
        else:
            versions = info.get('versions').keys()
        return base, versions

    def fragment_attrs(self, *tags):
        def decorate(cls):
            from .base import default_fragments
            containers = []
            for tag in tags:
                try:
                    info = self._classes[tag]
                except KeyError:
                    raise TagError(tag)
                try:
                    fields = info['fields']
                except KeyError:
                    raise TypeError(f"No field information for tag {tag!r}")
                container_key = info.get('base_container', None)
                if container_key is not None:
                    container = Section.from_key(container_key)
                    if container.has_version():
                        versions = info.get('versions', None)
                        if versions is not None:
                            container.version = max(versions)
                    containers.append(container)
                for name, default in fields.items():
                    setattr(cls, name, fragment_property(tag, name, default))
            default_fragments.add_sections_to(cls, *containers)
            return cls
        return decorate

    def __klass(self, tag, version, fallback):
        if fallback is None:
            fallback = self.get_fallback_container is not None
        elif fallback and self.get_fallback_container is None:
            raise ValueError("Fallback not defined for this collection")

        try:
            info = self._classes[tag]
        except KeyError:
            if not fallback:
                raise TagError(tag)
            return self.baseclass, self.get_fallback_container(tag)

        (modname, clsname), def_version = _get_klass_def(info, version)
        container = info.get('base_container')
        if container is not None:
            container = Section.from_key(container)
            if def_version is not None and container.has_version():
                container.version = def_version
        mod = importlib.import_module(modname)
        return getattr(mod, clsname), container

    def klass(self, tag, *, version=None):
        return self.__klass(tag, version, False)[0]

    def factory(self, tag, *, version=None, fallback=None):
        cls, container = self.__klass(tag, version, fallback)
        return InstanceFactory(cls, container)

    def create(self, tag, *, fallback=None, **kw):
        cls, container = self.__klass(tag, None, fallback)
        if 'container' not in kw and 'dbytes' not in kw:
            kw['container'] = container
        return cls(**kw)

    def is_section_interesting(self, sec):
        return sec.to_key(noversion=True) in self._interesting_sections

    def _load_autoload_content(self, content):
        self._autoload_sections.update(content['sections'])
        self._interesting_sections.update(content['interesting'])
        self._classes.update(content['classes'])
        self._tags_by_base_key.update(content['key_tags'])

    def _generate_autoload_content(self):
        return {
            'sections': {key: cls.__module__
                         for key, cls in self._sections.items()},
            'interesting': set(self._interesting_sections),
            'classes': dict(self._classes),
            'key_tags': dict(self._tags_by_base_key),
        }

    def _get_current_autoload_content(self):
        return {
            'sections': dict(self._autoload_sections),
            'interesting': set(self._interesting_sections),
            'classes': dict(self._classes),
            'key_tags': dict(self._tags_by_base_key),
        }

    def _autoload_impl_module(self, sec_key, impl_module):
        mod = importlib.import_module(impl_module)
        coll = getattr(mod.Classes, self.key)
        self._load_impl(coll, False)

    def _load_impl(self, coll, update_classes):
        self._sections.update(((k, v) for k, v in coll._sections.items()
                               if k not in self._sections))
        if update_classes:
            _update_class_info(self._classes, coll._classes)
            self._interesting_sections.update(coll._interesting_sections)
            self._tags_by_base_key.update(coll._tags_by_base_key)


class CompositeProber(_BaseProber):

    def __init__(self, *, probers=None, **kw):
        super().__init__(**kw)
        self.probers = [] if probers is None else probers

    def _probe_section_key(self, key):
        for p in self.probers:
            cls = p._probe_section_key(key)
            if cls is not None:
                return cls
        return None

    def _probe_fallback(self, sec):
        for p in self.probers:
            cls = p._probe_fallback(sec)
            if cls is not None:
                return cls
        return None


class CollectorGroup(object):

    def __init__(self):
        self._colls = {}

    def __getattr__(self, name):
        try:
            return self._colls[name]
        except KeyError:
            coll = ClassCollector()
            self._colls[name] = coll
            return coll

    def __dir__(self):
        return super().__dir__() + list(self._colls.keys())


class ClassesRegistry(object):

    def __init__(self):
        self._colls = {}
        self._autoload_modules = {}
        self._autoload_colls = {}

    def init_category(self, key, **kw):
        if key in self._colls:
            raise ValueError(f"Category {key!r} already exists")
        coll = ClassCollection(key=key, **kw)
        self._colls[key] = coll
        self._autoload_colls[key] = coll

    def init_composite(self, key, keys, **kw):
        if key in self._colls:
            raise ValueError(f"Category {key!r} already exists")
        keys = tuple(keys)
        colls = [self._colls[key] for key in keys]
        prober = CompositeProber(probers=colls, **kw)
        self._colls[key] = prober

    def __getattr__(self, name):
        try:
            return self._colls[name]
        except KeyError:
            raise AttributeError(f"No such category: {name!r}")

    def __dir__(self):
        return super().__dir__() + list(self._colls.keys())

    def autoload_modules(self, module_name, impl_modules):
        if module_name in self._autoload_modules:
            raise ValueError(f"Autoload of {module_name!r} is already defined")
        self._autoload_modules[module_name] = impl_modules
        if do_autoload:
            try:
                _load_autoload_module(self._autoload_colls, module_name)
                return
            except ImportError:
                pass # fall through and load immediately
        _load_impls_to_colls(self._autoload_colls, impl_modules)

    def write_autoload_module(self, module_name):
        try:
            impl_modules = self._autoload_modules[module_name]
        except KeyError:
            raise KeyError(f"Autoload module is not defined: {module_name!r}")
        from distance._autoload_gen import write_autoload_module
        write_autoload_module(module_name, impl_modules,
                              self._autoload_colls.keys())

    def _verify_autoload(self):
        keys = self._autoload_colls.keys()
        actual_colls = {k: ClassCollection(key=k) for k in keys}
        autoload_colls = {k: ClassCollection(key=k) for k in keys}
        for autoload_module, impl_modules in self._autoload_modules.items():
            _load_impls_to_colls(actual_colls, impl_modules)
            _load_autoload_module(autoload_colls, autoload_module)
        actual_content = {}
        loaded_content = {}
        for key in keys:
            actual_content[key] = actual_colls[key]._generate_autoload_content()
            loaded_content[key] = autoload_colls[key]._get_current_autoload_content()
        return actual_content, loaded_content

    def copy(self, **overrides):
        colls = dict(self._colls)
        colls.update(overrides)
        res = ClassesRegistry()
        res._autoload_modules = dict(self._autoload_modules)
        res._colls = colls
        return res


class InstanceFactory(object):

    def __init__(self, cls, container):
        self.cls = cls
        self.container = container

    def __call__(self, **kw):
        if 'container' not in kw and 'dbytes' not in kw:
            kw['container'] = self.container
        return self.cls(**kw)


def _get_klass_def(info, version):
    if version is None:
        try:
            return info['noversion_cls'], None
        except KeyError:
            versions = info['versions']
            ver = max(versions)
            return versions[ver], ver
    else:
        try:
            return info['versions'][version], version
        except KeyError:
            return info['noversion_cls'], version


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
    new_container = new.get('base_container')
    new_vers = new.get('versions')
    new_fields = new.get('fields')
    new_nover_cls = new.get('noversion_cls')

    base_container = prev.get('base_container')
    nover_cls = prev.get('noversion_cls')
    vers = prev.get('versions')
    fields = prev.get('fields')

    result = {}

    if new_container is not None and new_container != base_container:
        if base_container is None:
            base_container = new_container
        else:
            raise RegisterError(
                f"Cannot register {new_container!r} as base_container for tag"
                f" {tag!r} because it is already registered for {base_container!r}")
    if base_container is not None:
        result['base_container'] = base_container

    if new_nover_cls is not None and new_nover_cls != nover_cls:
        if not nover_cls:
            nover_cls = new_nover_cls
        else:
            raise RegisterError(
                f"Cannot register {new_nover_cls!r} as version-less class for tag"
                f" {tag!r} because it is already registered for {nover_cls!r}")
    if nover_cls is not None:
        result['noversion_cls'] = nover_cls

    if new_vers is not None:
        if vers is None:
            vers = new_vers
        else:
            vers = dict(vers)
            for nver, ncls in new_vers.items():
                cls = vers.get(nver)
                if cls is not None and ncls != cls:
                    raise RegisterError(f"Tag {tag!r} version {nver!r} already"
                                        f" registered for {cls}")
                vers[nver] = ncls
    if vers is not None:
        result['versions'] = vers

    if new_fields is not None:
        if fields is None:
            fields = new_fields
        else:
            fields = dict(fields)
            fields.update(new_fields)
    if fields is not None:
        result['fields'] = fields

    return result


def _load_autoload_module(colls, module_name):
    mod = importlib.import_module(module_name)
    content_map = mod.content_map
    for key, content in content_map.items():
        try:
            coll = colls[key]
        except KeyError:
            raise RegisterError(f"Invalid category key {key!r}")
        coll._load_autoload_content(content)


def _load_impls_to_colls(colls, impl_modules):
    if callable(impl_modules):
        impl_modules = impl_modules()
    for name in impl_modules:
        mod = importlib.import_module(name)
        try:
            for key, coll in mod.Classes._colls.items():
                try:
                    dest = colls[key]
                except KeyError as e:
                    raise AutoloadError(f"Category in module {name!r} does not exist: {key!r}") from e
                dest._load_impl(coll, True)
        except AutoloadError:
            raise
        except Exception as e:
            raise AutoloadError(f"Failed to load classes of module {name!r}") from e


# vim:set sw=4 ts=8 sts=4 et:
