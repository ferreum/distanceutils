

from distance.levelobjects import LevelObject
from distance.classes import CollectorGroup, DefaultClasses
from distance.base import Transform
from distance.printing import need_counters, print_objects


Classes = CollectorGroup()


@Classes.level_objects.object
@Classes.common.object
@DefaultClasses.fragments.fragment_attrs('Group', 'CustomName')
class Group(LevelObject):

    child_classes_name = 'level_objects'
    is_object_group = True
    type = 'Group'

    default_transform = Transform.fill()

    def _visit_print_children(self, p):
        with need_counters(p) as counters:
            num = len(self.children)
            if num:
                p(f"Grouped objects: {num}")
                if 'groups' in p.flags:
                    p.counters.grouped_objects += num
                    yield print_objects(p, self.children)
            if counters:
                counters.print(p)

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


# vim:set sw=4 et:
