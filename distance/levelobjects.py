"""Level objects."""


from .bytes import Magic
from .base import Transform, BaseObject, fragment_attrs
from .levelfragments import (
    GroupFragment,
    CustomNameFragment,
)
from .printing import need_counters
from .prober import BytesProber


class Probers(object):
    file = BytesProber()
    level_like = BytesProber()
    level_objects = BytesProber()
    level_subobjects = BytesProber()


class LevelObject(BaseObject):

    __slots__ = ()

    child_prober_name = 'level_subobjects'

    has_children = True

    def _print_children(self, p):
        if 'subobjects' in p.flags and self.children:
            num = len(self.children)
            p(f"Subobjects: {num}")
            with p.tree_children():
                for obj in self.children:
                    p.tree_next_child()
                    p.print_data_of(obj)


class SubObject(LevelObject):

    __slots__ = ()

    def _print_type(self, p):
        container = self.container
        if container and container.magic == Magic[6]:
            type_str = container.type
            p(f"Subobject type: {type_str!r}")


def print_objects(p, gen):
    counters = p.counters
    for obj in gen:
        p.tree_next_child()
        counters.num_objects += 1
        if 'numbers' in p.flags:
            p(f"Level object: {counters.num_objects}")
        p.print_data_of(obj)


@Probers.level_objects.for_type
@fragment_attrs(GroupFragment, **GroupFragment.value_attrs)
@fragment_attrs(CustomNameFragment, **CustomNameFragment.value_attrs)
class Group(LevelObject):

    child_prober_name = 'level_objects'
    is_object_group = True
    type = 'Group'

    default_transform = Transform.fill()

    def _print_children(self, p):
        with need_counters(p) as counters:
            num = len(self.children)
            if num:
                p(f"Grouped objects: {num}")
                if 'groups' in p.flags:
                    p.counters.grouped_objects += num
                    with p.tree_children():
                        print_objects(p, self.children)
            if counters:
                counters.print_data(p)

    def recenter(self, center):
        import numpy as np, quaternion
        from distance.transform import rotpointrev
        quaternion # suppress warning

        pos, rot, scale = self.transform
        self.transform = self.transform.set(pos=center)

        diff = tuple(c - o for c, o in zip(pos, center))
        qrot = np.quaternion(rot[3], *rot[:3])
        diff = rotpointrev(qrot, diff)

        for obj in self.children:
            pos = obj.transform.pos + diff
            obj.transform = obj.transform.set(pos=pos)

    def rerotate(self, rot):
        import numpy as np, quaternion
        from distance.transform import rotpoint
        quaternion # suppress warning

        orot = self.transform.rot
        self.transform = self.transform.set(rot=rot)

        qrot = np.quaternion(rot[3], *rot[:3])
        qorot = np.quaternion(orot[3], *orot[:3])

        diff = qorot / qrot
        for obj in self.children:
            pos, orot, scale = obj.transform
            qorot = diff * np.quaternion(orot[3], *orot[:3])
            nrot = (*qorot.imag, qorot.real)
            if pos:
                pos = rotpoint(diff, pos)
            obj.transform = Transform(pos, nrot, scale)

    def rescale(self, scale):
        import numpy as np

        old = self.transform
        self.transform = old.set(scale=scale)

        inverse = np.array(old.scale) / scale
        invtr = Transform.fill(scale=inverse)
        for obj in self.children:
            obj.transform = invtr.apply(*obj.transform)


Probers.level_like.baseclass = LevelObject
Probers.level_objects.baseclass = LevelObject
Probers.level_subobjects.baseclass = SubObject

# Add everything to level_like and file prober too.
Probers.level_like.extend_from(Probers.level_objects)
Probers.file.extend_from(Probers.level_objects)


# vim:set sw=4 ts=8 sts=4 et:
