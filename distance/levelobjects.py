"""Base classes for objects in levels."""


from .base import BaseObject
from .bytes import Section, Magic
from .base import Fragment, default_fragments
from ._data import MaterialSet
from .classes import CollectorGroup


Classes = CollectorGroup()


@Classes.fragments.fragment
class MaterialFragment(Fragment):

    base_container = Section.base(Magic[3], 0x3)
    container_versions = 1, 2

    have_content = False

    def __init__(self, *args, **kw):
        self.materials = MaterialSet()
        Fragment.__init__(self, *args, **kw)

    def _clone_data(self, new):
        dest = new.materials
        for matname, mat in self.materials.items():
            destmat = dest.get_or_add(matname)
            for colname, col in mat.items():
                destmat[colname] = col

    def _read_section_data(self, dbytes, sec):
        if sec.content_size >= 4:
            self.have_content = True
            self.materials.read(dbytes)

    def _write_section_data(self, dbytes, sec):
        if self.materials or self.have_content:
            self.materials.write(dbytes)

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if 'allprops' in p.flags and self.materials:
            self.materials.print(p)


def material_property(matname, colname):
    doc = f"property forwarded to material color {matname!r}/{colname!r}"
    def fget(self):
        try:
            frag = self['Material']
            return frag.materials[matname][colname]
        except KeyError as e:
            raise AttributeError(f"color {matname!r}/{colname!r}") from e
    def fset(self, value):
        try:
            frag = self['Material']
        except KeyError as e:
            raise AttributeError(f"color {matname!r}/{colname!r}") from e
        frag.materials.get_or_add(matname)[colname] = value
    def fdel(self):
        try:
            frag = self['Material']
            mats = frag.materials
            mat = mats[matname]
            del mat[colname]
        except KeyError as e:
            raise AttributeError(f"color {matname!r}/{colname!r}") from e
        if not mat:
            del mats[matname]
    return property(fget, fset, fdel, doc=doc)


class material_attrs(object):

    """Decorator to forward attributes to colors of MaterialFragment."""

    def __init__(self, **colors):
        self.colors = colors

    def __call__(self, target):
        for attrname, (matname, colname, default) in self.colors.items():
            setattr(target, attrname, material_property(matname, colname))

        try:
            clsdefaults = target.__default_colors
        except AttributeError:
            target.__default_colors = clsdefaults = {}
        clsdefaults.update(self.colors)

        default_fragments.add_to(target, MaterialFragment)

        return target

    @staticmethod
    def reset_colors(obj):
        mats = obj['Material'].materials
        for matname, colname, value in obj.__default_colors.values():
            mats.get_or_add(matname)[colname] = value


class LevelObject(BaseObject):

    child_classes_name = 'level_subobjects'

    has_children = True

    def _visit_print_children(self, p):
        if 'subobjects' in p.flags and self.children:
            num = len(self.children)
            p(f"Subobjects: {num}")
            with p.tree_children(num):
                for obj in self.children:
                    p.tree_next_child()
                    yield obj.visit_print(p)


class SubObject(LevelObject):

    def _print_type(self, p):
        p(f"Subobject type: {self.type!r}")


# vim:set sw=4 ts=8 sts=4 et:
