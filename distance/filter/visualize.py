"""Filter for replacing old simples with golden simples"""


from collections import defaultdict

from distance.levelobjects import GoldenSimple, Group
from distance import levelfragments as levelfrags
from distance.bytes import Section, MAGIC_2
from distance.base import Transform
from .base import ObjectFilter, DoNotReplace


VIS_MAPPERS = []

COPY_FRAG_TYPES = (
    levelfrags.AnimatorFragment,
    levelfrags.EventListenerFragment,
)


class SimpleCreator(object):

    defaults = {}

    def __init__(self, type, *, transform=Transform(), **options):
        self.transform = transform
        options['type'] = type
        options.update({k: v for k, v in self.defaults.items()
                        if k not in options})
        self.options = options

    def create(self, transform, **kw):
        options = self.options
        if kw:
            options = dict(options)
            options.update(kw)
        if self.transform:
            transform = transform.apply(*self.transform)
        return GoldenSimple(transform=transform, **options)


class HoloSimpleCreator(SimpleCreator):

    defaults = dict(
        emit_index = 7,
        tex_scale = (12, 12, 12),
        invert_emit = True,
        additive_transp = True,
        disable_reflect = True,
        disable_collision = True,
    )

    def __init__(self, type, color, **kw):
        if len(color) == 3:
            color = color + (.03,)
        kw['mat_emit'] = color
        super().__init__(type, **kw)


class DecoSimpleCreator(SimpleCreator):

    defaults = dict(
        image_index = 17,
        emit_index = 17,
        mat_spec = (0, 0, 0, 0),
        invert_emit = True,
        disable_diffuse = True,
        disable_reflect = True,
        disable_collision = True,
    )

    def __init__(self, type, color, **kw):
        kw['mat_color'] = color + (1,)
        kw['mat_emit'] = color + (.03,)
        super().__init__(type, **kw)


class Visualizer(object):

    default_radius = 1
    offset = (0, 0, 0)
    scale_factor = 1
    center_factor = 1
    locked_scale = False

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

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

        return Transform(tpos, orot, tscale)


class BoxVisualizer(Visualizer):

    default_trigger_size = (1, 1, 1)

    def __init__(self, color, **kw):
        super().__init__(**kw)
        self.creator = HoloSimpleCreator('CubeGS', color)

    def transform(self, main, coll):
        coll_center = coll.trigger_center or (0, 0, 0)
        size = coll.trigger_size or self.default_trigger_size
        return self._transform_collider(
            main,
            coll_center=coll_center,
            size=size)

    def visualize(self, main, coll):
        transform = self.transform(main, coll)
        gs = self.creator.create(transform)
        return gs,


class SphereVisualizer(Visualizer):

    locked_scale = True
    default_center = (0, 0, 0)

    def __init__(self, color, **kw):
        super().__init__(**kw)
        self.creator = HoloSimpleCreator('SphereHDGS', color)

    def transform(self, main, coll):
        coll_center = coll.trigger_center or self.default_center
        radius = coll.trigger_radius or self.default_radius
        return self._transform_collider(
            main,
            coll_center=coll_center,
            size=(radius, radius, radius))

    def visualize(self, main, coll):
        transform = self.transform(main, coll)
        gs = self.creator.create(transform)
        return gs,


class VisualizeMapper(object):

    def prepare(self, main, matches):
        """First pass, for gathering information"""
        pass

    def post_prepare(self):
        """Called after first pass and before second pass."""
        pass

    def apply(self, main, matches):
        """Second pass, apply filter."""
        return ()


class GravityTriggerMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x45, 0),
        Section(MAGIC_2, 0x45, 1),
    )

    vis = SphereVisualizer(
        color = (.82, .44, 0),
        default_radius = 50,
        scale_factor = 1/32,
    )

    def apply(self, main, matches):
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is None:
            raise DoNotReplace
        return self.vis.visualize(main, coll)

VIS_MAPPERS.append(GravityTriggerMapper)


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

    vis = SphereVisualizer(
        color = (0, .482, 1),
        offset = (0, 4.8, 0),
        center_factor = (16, 16, 16),
        scale_factor = .5,
        default_radius = .5,
    )

    from math import sin, cos, pi

    deco_status = (
        DecoSimpleCreator(
            'TubeGS', (0, 1, .482),
            transform = Transform.fill(scale=(1.71, 0.03, 1.71)),
        ), DecoSimpleCreator(
            'TubeGS', (0, 1, .482),
            transform = Transform.fill(rot=(2**.5/2, 0, 0, 2**.5/2), scale=(1.71, 0.03, 1.71)),
        ), DecoSimpleCreator(
            'TubeGS', (0, 1, .482),
            transform = Transform.fill(rot=(0, 0, 2**.5/2, 2**.5/2), scale=(1.71, 0.03, 1.71)),
        ),
    )

    def __init__(self):
        self._entrances = defaultdict(list)
        self._exits = defaultdict(list)

    def prepare(self, main, matches):
        dest, link_id = None, None
        for objpath, frag in matches:
            if isinstance(frag, levelfrags.TeleporterEntranceFragment):
                if frag.destination is not None:
                    dest = frag.destination
                    self._entrances[dest].append(main)
            elif isinstance(frag, levelfrags.TeleporterExitFragment):
                if frag.link_id is not None:
                    link_id = frag.link_id
                    self._exits[link_id].append(main)
        main.__dest_id = dest
        main.__link_id = link_id

    def post_prepare(self):
        self._entrances = dict(self._entrances)
        self._exits = dict(self._exits)

    def _real_dest(self, main):
        if main is None:
            return None
        dests = self._exits.get(main.__dest_id, ())
        for dest in dests:
            if dest is not main:
                return dest
        # not connected, or teleports to self
        return None

    def apply(self, main, matches):
        tele = matches[0][0][-1]
        coll = tele.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is None:
            if main.type != 'TeleporterExit':
                raise DoNotReplace
            transform = main.effective_transform.apply(
                pos=self.vis.offset, scale=(.25, .25, .25))
        else:
            transform = self.vis.transform(main, coll)

        entrances = self._entrances.get(main.__link_id, ())
        can_exit = any(1 for e in entrances if self._real_dest(e) is main)
        real_dest = self._real_dest(main)
        ddst = self._real_dest(real_dest)
        is_bidi = real_dest is not None and ddst is main

        if real_dest:
            if can_exit:
                if is_bidi:
                    deco_color = (.2, 1, 0)
                else:
                    deco_color = (.4, .4, 1)
            else:
                deco_color = (.7, .7, 0)
        else:
            if can_exit:
                deco_color = (.8, 0, .6)
            else:
                deco_color = (1, 0, 0)

        res = []
        res.append(self.vis.creator.create(transform))
        status_color = (*deco_color, 1)
        status_emit = (*deco_color, .02)
        for deco in self.deco_status:
            res.append(deco.create(transform,
                                   mat_color=status_color,
                                   mat_emit=status_emit))
        return res

VIS_MAPPERS.append(TeleporterMapper)


class VirusSpiritSpawnerMapper(VisualizeMapper):

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

VIS_MAPPERS.append(VirusSpiritSpawnerMapper)


class EventTriggerMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x89, 2),
    )

    color = (0, .4, 0)

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

VIS_MAPPERS.append(EventTriggerMapper)


class EnableAbilitiesTriggerMapper(VisualizeMapper):

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

VIS_MAPPERS.append(EnableAbilitiesTriggerMapper)


class ForceZoneMapper(VisualizeMapper):

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

VIS_MAPPERS.append(ForceZoneMapper)


class WingCorruptionZoneMapper(VisualizeMapper):

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

VIS_MAPPERS.append(WingCorruptionZoneMapper)


class VirusMazeMapper(VisualizeMapper):

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

VIS_MAPPERS.append(VirusMazeMapper)


class VisualizeFilter(ObjectFilter):

    def __init__(self, args):
        super().__init__("vis", args)
        mappers = [cls() for cls in VIS_MAPPERS]
        bysection = defaultdict(list)
        for mapper in mappers:
            for sec in mapper.match_sections:
                bysection[sec.to_key()].append(mapper)
        self._mappers = mappers
        self._mappers_by_sec = dict(bysection)
        self._mappers_by_id = {id(m): m for m in mappers}
        self.num_visualized = 0

    def _create_group(self, main, objs):
        copied_frags = []
        for ty in COPY_FRAG_TYPES:
            copyfrag = main.fragment_by_type(ty)
            if copyfrag is not None:
                copied_frags.append(copyfrag.clone())
        pos, rot, scale = main.effective_transform
        group = Group(children=objs)
        group.recenter(pos)
        group.rerotate(rot)
        group.fragments = list(group.fragments) + copied_frags
        return group

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
        if self.passnum == 0:
            for id_, matches in mappers.items():
                self._mappers_by_id[id_].prepare(obj, matches)
            return obj,
        elif self.passnum == 1:
            result = []
            for id_, matches in mappers.items():
                try:
                    result.extend(self._mappers_by_id[id_].apply(obj, matches))
                    self.num_visualized += 1
                except DoNotReplace:
                    pass
            if result:
                grp = self._create_group(obj, result)
                return obj, grp
            return obj,

    def apply(self, content):
        self.passnum = 0
        super().apply(content)
        for m in self._mappers:
            m.post_prepare()
        self.passnum = 1
        return super().apply(content)

    def print_summary(self, p):
        p(f"Visualized objects: {self.num_visualized}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
