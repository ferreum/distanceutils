"""Base classes for filters."""


import collections

from distance.level import Level
from distance.levelobjects import Group


class ObjectFilter(object):

    @classmethod
    def add_args(cls, parser):
        parser.add_argument("--maxrecurse", type=int, default=-1,
                            help="Maximum of recursions.")

    def __init__(self, name, args):
        self.name = name
        self.maxrecurse = args.maxrecurse

    def filter_object(self, obj):
        return obj,

    def filter_group(self, grp, levels, **kw):
        orig_empty = not grp.children
        grp.children = self.filter_objects(grp.children, levels, **kw)
        if not orig_empty and not grp.children:
            # remove empty group
            return ()
        return grp,

    def filter_any_object(self, obj, levels, **kw):
        if obj.is_object_group:
            if levels == 0:
                return obj,
            return self.filter_group(obj, levels - 1, **kw)
        else:
            return self.filter_object(obj, **kw)

    def filter_objects(self, objects, levels, **kw):
        res = []
        for obj in objects:
            res.extend(self.filter_any_object(obj, levels, **kw))
        return res

    def apply_level(self, level):
        for layer in level.layers:
            layer.objects = self.filter_objects(layer.objects, self.maxrecurse)

    def apply_group(self, grp):
        # not using filter_group, because we never want to remove the root
        # group object
        grp.children = self.filter_objects(grp.children, self.maxrecurse)

    def apply(self, content):
        if isinstance(content, Level):
            self.apply_level(content)
        elif isinstance(content, Group):
            self.apply_group(content)
        else:
            raise TypeError(f'Unknown object type: {type(content).__name__!r}')

    def post_filter(self, content):
        return True

    def print_summary(self, p):
        pass


class DoNotReplace(Exception):

    def __init__(self, reason=None, *args, **kw):
        super().__init__(*args, **kw)
        self.reason = reason


class ObjectMapper(object):

    def __init__(self, offset=None, rotate=None, size_factor=1,
                 locked_scale_axes=(),
                 default_rotation=(1, 0, 0, 0),
                 default_scale=(1, 1, 1)):
        if not callable(size_factor):
            if isinstance(size_factor, collections.Sequence):
                def size_factor(scale, factor=size_factor):
                    return tuple(s * f for s, f in zip(scale, factor))
            else:
                def size_factor(scale, factor=size_factor):
                    return tuple(s * factor for s in scale)
        self.offset = offset
        self.rotate = rotate
        self.size_factor = size_factor
        self.locked_scale_axes = locked_scale_axes
        self.default_rotation = default_rotation
        self.default_scale = default_scale

    def _apply_transform(self, transform):
        pos, rot, scale = transform or ((), (), ())

        if not scale:
            scale = self.default_scale

        if self.locked_scale_axes:
            if scaled_group:
                raise DoNotReplace('locked_scale_group')
            from math import isclose
            v1 = scale[self.locked_scale_axes[0]]
            for i in self.locked_scale_axes[1:]:
                if not isclose(scale[i], v1):
                    # Rotated object cannot scale these axes independently.
                    raise DoNotReplace('locked_scale')

        if self.offset or self.rotate:
            import numpy as np, quaternion
            quaternion # suppress warning
            if not rot:
                qrot = np.quaternion(*self.default_rotation)
            else:
                qrot = np.quaternion(rot[3], *rot[0:3])

        if self.offset:
            from distance.transform import rotpoint
            if not pos:
                pos = (0, 0, 0)
            soffset = tuple(o * s for o, s in zip(self.offset, scale))
            rsoffset = rotpoint(qrot, soffset)
            pos = tuple(p + o for p, o in zip(pos, rsoffset))

        if self.rotate:
            qrot *= np.quaternion(*self.rotate)
            rot = (*qrot.imag, qrot.real)

        scale = self.size_factor(scale)

        return pos, rot, scale

    def apply(self, obj, scaled_group=False, **kw):
        transform = self._apply_transform(obj.transform)

        return self.create_result(obj, transform, **kw)

    def create_result(self, old, transform):
        raise NotImplementedError


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
