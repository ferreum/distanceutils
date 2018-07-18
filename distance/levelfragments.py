"""Level fragment implementations."""


from .bytes import Section, Magic
from .base import Fragment, default_fragments
from ._data import MaterialSet
from .prober import BytesProber


class Probers(object):
    fragments = BytesProber()


@Probers.fragments.fragment
class GroupFragment(Fragment):

    base_container = Section.base(Magic[2], 0x1d)
    container_versions = 1

    value_attrs = dict(
        inspect_children = None, # None
    )

    _has_more_data = False

    def _init_defaults(self):
        super()._init_defaults()
        for name, value in self.value_attrs.items():
            setattr(self, name, value)

    def _read_section_data(self, dbytes, sec):
        if sec.content_size < 12:
            self.inspect_children = None
        else:
            dbytes.require_equal_uint4(Magic[1])
            num_values = dbytes.read_uint4()
            self.inspect_children = dbytes.read_uint4()
            # do save raw_data if there are unexpected values following
            self._has_more_data = num_values > 0

    def _write_section_data(self, dbytes, sec):
        if not self._has_more_data:
            if self.inspect_children is not None:
                dbytes.write_int(4, Magic[1])
                dbytes.write_int(4, 0) # num values
                dbytes.write_int(4, self.inspect_children)
        else:
            dbytes.write_bytes(self.raw_data)


@Probers.fragments.fragment
class CustomNameFragment(Fragment):

    base_container = Section.base(Magic[2], 0x63)
    container_versions = 0

    value_attrs = dict(custom_name=None)

    is_interesting = True

    custom_name = None

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            self.custom_name = dbytes.read_str()

    def _write_section_data(self, dbytes, sec):
        if self.custom_name is not None:
            dbytes.write_str(self.custom_name)

    def _print_type(self, p):
        p(f"Fragment: CustomName")

    def _print_data(self, p):
        super()._print_data(p)
        if self.custom_name is not None:
            p(f"Custom name: {self.custom_name!r}")


@Probers.fragments.fragment
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

    def _print_data(self, p):
        super()._print_data(p)
        if 'allprops' in p.flags and self.materials:
            self.materials.print_data(p)


def material_property(matname, colname):
    doc = f"property forwarded to material color {matname!r}/{colname!r}"
    def fget(self):
        frag = self.fragment_by_type(MaterialFragment)
        try:
            return frag.materials[matname][colname]
        except KeyError as e:
            raise AttributeError(f"color {matname!r}/{colname!r}") from e
    def fset(self, value):
        frag = self.fragment_by_type(MaterialFragment)
        frag.materials.get_or_add(matname)[colname] = value
    def fdel(self):
        frag = self.fragment_by_type(MaterialFragment)
        mats = frag.materials
        try:
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
        mats = obj.fragment_by_type(MaterialFragment).materials
        for matname, colname, value in obj.__default_colors.values():
            mats.get_or_add(matname)[colname] = value


# vim:set sw=4 ts=8 sts=4 et:
