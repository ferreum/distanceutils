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


class ObjectDefaults(dict):

    def add(self, type, pos=(0, 0, 0), rot=(0, 0, 0, 1), scale=(1, 1, 1)):
        self[type] = pos, rot, scale

    def get_effective(self, obj, transform=None):
        if transform is None:
            transform = obj.transform
        defs = self.get(obj.type, ())
        return transform.effective(*defs)


_OBJ_DEFAULTS = ObjectDefaults()
_defaults = _OBJ_DEFAULTS.add


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

    def _transform_collider(self, main,
                            size=(1, 1, 1),
                            coll_center=(0, 0, 0),
                            offset=(0, 0, 0), scale_factor=1,
                            center_factor=1,
                            locked_scale=False):
        import numpy as np, quaternion
        quaternion # suppress warning
        from distance.transform import rotpoint

        opos, orot, oscale = _OBJ_DEFAULTS.get_effective(main)

        center = (np.array(coll_center) * center_factor + offset) * oscale
        qrot = np.quaternion(orot[3], *orot[:3])
        tpos = np.array(opos) + rotpoint(qrot, center)

        apply_scale = oscale
        if locked_scale:
            apply_scale = max(oscale)
        tscale = np.array(size) * scale_factor * apply_scale

        return tpos, orot, tscale

    def _visualize_spherecollider(self, main, coll,
                                  default_radius=50,
                                  **kw):
        coll_center = coll.trigger_center or (0, 0, 0)
        radius = coll.trigger_radius or default_radius
        transform = self._transform_collider(
            main,
            coll_center=coll_center,
            size=(radius, radius, radius),
            locked_scale=True,
            **kw)
        gs = self._create_gs('SphereHDGS', transform)
        return gs,

    def _visualize_boxcollider(self, main, coll,
                               default_trigger_size=(1, 1, 1),
                               **kw):
        coll_center = coll.trigger_center or (0, 0, 0)
        size = coll.trigger_size or default_trigger_size
        transform = self._transform_collider(
            main,
            coll_center=coll_center,
            size=size,
            **kw)
        gs = self._create_gs('CubeGS', transform)
        return gs,


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
            main, coll, scale_factor=1/32, default_radius=50)

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
            main, coll, offset=(0, 4.817, 0),
            center_factor=(15.972,) * 3,
            scale_factor=.5, default_radius=.5)

VIS_MAPPERS.append(TeleporterMapper())


class VirusSpiritSpawnerMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x3a, 0),
    )

    def __init__(self):
        super().__init__((.878, .184, .184))

    def apply(self, matches):
        main = None
        for objpath, frag in matches:
            main = objpath[0]
        if main is None:
            raise DoNotReplace
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is None:
            raise DoNotReplace
        return self._visualize_spherecollider(
            main, coll,
            scale_factor=1/32,
            default_radius=100)

VIS_MAPPERS.append(VirusSpiritSpawnerMapper())


class EventTriggerMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x89, 2),
    )

    def __init__(self):
        super().__init__((0, .8, 0))

    def apply(self, matches):
        main = None
        for objpath, frag in matches:
            main = objpath[0]
        if main is None:
            raise DoNotReplace
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is not None:
            return self._visualize_spherecollider(
                main, coll,
                scale_factor=1/32,
                default_radius=1)
        coll = main.fragment_by_type(levelfrags.BoxColliderFragment)
        if coll is not None:
            return self._visualize_boxcollider(
                main, coll,
                scale_factor=1/64)

_defaults('EventTriggerBox', scale=(35, 35, 35))
_defaults('EventTriggerSphere', scale=(35, 35, 35))
VIS_MAPPERS.append(EventTriggerMapper())


class EnableAbilitiesTriggerMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x5e, 0),
    )

    def __init__(self):
        super().__init__((.686, .686, .686))

    def apply(self, matches):
        main = None
        for objpath, frag in matches:
            main = objpath[0]
        if main is None:
            raise DoNotReplace
        coll = main.fragment_by_type(levelfrags.BoxColliderFragment)
        if coll is None:
            raise DoNotReplace
        return self._visualize_boxcollider(
            main, coll,
            scale_factor=1/64)

_defaults('EnableAbilitiesBox', scale=(100, 100, 100))
VIS_MAPPERS.append(EnableAbilitiesTriggerMapper())


class ForceZoneMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0xa0, 0),
    )

    def __init__(self):
        super().__init__((.9134, .345, 1))

    def apply(self, matches):
        main = None
        for objpath, frag in matches:
            main = objpath[0]
        if main is None:
            raise DoNotReplace
        coll = main.fragment_by_type(levelfrags.BoxColliderFragment)
        if coll is None:
            raise DoNotReplace
        return self._visualize_boxcollider(
            main, coll,
            scale_factor=1/64)

_defaults('ForceZone', scale=(35, 35, 35))
VIS_MAPPERS.append(ForceZoneMapper())


class WingCorruptionZoneMapper(VisualizeMapper):

    match_sections = (
        Section(MAGIC_2, 0x53, 0),
    )

    def __init__(self):
        super().__init__((.545, .545, 0))

    def apply(self, matches):
        main = None
        for objpath, frag in matches:
            main = objpath[0]
        if main is None:
            raise DoNotReplace
        coll = main.fragment_by_type(levelfrags.BoxColliderFragment)
        if coll is not None:
            return self._visualize_boxcollider(
                main, coll,
                scale_factor=1/64)
        coll = main.fragment_by_type(levelfrags.SphereColliderFragment)
        if coll is not None:
            return self._visualize_spherecollider(
                main, coll,
                scale_factor=1/32,
                default_radius=.5)
        raise DoNotReplace

_defaults('WingCorruptionZone', (100, 100, 100))
_defaults('WingCorruptionZoneLarge', (1000, 1000, 1000))
VIS_MAPPERS.append(WingCorruptionZoneMapper())


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
        pos, rot, scale = _OBJ_DEFAULTS.get_effective(main)
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
                result.extend(self._mappers_by_id[id_].apply(matches))
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
