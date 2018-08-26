

from distance.bytes import Magic, Section
from distance.base import Fragment
from distance.constants import LAYER_FLAG_NAMES
from distance.printing import need_counters, print_objects
from distance.classes import CollectorGroup


Classes = CollectorGroup()


def format_layer_flags(gen):
    for flag, names in gen:
        name = names.get(flag, f"Unknown({flag})")
        if name:
            yield name


@Classes.level_content.fragment
class Layer(Fragment):

    class_tag = 'Layer'
    default_container = Section(Magic[7])

    layer_name = None
    layer_flags = (0, 0, 0)
    objects = ()
    has_layer_flags = True
    flags_version = 1
    unknown_flag = 0

    def _read_section_data(self, dbytes, sec):
        if sec.magic != Magic[7]:
            raise ValueError(f"Invalid layer section: {sec.magic}")
        self.layer_name = sec.name

        if sec.content_size < 4:
            # Happens with empty old layer sections, this prevents error
            # with empty layer at end of file.
            self.has_layer_flags = False
            return
        version = dbytes.read_uint()
        if version in (0, 1):
            self.flags_version = version
            flags = dbytes.read_bytes(3)
            if version == 0:
                frozen = 1 if flags[0] == 0 else 0
                self.layer_flags = (flags[1], frozen, flags[2])
            else:
                self.layer_flags = flags
                self.unknown_flag = dbytes.read_byte()
            obj_start = dbytes.tell()
        else:
            self.has_layer_flags = False
            obj_start = sec.content_start
        self.objects = self.classes.level_objects.lazy_n_maybe(
            dbytes, sec.count, start_pos=obj_start)

    def _write_section_data(self, dbytes, sec):
        if sec.magic != Magic[7]:
            raise ValueError(f"Invalid layer section: {sec.magic}")
        if self.has_layer_flags:
            flags = self.layer_flags
            dbytes.write_uint(self.flags_version)
            if self.flags_version == 0:
                flags_bytes = [0 if flags[1] else 1, flags[0], flags[2]]
            else:
                flags_bytes = [flags[0], flags[1], flags[2], self.unknown_flag]
            dbytes.write_bytes(bytes(flags_bytes))
        for obj in self.objects:
            obj.write(dbytes)

    def _repr_detail(self):
        supstr = super()._repr_detail()
        return f" {self.layer_name!r}{supstr}"

    def _print_type(self, p):
        p(f"Layer: {self.layer_name!r}")

    def visit_print(self, p):
        with need_counters(p) as counters:
            yield super().visit_print(p)
            if counters:
                counters.print(p)

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        p(f"Layer object count: {len(self.objects)}")
        if self.layer_flags:
            flag_str = ', '.join(
                format_layer_flags(zip(self.layer_flags, LAYER_FLAG_NAMES)))
            if not flag_str:
                flag_str = "None"
            p(f"Layer flags: {flag_str}")
        p.counters.num_layers += 1
        p.counters.layer_objects += len(self.objects)

    def _visit_print_children(self, p):
        yield super()._visit_print_children(p)
        yield print_objects(p, self.objects)


# vim:set sw=4 et:
