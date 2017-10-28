"""Filter for replacing old simples with golden simples"""


from collections import defaultdict

from distance.levelobjects import GoldenSimple, Group
from distance import levelfragments as levelfrags
from distance.bytes import Section, MAGIC_2
from .base import ObjectFilter, DoNotReplace


VIS_MAPPERS = []

COPY_FRAG_TYPES = (
    levelfrags.AnimatorFragment,
    levelfrags.EventListenerFragment,
)


class Visualizer(object):

    default_radius = 1
    offset = (0, 0, 0)
    scale_factor = 1
    center_factor = 1
    locked_scale = False

    def __init__(self, color, **kw):
        self.color = color + (0.03,)
        for k, v in kw.items():
            setattr(self, k, v)

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

    def _transform_collider(self, main, size=(1, 1, 1), coll_center=(0, 0, 0)):
        import numpy as np, quaternion
        quaternion # suppress warning
        from distance.transform import rotpoint

        opos, orot, oscale = main.effective_transform

        center = (np.array(coll_center) * self.center_factor + self.offset) * oscale
        qrot = np.quaternion(orot[3], *orot[:3])
        tpos = np.array(opos) + rotpoint(qrot, center)

        apply_scale = oscale
        if self.locked_scale:
            apply_scale = max(oscale)
        tscale = np.array(size) * self.scale_factor * apply_scale

        return tpos, orot, tscale


class BoxVisualizer(Visualizer):

    default_trigger_size = (1, 1, 1)

    def transform(self, main, coll):
        coll_center = coll.trigger_center or (0, 0, 0)
        size = coll.trigger_size or self.default_trigger_size
        return self._transform_collider(
            main,
            coll_center=coll_center,
            size=size)

    def visualize(self, main, coll):
        transform = self.transform(main, coll)
        gs = self._create_gs('CubeGS', transform)
        return gs,


class SphereVisualizer(Visualizer):

    locked_scale = True
    default_center = (0, 0, 0)

    def transform(self, main, coll):
        coll_center = coll.trigger_center or self.default_center
        radius = coll.trigger_radius or self.default_radius
        return self._transform_collider(
            main,
            coll_center=coll_center,
            size=(radius, radius, radius))

    def visualize(self, main, coll):
        transform = self.transform(main, coll)
        gs = self._create_gs('SphereHDGS', transform)
        return gs,


class GravityTriggerMapper(object):

    match_sections = (
        Section(MAGIC_2, 0x45, 1),
    )

    vis = SphereVisualizer(
        color = (.82, .44, 0),
        default_radius = 50,
        scale_factor = 1/32,
    )

    def apply(self, main, matches):
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        return self.vis.visualize(main, coll)

VIS_MAPPERS.append(GravityTriggerMapper())


class TeleporterMapper(object):

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

    vis = SphereVisualizer(
        color = (0, .482, 1),
        offset = (0, 4.817, 0),
        center_factor = (15.972,) * 3,
        scale_factor = .5,
        default_radius = .5,
    )

    def apply(self, main, matches):
        exit = None
        for objpath, frag in matches:
            if isinstance(frag, levelfrags.TeleporterEntranceFragment):
                tele = objpath[-1]
                entrance = frag
            elif isinstance(frag, levelfrags.TeleporterExitFragment):
                tele = objpath[-1]
                exit = frag
        if tele is None:
            raise DoNotReplace
        coll = tele.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is None:
            raise DoNotReplace
        return self.vis.visualize(main, coll)

VIS_MAPPERS.append(TeleporterMapper())


class VirusSpiritSpawnerMapper(object):

    match_sections = (
        Section(MAGIC_2, 0x3a, 0),
    )

    vis = SphereVisualizer(
        color = (.878, .184, .184),
        scale_factor = 1/32,
        default_radius = 100,
    )

    def apply(self, main, matches):
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is None:
            raise DoNotReplace
        return self.vis.visualize(main, coll)

VIS_MAPPERS.append(VirusSpiritSpawnerMapper())


class EventTriggerMapper(object):

    match_sections = (
        Section(MAGIC_2, 0x89, 2),
    )

    color = (0, .8, 0)

    vis_box = BoxVisualizer(color, scale_factor=1/64)
    vis_sphere = SphereVisualizer(color, scale_factor=1/32)

    def apply(self, main, matches):
        coll = main.fragment_by_type(levelfrags.BoxColliderFragment)
        if coll is not None:
            return self.vis_box.visualize(main, coll)
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is not None:
            return self.vis_sphere.visualize(main, coll)
        raise DoNotReplace

VIS_MAPPERS.append(EventTriggerMapper())


class EnableAbilitiesTriggerMapper(object):

    match_sections = (
        Section(MAGIC_2, 0x5e, 0),
    )

    vis = BoxVisualizer(
        color = (.686, .686, .686),
        scale_factor = 1/64,
    )

    def apply(self, main, matches):
        coll = main.fragment_by_type(levelfrags.BoxColliderFragment)
        if coll is None:
            raise DoNotReplace
        return self.vis.visualize(main, coll)

VIS_MAPPERS.append(EnableAbilitiesTriggerMapper())


class ForceZoneMapper(object):

    match_sections = (
        Section(MAGIC_2, 0xa0, 0),
    )

    vis = BoxVisualizer(
        color = (.9134, .345, 1),
        scale_factor = 1/64,
    )

    def apply(self, main, matches):
        coll = main.fragment_by_type(levelfrags.BoxColliderFragment)
        if coll is None:
            raise DoNotReplace
        return self.vis.visualize(main, coll)

VIS_MAPPERS.append(ForceZoneMapper())


class WingCorruptionZoneMapper(object):

    match_sections = (
        Section(MAGIC_2, 0x53, 0),
    )

    vis_box = BoxVisualizer(
        color = (.545, .545, 0),
        scale_factor = 1/64,
    )

    vis_sphere = SphereVisualizer(
        color = (.545, .545, 0),
        scale_factor = 1/32,
        default_radius = .5,
    )

    def apply(self, main, matches):
        coll = main.fragment_by_type(levelfrags.BoxColliderFragment)
        if coll is not None:
            return self.vis_box.visualize(main, coll)
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is not None:
            return self.vis_sphere.visualize(main, coll)
        raise DoNotReplace

VIS_MAPPERS.append(WingCorruptionZoneMapper())


class VirusMazeMapper(object):

    match_sections = (
        Section(MAGIC_2, 0x43, 0),
        Section(MAGIC_2, 0x43, 1),
        Section(MAGIC_2, 0x43, 2),
    )

    _opts = dict(
        color = (.355, .077, 0),
        scale_factor = 1/32,
    )
    _vis_ceiling = SphereVisualizer(
        default_radius = 66.591,
        **_opts,
    )
    _vis_tower = SphereVisualizer(
        default_center = (.107, .593, 63.197),
        default_radius = 176.755,
        **_opts,
    )

    visualizers = {
        'VirusMazeCeiling001': _vis_ceiling,
        'VirusMazeTowerFat': _vis_tower,
        'VirusMazeTowerFat002': _vis_tower,
        'VirusMazeTowerFat003': _vis_tower,
    }

    def apply(self, main, matches):
        interp_frag = main.fragment_by_type(levelfrags.BaseInterpolateToPositiononTrigger)
        if interp_frag and not interp_frag.actually_interpolate:
            raise DoNotReplace
        vis = self.visualizers.get(main.type, None)
        if vis is None:
            raise DoNotReplace
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is not None:
            return vis.visualize(main, coll)
        raise DoNotReplace

VIS_MAPPERS.append(VirusMazeMapper())


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

    def _apply_animators(self, main, objs):
        copied_frags = []
        for ty in COPY_FRAG_TYPES:
            copyfrag = main.fragment_by_type(ty)
            if copyfrag is not None:
                copied_frags.append(copyfrag.clone())
        if not copied_frags:
            return objs
        pos, rot, scale = main.effective_transform
        group = Group(children=objs)
        group.recenter(pos)
        group.rerotate(rot)
        group_frags = list(group.fragments)
        group_frags.extend(copied_frags)
        group.fragments = group_frags
        return group,

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
        result = []
        for id_, matches in mappers.items():
            try:
                result.extend(self._mappers_by_id[id_].apply(obj, matches))
                self.num_visualized += 1
            except DoNotReplace:
                pass
        if result:
            result = self._apply_animators(obj, result)
            return (obj, *result)
        return obj,

    def print_summary(self, p):
        p(f"Visualized objects: {self.num_visualized}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
