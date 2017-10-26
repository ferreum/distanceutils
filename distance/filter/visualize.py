"""Filter for replacing old simples with golden simples"""


from collections import defaultdict

from distance.levelobjects import GoldenSimple
from distance import levelfragments as levelfrags
from distance.bytes import Section, MAGIC_2
from .base import ObjectFilter, DoNotReplace


VIS_MAPPERS = []


class VisualizeMapper(object):

    def __init__(self, type, color, **kw):
        super().__init__(**kw)
        self.type = type
        self.color = color + (0.03,)

    def _create_gs(self, transform):
        gs = GoldenSimple(type=self.type, transform=transform)
        gs.mat_emit =  self.color
        gs.emit_index = 7
        gs.tex_scale = (12, 12, 12)
        gs.additive_transp = True
        gs.disable_collision = True
        gs.disable_reflect = True
        gs.invert_emit = True
        return gs


class GravityTriggerMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x45, 1),
    )

    def __init__(self):
        super().__init__('SphereGS', (.82, .44, 0))

    def apply(self, matches):
        main = None
        for objpath, frag in matches:
            if isinstance(frag, levelfrags.GravityToggleFragment):
                main = objpath[0]
                break
        if main is None:
            raise DoNotReplace
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        center = coll.trigger_center
        radius = coll.trigger_radius or 50

        pos, rot, scale = main.transform or ((), (), ())
        if not scale:
            scale = (1, 1, 1)
        tpos = pos
        if rot and center and any(-0.01 < v < 0.01 for v in center):
            import numpy as np, quaternion
            quaternion # suppress warning
            from distance.transform import rotpoint
            center = center * np.array(scale or (1, 1, 1))
            qrot = np.quaternion(rot[3], *rot[:3])
            tpos = tuple(np.array(pos or (0, 0, 0)) + rotpoint(qrot, center))
        tscale = tuple(1.575 / 50 * s * radius for s in scale)
        transform = tpos, rot, tscale

        gs = self._create_gs(transform)
        return gs,


VIS_MAPPERS.append(GravityTriggerMapper())


class VisualizeFilter(ObjectFilter):

    def __init__(self, args):
        super().__init__("vis", args)
        bysection = defaultdict(list)
        for mapper in VIS_MAPPERS:
            for sec in mapper.match_sections:
                bysection[sec.to_key()].append(mapper)
        self._mappers_by_sec = dict(bysection)
        self._mappers_by_id = {id(m): m for m in VIS_MAPPERS}
        self.num_visualized = 0

    def _match_object(self, objpath):
        def filter_frags(sec, prober):
            return sec.to_key() in self._mappers_by_sec
        mappers = defaultdict(list)
        obj = objpath[-1]
        for frag in obj.filtered_fragments(filter_frags):
            for mapper in self._mappers_by_sec[frag.container.to_key()]:
                mappers[id(mapper)].append((objpath, frag))
        if not obj.is_object_group:
            for c in obj.children:
                mappers.update(self._match_object(objpath + (c,)))
        return mappers

    def filter_object(self, obj):
        mappers = self._match_object((obj,))
        result = [obj]
        for id_, matches in mappers.items():
            try:
                result.extend(self._mappers_by_id[id_].apply(matches))
                self.num_visualized += 1
            except DoNotReplace:
                pass
        return result

    def print_summary(self, p):
        p(f"Visualized objects: {self.num_visualized}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
