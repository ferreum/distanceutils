"""Provides BaseObject."""


from .bytes import (BytesModel, Section, MAGIC_3, MAGIC_5, MAGIC_6,
                    SKIP_BYTES, S_FLOAT, S_FLOAT3, S_FLOAT4)
from .printing import format_transform


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

    child_prober = None
    is_object_group = False

    transform = None
    _children = None
    has_children = False
    children_section = None

    default_sections = (
        Section(MAGIC_3, 0x01, 0),
    )

    def _read(self, dbytes):
        ts = self._get_start_section()
        self.type = ts.type
        self._report_end_pos(ts.data_end)
        self._read_sections(ts.data_end)

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_3, 0x01):
            end = sec.data_end
            if dbytes.pos + TRANSFORM_MIN_SIZE < end:
                self.transform = read_transform(dbytes)
            if dbytes.pos + Section.MIN_SIZE < end:
                self.children_section = Section(dbytes)
                self.has_children = True
            return True
        return BytesModel._read_section_data(self, dbytes, sec)

    def write(self, dbytes):
        if self.sections is ():
            self.sections = self._init_sections()
        with dbytes.write_section(MAGIC_6, self.type):
            self._write_sections(dbytes)

    def _init_sections(self):
        return self.default_sections

    def _write_section_data(self, dbytes, sec):
        if sec.match(MAGIC_3, 0x01):
            children = self.children
            has_children = self.has_children or children
            if self.transform or has_children:
                write_transform(dbytes, self.transform)
            if self.has_children or self.children:
                dbytes.write_int(4, MAGIC_5)
                with dbytes.write_size():
                    dbytes.write_int(4, len(self.children))
                    for obj in self.children:
                        obj.write(dbytes)
            return True
        return BytesModel._write_section_data(self, dbytes, sec)

    @property
    def children(self):
        objs = self._children
        if objs is None:
            s5 = self.children_section
            if s5 and s5.num_objects:
                self._children = objs = []
                dbytes = self.dbytes
                with dbytes.saved_pos():
                    dbytes.pos = s5.children_start
                    objs = self.child_prober.read_n_maybe(
                        dbytes, s5.num_objects)
                    self._children = objs
            else:
                self._children = objs = ()
        return objs

    @children.setter
    def children(self, objs):
        self._children = objs

    def iter_children(self, ty=None, name=None):
        for obj in self.children:
            if ty is None or isinstance(obj, ty):
                if name is None or obj.type == name:
                    yield obj

    def _print_data(self, p):
        if 'transform' in p.flags:
            p(f"Transform: {format_transform(self.transform)}")

    def _print_children(self, p):
        if self.children:
            num = len(self.children)
            p(f"Children: {num}")
            with p.tree_children():
                for obj in self.children:
                    p.tree_next_child()
                    p.print_data_of(obj)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
