"""Provides BaseObject."""


from .bytes import (BytesModel, Section, MAGIC_3, MAGIC_5, MAGIC_6,
                    SKIP_BYTES, S_FLOAT, S_FLOAT3, S_FLOAT4)
from .printing import format_transform
from .prober import BytesProber, ProbeError
from .lazy import LazySequence, LazyMappedSequence


BASE_PROBER = BytesProber()

BASE_FRAG_PROBER = BytesProber()

EMPTY_PROBER = BytesProber()

TRANSFORM_MIN_SIZE = 12


def read_transform(dbytes):
    data = dbytes.read_bytes(12)
    if data.startswith(SKIP_BYTES):
        pos = ()
        data = data[4:]
    else:
        pos = S_FLOAT3.unpack(data)
        data = dbytes.read_bytes(8)
    # len(data) == 8
    if data.startswith(SKIP_BYTES):
        rot = ()
        data = data[4:]
    else:
        ndata = dbytes.read_bytes(12)
        rot = S_FLOAT4.unpack(data + ndata[:8])
        data = ndata[8:]
    # len(data) == 4
    if data == SKIP_BYTES:
        scale = ()
    else:
        data = data + dbytes.read_bytes(8)
        scale = S_FLOAT3.unpack(data)
    return pos, rot, scale


def write_transform(dbytes, trans):
    if trans is None:
        trans = ()
    if len(trans) > 0 and len(trans[0]):
        pos = trans[0]
        dbytes.write_bytes(S_FLOAT3.pack(*pos))
    else:
        dbytes.write_bytes(SKIP_BYTES)
    if len(trans) > 1 and len(trans[1]):
        rot = trans[1]
        dbytes.write_bytes(S_FLOAT4.pack(*rot))
    else:
        dbytes.write_bytes(SKIP_BYTES)
    if len(trans) > 2 and len(trans[2]):
        scale = trans[2]
        dbytes.write_bytes(S_FLOAT3.pack(*scale))
    else:
        dbytes.write_bytes(SKIP_BYTES)


def filter_interesting(sec, prober):
    return sec.content_size and prober.probe_section(sec).is_interesting


class Fragment(BytesModel):

    default_section = None

    is_interesting = False

    _raw_data = None

    def _read(self, dbytes, **kw):
        sec = self._get_container()
        self.end_pos = sec.end_pos
        self._read_section_data(dbytes, sec)

    def write(self, dbytes, section=None):
        sec = self.container if section is None else section
        if sec is None:
            self.container = sec = self._init_section()
        with dbytes.write_section(sec):
            self._write_section_data(dbytes, sec)

    @property
    def raw_data(self):
        data = self._raw_data
        if data is None:
            dbytes = self.dbytes
            sec = self.container
            with dbytes:
                dbytes.seek(sec.content_start)
                data = dbytes.read_bytes(sec.content_size)
                self._raw_data = data
        return data

    @raw_data.setter
    def raw_data(self, value):
        self._raw_data = value

    def _init_section(self):
        return self.default_section

    def _read_section_data(self, dbytes, sec):
        pass

    def _write_section_data(self, dbytes, sec):
        dbytes.write_bytes(self.raw_data)

    def _print_type(self, p):
        name = type(self).__name__
        if name.endswith('Fragment'):
            name = name[:-8]
            if not name and type(self) == Fragment:
                p(f"Fragment: Unknown")
            else:
                p(f"Fragment: {name}")


@BASE_FRAG_PROBER.fragment(MAGIC_3, 1, 0)
class ObjectFragment(Fragment):

    transform = None
    has_children = False
    children = ()

    def _read(self, *args, **kw):
        self.child_prober = kw.get('child_prober', EMPTY_PROBER)
        Fragment._read(self, *args, **kw)

    def _read_section_data(self, dbytes, sec):

        """Read data of the given section.

        Returns `True` if the raw section data is not needed.

        Returns `False` to indicate that raw data of the section
        shall be saved (e.g. for `_write_section_data()`).

        """

        if sec.content_size >= TRANSFORM_MIN_SIZE:
            self.transform = read_transform(dbytes)
            if dbytes.tell() + Section.MIN_SIZE < sec.end_pos:
                s5 = Section(dbytes, seek_end=False)
                self.has_children = True
                self.children = self.child_prober.lazy_n_maybe(
                    dbytes, s5.count, opts=self.opts,
                    start_pos=s5.content_start)
        return True

    def _write_section_data(self, dbytes, sec):

        """Write data of the given section.

        Returns `True` if the section has been written.

        Returns `False` if the raw section data shall be copied
        from the source that this object has been read from. This
        is an error if raw data has not been saved for the section
        (e.g. by returning `False` from `_read_section_data`).

        """

        children = self.children
        has_children = self.has_children or children
        if self.transform or has_children:
            write_transform(dbytes, self.transform)
        if self.has_children or self.children:
            with dbytes.write_section(MAGIC_5):
                for obj in self.children:
                    obj.write(dbytes)
        return True


class ForwardFragmentAttrs(object):

    """Decorator to forward attributes of a objects to their fragments."""

    def __init__(self, cls, attrs):
        self.cls = cls
        self.attrs = attrs

    def __call__(self, target):
        cls = self.cls
        doc = f"property forwarded to {cls.__name__!r}"
        for name, default in self.attrs.items():
            # These keyword args are here to capture the values of every
            # iteration. Otherwise they would all refer to the same variable
            # which is set to the value of the last iteration.
            def fget(self, name=name, default=default):
                frag = self.fragment_by_type(cls)
                return getattr(frag, name, default)
            def fset(self, value, name=name):
                frag = self.fragment_by_type(cls)
                setattr(frag, name, value)
            setattr(target, name, property(fget, fset, None, doc=doc))
        return target


@ForwardFragmentAttrs(ObjectFragment, dict(transform=None, children=()))
class BaseObject(BytesModel):

    """Base class of objects represented by a MAGIC_6 section."""

    child_prober = BASE_PROBER
    fragment_prober = BASE_FRAG_PROBER
    is_object_group = False

    sections = ()
    fragments = ()
    _fragment_types = None
    _fragments_by_type = None

    default_sections = (
        Section(MAGIC_3, 0x01, 0),
    )

    def fragment_by_type(self, typ):
        if typ is ObjectFragment:
            # Optimized ObjectFragment access: it is virtually always first.
            frag = self.fragments[0]
            if type(frag) is ObjectFragment:
                return frag
            # not first - fall through to regular method
        types = self._fragment_types
        if types is None:
            probe = self.fragment_prober.probe_section
            secs = self.sections
            types = LazySequence(map(probe, secs), len(secs))
            bytype = {}
            self._fragments_by_type = bytype
        else:
            bytype = self._fragments_by_type
            try:
                return bytype[typ]
            except KeyError:
                pass # not cached, fall through
        i = 0
        for sectype in types:
            if issubclass(sectype, typ):
                frag = self.fragments[i]
                bytype[typ] = frag
                return frag
            i += 1
        bytype[typ] = None
        return None

    def filtered_fragments(self, type_filter):
        fragments = self.fragments
        prober = self.fragment_prober
        i = 0
        for sec in self.sections:
            if type_filter(sec, prober):
                yield fragments[i]
            i += 1

    def _read(self, dbytes):
        sec = self._get_container()
        self.type = sec.type
        self.end_pos = sec.end_pos
        self.sections = Section.lazy_n_maybe(dbytes, sec.count)
        self.fragments = LazyMappedSequence(
            self.sections, self._read_fragment)

    def _read_fragment(self, sec):
        if sec.exception:
            # failed to read section - return object containing the error
            return Fragment(exception=sec.exception)
        dbytes = self.dbytes
        dbytes.seek(sec.content_start)
        return self.fragment_prober.maybe(
            dbytes, probe_section=sec,
            child_prober=self.child_prober)

    def write(self, dbytes):
        if self.container is None:
            self.container = Section(MAGIC_6, self.type)
        if self.sections is ():
            self._init_defaults()
        with dbytes.write_section(self.container):
            for frag in self.fragments:
                frag.write(dbytes)

    def _init_defaults(self):
        sections = list(Section(s) for s in self.default_sections)
        fragments = []
        self.sections = sections
        self.fragments = fragments
        for sec in sections:
            try:
                cls = self.fragment_prober.probe_section(sec)
            except ProbeError:
                pass # subclass has to write this section
            else:
                frag = cls(container=sec)
                if cls is ObjectFragment:
                    frag.has_children = self.has_children
                fragments.append(frag)

    def iter_children(self, ty=None, name=None):
        for obj in self.children:
            if ty is None or isinstance(obj, ty):
                if name is None or obj.type == name:
                    yield obj

    def _print_data(self, p):
        if 'transform' in p.flags:
            p(f"Transform: {format_transform(self.transform)}")
        if 'fragments' in p.flags and self.fragments:
            if 'allprops' in p.flags:
                p(f"Fragments: {len(self.fragments)}")
                with p.tree_children():
                    for frag in self.fragments:
                        p.tree_next_child()
                        p.print_data_of(frag)
            else:
                frags = self.filtered_fragments(filter_interesting)
                try:
                    frag = next(frags)
                    p(f"Fragments: {len(self.fragments)} <filtered>")
                    with p.tree_children():
                        p.tree_next_child()
                        p.print_data_of(frag)
                        for frag in frags:
                            p.tree_next_child()
                            p.print_data_of(frag)
                except StopIteration:
                    pass

    def _print_children(self, p):
        if self.children:
            num = len(self.children)
            p(f"Children: {num}")
            with p.tree_children():
                for obj in self.children:
                    p.tree_next_child()
                    p.print_data_of(obj)


@BASE_PROBER.func
def _probe_fallback(sec):
    if sec.magic == MAGIC_6:
        return BaseObject
    return None


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
