"""Datastructures of .bytes files."""


from collections import OrderedDict

from .bytes import MAGIC_1, S_FLOAT4
from .printing import format_bytes


class NamedPropertyList(OrderedDict):

    def read(self, dbytes):
        num_props = dbytes.read_int(4)
        for _ in range(num_props):
            propname, value = self.read_property(dbytes)
            self[propname] = value

    def read_property(self, dbytes):
        propname = dbytes.read_str()
        propend = dbytes.read_int(8)
        value = dbytes.read_bytes(propend - dbytes.tell())
        return propname, value

    def write(self, dbytes):
        dbytes.write_int(4, len(self))
        for propname, value in self.items():
            self.write_property(dbytes, propname, value)

    def write_property(self, dbytes, propname, value):
        dbytes.write_str(propname)
        dbytes.write_int(8, dbytes.tell() + len(value) + 8)
        dbytes.write_bytes(value)

    def print_data(self, p):
        p(f"Properties: {len(self)}")
        for k, v in self.items():
            p(f"Property: {k!r} = {format_bytes(v)}")


class ColorSet(OrderedDict):

    def read(self, dbytes):
        if dbytes.read_int(4) != MAGIC_1:
            raise ValueError(f"expected {MAGIC_1}")
        num_colors = dbytes.read_int(4)
        for _ in range(num_colors):
            colname, colors = self.read_color(dbytes)
            self[colname] = colors

    def read_color(self, dbytes):
        colname = dbytes.read_str()
        colors = dbytes.read_struct(S_FLOAT4)
        return colname, colors

    def write(self, dbytes):
        dbytes.write_int(4, MAGIC_1)
        dbytes.write_int(4, len(self))
        for colname, color in self.items():
            self.write_color(dbytes, colname, color)

    def write_color(self, dbytes, colname, color):
        dbytes.write_str(colname)
        dbytes.write_bytes(S_FLOAT4.pack(*color))

    def print_data(self, p):
        p(f"Colors: {len(self)}")
        with p.tree_children():
            for colname, color in self.items():
                p.tree_next_child()
                cstr = ", ".join(format(v, ".3f") for v in color)
                p(f"Color: {colname!r} {cstr}")


class MaterialSet(OrderedDict):

    def get_or_add(self, matname):
        try:
            return self[matname]
        except KeyError:
            colors = ColorSet()
            self[matname] = colors
            return colors

    def read(self, dbytes):
        if dbytes.read_int(4) != MAGIC_1:
            raise ValueError(f"expected {MAGIC_1}")
        num_mats = dbytes.read_int(4)
        for _ in range(num_mats):
            matname, colors = self.read_material(dbytes)
            self[matname] = colors

    def read_material(self, dbytes):
        matname = dbytes.read_str()
        colors = ColorSet()
        colors.read(dbytes)
        return matname, colors

    def write(self, dbytes):
        dbytes.write_int(4, MAGIC_1)
        dbytes.write_int(4, len(self))
        for matname, colors in self.items():
            self.write_material(dbytes, matname, colors)

    def write_material(self, dbytes, matname, colors):
        dbytes.write_str(matname)
        colors.write(dbytes)

    def print_data(self, p):
        p(f"Materials: {len(self)}")
        with p.tree_children():
            for matname, colors in self.items():
                p.tree_next_child()
                p(f"Material: {matname!r}")
                colors.print_data(p)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
