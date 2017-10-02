"""Provides BaseObject."""


from .bytes import (BytesModel, Section, MAGIC_3, MAGIC_5, MAGIC_6,
                    SKIP_BYTES, S_FLOAT, S_FLOAT3, S_FLOAT4)
from .printing import format_transform
from .prober import BytesProber, ProbeError
from .lazy import LazySequenceMapping


BASE_PROBER = BytesProber()

BASE_FRAG_PROBER = BytesProber()

EMPTY_PROBER = BytesProber()

TRANSFORM_MIN_SIZE = 12


def read_transform(dbytes):
    def read_float():
        return dbytes.read_struct(S_FLOAT)[0]
    f = dbytes.read_bytes(4)
    if f == SKIP_BYTES:
        pos = ()
    else:
        pos = (S_FLOAT.unpack(f)[0], read_float(), read_float())
    f = dbytes.read_bytes(4)
    if f == SKIP_BYTES:
        rot = ()
    else:
        rot = (S_FLOAT.unpack(f)[0], read_float(), read_float(), read_float())
    f = dbytes.read_bytes(4)
    if f == SKIP_BYTES:
        scale = ()
    else:
        scale = (S_FLOAT.unpack(f)[0], read_float(), read_float())
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


class BaseObject(BytesModel):

    """Base class of objects represented by a MAGIC_6 section."""

    child_prober = BASE_PROBER
    fragment_prober = BASE_FRAG_PROBER
    is_object_group = False

    fragments = ()

    default_sections = (
        Section(MAGIC_3, 0x01, 0),
    )

    def fragment_by_type(self, typ):
        for frag in self.fragments:
            if isinstance(frag, typ):
                return frag
        return None

    def _read(self, dbytes):
        ts = self._get_container()
        self.type = ts.type
        self._report_end_pos(ts.data_end)
        self.sections = Section.lazy_n_maybe(dbytes, ts.num_sections)
        self.fragments = LazySequenceMapping(
            self.sections, self._read_fragment)

    def _read_fragment(self, sec):
        if sec.exception:
            raise sec.exception
        dbytes = self.dbytes
        with dbytes.saved_pos(sec.end_pos):
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
                sec.__fragment = frag
                fragments.append(frag)

    def iter_children(self, ty=None, name=None):
        for obj in self.children:
            if ty is None or isinstance(obj, ty):
                if name is None or obj.type == name:
                    yield obj

    @property
    def children(self):
        frag = self.fragment_by_type(ObjectFragment)
        if frag is None:
            return ()
        return frag.children

    @children.setter
    def children(self, value):
        self.fragment_by_type(ObjectFragment).children = value

    @property
    def transform(self):
        frag = self.fragment_by_type(ObjectFragment)
        if frag is None:
            return None
        return frag.transform

    @transform.setter
    def transform(self, value):
        self.fragment_by_type(ObjectFragment).transform = value

    def _print_data(self, p):
        if 'transform' in p.flags:
            p(f"Transform: {format_transform(self.transform)}")
        if 'fragments' in p.flags and self.fragments:
            p(f"Fragments: {len(self.fragments)}")
            with p.tree_children():
                for fragment in self.fragments:
                    p.tree_next_child()
                    p.print_data_of(fragment)

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


class Fragment(BytesModel):

    default_section = None

    raw_data = None

    def _read(self, dbytes, **kw):
        sec = self._get_container()
        self._report_end_pos(sec.data_end)
        pos = dbytes.tell()
        if not self._read_section_data(dbytes, sec):
            with dbytes.saved_pos(pos):
                self.raw_data = dbytes.read_bytes(
                    sec.data_end - pos, or_to_eof=True)

    def write(self, dbytes, section=None):
        sec = self.container if section is None else section
        if sec is None:
            self.container = sec = self._init_section()
        with dbytes.write_section(sec):
            if not self._write_section_data(dbytes, sec):
                data = self.raw_data
                if data is None:
                    raise ValueError("Raw data not available")
                dbytes.write_bytes(data)

    def _init_section(self):
        return self.default_section

    def _read_section_data(self, dbytes, sec):
        return False

    def _write_section_data(self, dbytes, sec):
        return False

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

        end = sec.data_end
        if dbytes.tell() + TRANSFORM_MIN_SIZE < end:
            self.transform = read_transform(dbytes)
            if dbytes.tell() + Section.MIN_SIZE < end:
                s5 = Section(dbytes)
                self.has_children = True
                self.children = self.child_prober.lazy_n_maybe(
                    dbytes, s5.num_objects, start_pos=s5.children_start,
                    opts=self.opts)
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


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
