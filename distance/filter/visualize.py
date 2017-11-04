"""Filter for visualizing invisible things"""


from collections import defaultdict
import math

from distance.levelobjects import GoldenSimple, Group
from distance import levelfragments as levelfrags
from distance.bytes import Section, MAGIC_2
from distance.base import Transform, NoDefaultTransformError
from .base import ObjectFilter, DoNotApply, create_replacement_group

SKIP_REASON_LABELS = {
    'no_collider': "No collider found",
    'no_visualizer': "No visualizer for type",
    'disabled': "Trigger disabled",
    'no_default_transform': "Unknown default transform",
}

VIS_MAPPERS = []


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
        tex_offset = (0.003, -0.003, 0),
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

        try:
            opos, orot, oscale = main.transform
        except NoDefaultTransformError:
            raise DoNotApply('no_default_transform')

        center = (np.array(coll_center) * self.center_factor + self.offset) * oscale
        qrot = np.quaternion(orot[3], *orot[:3])
        tpos = np.array(opos) + rotpoint(qrot, center)

        apply_scale = oscale
        if self.locked_scale:
            apply_scale = max(oscale)
        tscale = np.array(size) * self.scale_factor * apply_scale

        return Transform(tpos, orot, tscale)


class BoxVisualizer(Visualizer):

    default_center = (0, 0, 0)
    default_size = (1, 1, 1)

    def __init__(self, color, **kw):
        super().__init__(**kw)
        self.creator = HoloSimpleCreator('CubeGS', color)

    def transform(self, main, obj):
        coll = obj.fragment_by_type(levelfrags.BoxColliderFragment)
        if coll is None:
            raise DoNotApply('no_collider')
        coll_center = coll.trigger_center or self.default_center
        size = coll.trigger_size or self.default_size
        return self._transform_collider(
            main,
            coll_center=coll_center,
            size=size)

    def visualize(self, main, obj):
        transform = self.transform(main, obj)
        gs = self.creator.create(transform)
        return gs,


class SphereVisualizer(Visualizer):

    locked_scale = True
    default_center = (0, 0, 0)

    def __init__(self, color, **kw):
        super().__init__(**kw)
        self.creator = HoloSimpleCreator('SphereHDGS', color)

    def transform(self, main, obj):
        coll = obj.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is None:
            raise DoNotApply('no_collider')
        coll_center = coll.trigger_center or self.default_center
        radius = coll.trigger_radius or self.default_radius
        return self._transform_collider(
            main,
            coll_center=coll_center,
            size=(radius, radius, radius))

    def visualize(self, main, obj):
        transform = self.transform(main, obj)
        gs = self.creator.create(transform)
        return gs,


class VisualizeMapper(object):

    match_sections = ()
    match_types = ()
    match_subtypes = ()

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
        return self.vis.visualize(main, main)

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
        if main.type == 'TeleporterExit':
            transform = main.transform.apply(
                pos=self.vis.offset, scale=(.25, .25, .25))
        else:
            transform = self.vis.transform(main, tele)

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
        return self.vis.visualize(main, main)

VIS_MAPPERS.append(VirusSpiritSpawnerMapper)


class EventTriggerMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x89, 2),
    )

    color = (0, .4, 0)

    vis_box = BoxVisualizer(color, scale_factor=1/64)
    vis_sphere = SphereVisualizer(color, scale_factor=1/32)

    def apply(self, main, matches):
        try:
            return self.vis_box.visualize(main, main)
        except DoNotApply as e:
            if e.reason != 'no_collider':
                raise
            return self.vis_sphere.visualize(main, main)

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
        return self.vis.visualize(main, main)

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
        return self.vis.visualize(main, main)

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
        try:
            return self.vis_box.visualize(main, main)
        except DoNotApply as e:
            if e.reason != 'no_collider':
                raise
            return self.vis_sphere.visualize(main, main)

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
            raise DoNotApply('disabled')
        vis = self.visualizers.get(main.type, None)
        if vis is None:
            raise DoNotApply('no_visualizer')
        return vis.visualize(main, main)

VIS_MAPPERS.append(VirusMazeMapper)


class CheckpointMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x19, 1),
    )

    _opts = dict(
        color = (0, .733, .498),
        scale_factor = 1/64,
    )

    vis = BoxVisualizer(
        **_opts,
        default_center = (0, 1.25, 0),
        default_size = (5, 3.5, .5),
    )
    vis_for_type = {
        'EmpireCheckpoint': BoxVisualizer(
            **_opts,
            default_size = (5, 6, .5),
        ),
        'AbilityCheckpoint': BoxVisualizer(
            **_opts,
            default_center = (-2, 0, 3.6),
            default_size = (90, 90, .5),
        ),
        'NitronicCheckpoint': BoxVisualizer(
            **_opts,
            default_center = (0, 5.81, 0),
            default_size = (38.36, 21.0, 6.746),
        )
    }

    def apply(self, main, matches):
        obj = matches[0][0][-1]
        vis = self.vis_for_type.get(main.type, self.vis)
        return vis.visualize(main, obj)


VIS_MAPPERS.append(CheckpointMapper)


class CooldownTriggerMapper(VisualizeMapper):

    match_types = ('CooldownTriggerNoVisual',)
    match_subtypes = ('CooldownLogic', 'FlyingRingLogic',)

    vis = BoxVisualizer(
        color = (.15, .45, .45),
        default_size = (50, 50, 40),
        scale_factor = 1/64,
    )

    def _apply_ring_anim(self, main, objs):
        rotLogic = main.fragment_by_type(levelfrags.RigidbodyAxisRotationLogicFragment)
        if rotLogic is None:
            # object is not a rotating ring
            return objs

        spd = rotLogic.angular_speed
        if spd is None:
            spd = 30

        axis = rotLogic.rotation_axis
        if axis is None:
            axis = 2

        if -0.0001 < spd < 0.0001:
            # static ring
            return objs

        grp = Group(children=objs)
        grp.recenter(main.transform.pos)
        grp.rerotate(main.transform.rot)

        anim = levelfrags.AnimatorFragment()
        anim.motion_mode = 5 # advanced

        if rotLogic.limit_rotation:
            bounds = rotLogic.rotation_bounds
            bounds_rad = math.radians(bounds)

            if spd < 0:
                bounds = -bounds
                bounds_rad = -bounds_rad

            rot = [0, 0, 0, -math.cos(bounds_rad / 2)]
            rot[axis % 3] = math.sin(bounds_rad / 2)
            grp.transform = grp.transform.apply(rot=rot)

            # the game calculates the duration without bounds
            anim.duration = 180 / abs(spd)
            anim.time_offset = 90 / abs(spd)
            anim.extrapolation_type = 1 # pingpong
            anim.rotate_magnitude = bounds * 2
            anim.curve_type = 6 # sin wave
        else:
            start_offset = rotLogic.starting_angle_offset or 0
            anim.time_offset = start_offset / spd
            anim.rotate_magnitude = 360 if spd > 0 else -360
            anim.duration = 360 / abs(spd)
            anim.extrapolation_type = 2 # extend
            anim.curve_type = 0 # linear
        anim.do_loop = 1
        anim.delay = 0
        axis_vec = [0, 0, 0]
        axis_vec[axis % 3] = 1
        anim.rotate_axis = axis_vec
        grp.fragments = list(grp.fragments) + [anim]
        return grp,

    def apply(self, main, matches):
        obj = matches[0][0][-1]
        res = self.vis.visualize(main, obj)
        res = self._apply_ring_anim(main, res)
        return res

VIS_MAPPERS.append(CooldownTriggerMapper)


class PlanetWithSphericalGravityMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x5f, 0),
        Section(MAGIC_2, 0x5f, 1),
    )

    vis = SphereVisualizer(
        color = (.341, 0, .694),
        default_radius = 200,
        scale_factor = 1/32,
    )

    def apply(self, main, matches):
        return self.vis.visualize(main, main)

VIS_MAPPERS.append(PlanetWithSphericalGravityMapper)


class VisualizeFilter(ObjectFilter):

    @classmethod
    def add_args(cls, parser):
        super().add_args(parser)
        parser.add_argument('--verbose', action='store_true',
                            help="Print list of skipped objects.")

    def __init__(self, args):
        super().__init__(args)
        self.verbose = args.verbose
        mappers = [cls() for cls in VIS_MAPPERS]
        bysection = defaultdict(list)
        bytype = defaultdict(list)
        bysubtype = defaultdict(list)
        for mapper in mappers:
            for sec in mapper.match_sections:
                bysection[sec.to_key()].append(mapper)
            for type in mapper.match_types:
                bytype[type].append(mapper)
            for subtype in mapper.match_subtypes:
                bysubtype[subtype].append(mapper)
        self._mappers = mappers
        self._mappers_by_sec = dict(bysection)
        self._mappers_by_type = dict(bytype)
        self._mappers_by_subtype = dict(bysubtype)
        self._mappers_by_id = {id(m): m for m in mappers}
        self.num_visualized = 0
        self._num_skipped = 0
        self._skipped_by_reason = defaultdict(list)

    def _match_object(self, objpath):
        def filter_frags(sec, prober):
            return sec.to_key() in self._mappers_by_sec
        mappers = defaultdict(list)
        if len(objpath) == 1:
            bytype = self._mappers_by_type
        else:
            bytype = self._mappers_by_subtype
        for mapper in bytype.get(objpath[-1].type, ()):
            mappers[id(mapper)].append((objpath, None))
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
                except DoNotApply as e:
                    self._num_skipped += 1
                    self._skipped_by_reason[e.reason].append((obj, e))
            if result:
                grp = create_replacement_group(obj, result)
                return (obj, *grp)
            return obj,

    def apply(self, content):
        self.passnum = 0
        super().apply(content)
        for m in self._mappers:
            m.post_prepare()
        self.passnum = 1
        return super().apply(content)

    def _print_objects(self, p, objs):
        with p.tree_children():
            for obj, exc in objs:
                p.tree_next_child()
                p(f"Object: {obj.type!r} at 0x{obj.start_pos:08x}")

    def _print_skipped(self, p):
        p(f"Skipped objects: {self._num_skipped}")
        with p.tree_children():
            for reason, objs in sorted(self._skipped_by_reason.items()):
                p.tree_next_child()
                label = SKIP_REASON_LABELS.get(reason, reason)
                p(f"{label}: {len(objs)}")
                if self.verbose:
                    self._print_objects(p, objs)

    def print_summary(self, p):
        p(f"Visualized objects: {self.num_visualized}")
        if self._num_skipped:
            self._print_skipped(p)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
