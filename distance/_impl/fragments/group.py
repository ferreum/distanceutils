

from distance.bytes import Section, Magic
from distance.base import Fragment
from distance.classes import CollectorGroup


Classes = CollectorGroup()


@Classes.fragments.fragment
class GroupFragment(Fragment):

    base_container = Section.base(Magic[2], 0x1d)
    container_versions = 1

    _fields_ = dict(
        inspect_children = None,
    )

    _has_more_data = False

    def _init_defaults(self):
        super()._init_defaults()
        for name, value in self._fields_.items():
            setattr(self, name, value)

    def _read_section_data(self, dbytes, sec):
        if sec.content_size < 12:
            self.inspect_children = None
        else:
            dbytes.require_equal_uint4(Magic[1])
            num_values = dbytes.read_uint()
            self.inspect_children = dbytes.read_uint()
            # do save raw_data if there are unexpected values following
            self._has_more_data = num_values > 0

    def _write_section_data(self, dbytes, sec):
        if not self._has_more_data:
            if self.inspect_children is not None:
                dbytes.write_uint(Magic[1])
                dbytes.write_uint(0) # num values
                dbytes.write_uint(self.inspect_children)
        else:
            dbytes.write_bytes(self.raw_data)


@Classes.fragments.fragment
class CustomNameFragment(Fragment):

    base_container = Section.base(Magic[2], 0x63)
    container_versions = 0

    _fields_ = dict(custom_name=None)

    is_interesting = True

    custom_name = None

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            self.custom_name = dbytes.read_str()

    def _write_section_data(self, dbytes, sec):
        if self.custom_name is not None:
            dbytes.write_str(self.custom_name)

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if self.custom_name is not None:
            p(f"Custom name: {self.custom_name!r}")


# vim:set sw=4 et:
