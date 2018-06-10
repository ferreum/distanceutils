"""Facilities for defining fragments with the construct module."""


from construct import (
    PascalString, VarInt,
)

from distance.base import Fragment


class C(object):

    """Provides cons useful for distance .bytes files."""

    from construct import (
        Struct as struct,
        Default as default,
        Byte as byte,
        Int32sl as int,
        Int32ul as uint,
        Int64sl as long,
        Int64ul as ulong,
        Float32l as float,
        Float64l as double,
    )

    str = PascalString(VarInt, encoding='utf-16le')


class BaseConstructFragment(Fragment):

    """Baseclass for fragments defined by construct Structs.

    Subclasses need to override the `_format` attribute with the Struct that
    defines the fragment.

    """

    # to be overridden by subclasses
    _format = None

    def _init_defaults(self):
        self.data = {}

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            self.data = self._format.parse(dbytes.read_bytes(sec.content_size))
        else:
            # Data is empty - game falls back to defaults here.
            self.data = {}

    def _write_section_data(self, dbytes, sec):
        # If data is empty, game falls back to defaults.
        if self.data:
            dbytes.write_bytes(self._format.build(self.data))

    def _print_data(self, p):
        if 'allprops' in p.flags:
            with p.tree_children():
                for k, v in self.data.items():
                    if k != '_io': # construct internal?
                        p.tree_next_child()
                        p(f"Construct: {k} = {v!r}")


def construct_property(cls, name, doc=None):
    if doc is None:
        doc = f"property forwarded to {cls.__name__!r}"
    def fget(self):
        try:
            return self.data[name]
        except KeyError as e:
            raise AssertionError from e
    def fset(self, value):
        self.data[name] = value
    def fdel(self):
        del self.data[name]
    return property(fget, fset, fdel, doc=doc)


def ExposeConstructFields(target=None, only=None):

    """Decorator to expose construct fields as attributes."""

    def decorate(target):
        if only is None:
            names = (c.name for c in target._format.subcons if c.name)
        else:
            names = only
        for name in names:
            setattr(target, name, construct_property(target, name))
        return target

    if target is None:
        return decorate
    return decorate(target)


# vim:set sw=4 ts=8 sts=4 et:
