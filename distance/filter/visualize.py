"""Filter for replacing old simples with golden simples"""


from collections import defaultdict

from distance.levelobjects import GoldenSimple, Group
from distance import levelfragments as levelfrags
from distance.bytes import Section, MAGIC_2
from .base import ObjectFilter, DoNotReplace


VIS_MAPPERS = []


class VisualizeMapper(object):

    def __init__(self, color, **kw):
        super().__init__(**kw)
        self.color = color + (0.03,)

    def _create_gs(self, type, transform):
        gs = GoldenSimple(type=type, transform=transform)
        gs.mat_emit =  self.color
        gs.emit_index = 7
        gs.tex_scale = (12, 12, 12)
        gs.additive_transp = True
        gs.disable_collision = True
        gs.disable_reflect = True
        gs.invert_emit = True
        return gs

    def _visualize_spherecollider(self, main, coll,
                                  offset=(0, 0, 0), scale_factor=1,
                                  center_factor=1,
                                  default_center=(0, 0, 0),
                                  default_radius=50):
        coll_center = coll.trigger_center or default_center
        radius = coll.trigger_radius or default_radius

        pos, rot, scale = main.transform or ((), (), ())
        if not scale:
            scale = (1, 1, 1)
        tpos = pos

        import numpy as np, quaternion
        quaternion # suppress warning
        from distance.transform import rotpoint
        rel_center = np.array(coll_center) * center_factor + offset
        center = (scale or (1, 1, 1)) * rel_center
        if rot:
            qrot = np.quaternion(rot[3], *rot[:3])
        else:
            qrot = np.quaternion(1, 0, 0, 0)
        tpos = tuple(np.array(pos or (0, 0, 0)) + rotpoint(qrot, center))
        tscale = (scale_factor * max(scale) * radius,) * 3
        transform = tpos, (0, 0, 0, 1), tscale

        gs = self._create_gs('SphereHDGS', transform)
        group = Group(children=[gs])
        if pos:
            group.recenter(pos)
            group.transform = group.transform[0], rot, ()
        anim = main.fragment_by_type(levelfrags.AnimatorFragment)
        if anim is not None:
            frags = list(group.fragments)
            anim_copy = levelfrags.AnimatorFragment(raw_data=anim.raw_data, container=Section(anim.container))
            frags.append(anim_copy)
            group.fragments = frags
        return group,


class GravityTriggerMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x45, 1),
    )

    def __init__(self):
        super().__init__((.82, .44, 0))

    def apply(self, matches):
        main = None
        for objpath, frag in matches:
            if isinstance(frag, levelfrags.GravityToggleFragment):
                main = objpath[0]
                break
        if main is None:
            raise DoNotReplace
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        return self._visualize_spherecollider(
            main, coll, scale_factor=.03126, default_radius=50)

VIS_MAPPERS.append(GravityTriggerMapper())


class TeleporterMapper(VisualizeMapper):

    match_sections = (
        # tele entrance
        Section(MAGIC_2, 0x3e, 0),
        Section(MAGIC_2, 0x3e, 1),
        Section(MAGIC_2, 0x3e, 2),
        Section(MAGIC_2, 0x3e, 3),
        # tele exit
        Section(MAGIC_2, 0x3f, 0),
        Section(MAGIC_2, 0x3f, 1),
    )

    def __init__(self):
        super().__init__((0, .482, 1))

    def apply(self, matches):
        main = None
        exit = None
        for objpath, frag in matches:
            if isinstance(frag, levelfrags.TeleporterEntranceFragment):
                main = objpath[0]
                tele = objpath[-1]
                entrance = frag
            elif isinstance(frag, levelfrags.TeleporterExitFragment):
                main = objpath[0]
                tele = objpath[-1]
                exit = frag
        if main is None or tele is None:
            raise DoNotReplace
        coll = tele.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is None:
            raise DoNotReplace
        return self._visualize_spherecollider(
            main, coll, offset=(0, 4.817, 0), center_factor=(15.972,) * 3, scale_factor=.5, default_radius=.5)

VIS_MAPPERS.append(TeleporterMapper())


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
