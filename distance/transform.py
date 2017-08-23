#!/usr/bin/python
# File:        transform.py
# Description: transform
# Created:     2017-08-19


import numpy as np, quaternion

from .level import WedgeGS


SIMPLE_SIZE = 64

WEDGE_DEF_ROT = np.quaternion(np.cos(np.pi/4), 0, np.sin(np.pi/4), 0)


def convquat(quat):
    return np.array([quat.x, quat.y, quat.z, quat.w])


def length(vec):
    import numpy as np
    return np.linalg.norm(vec)


def normalized(vec):
    import numpy as np
    return vec / np.linalg.norm(vec)


def rotpoint(rot, point):
    import numpy as np
    return (rot * np.quaternion(0, *point) / rot).imag


def rotpointrev(rot, point):
    import numpy as np
    return (rot.conj() * np.quaternion(0, *point) * rot).imag


def vec_angle(va, vb):
    import numpy as np
    ua = normalized(va)
    ub = normalized(vb)
    return np.arccos(np.clip(np.dot(ua, ub), -1.0, 1.0))


def rtri_to_vers(verts):

    """Calculates the versor that aligns the legs of the triangle
    [(0, 0, 0), (0, 0, -1), (0, 1, 0)] with the given right-angled triangle's legs.

    `verts` is an array of 3-dimensional vertices of length 3.
    The first entry is the vertex of the triangle's right angle."""

    import numpy as np, quaternion
    from numpy import pi, sin, cos, arctan2

    pr, pa, pb = verts
    rot = np.quaternion(1, 0, 0, 0)

    # rotate around y for pa
    var = pa - pr
    ay = arctan2(-var[0], -var[2])
    rot *= np.quaternion(cos(ay/2), 0, sin(ay/2), 0)

    # rotate around x for pa
    vaxr = rotpointrev(rot, var)
    ax = arctan2(vaxr[1], -vaxr[2])
    rot *= np.quaternion(cos(ax/2), sin(ax/2), 0, 0)

    # rotate around z for pb
    vbxr = rotpointrev(rot, pb - pr)
    az = arctan2(-vbxr[0], vbxr[1])
    rot *= np.quaternion(cos(az/2), 0, 0, sin(az/2))

    return rot


def rtri_to_transform(verts, srot=None):

    """Converts the given vetices representing a right triangle to a
    transform for a WedgeGS."""

    import numpy as np, quaternion
    from numpy import pi, sin, cos

    pr, pa, pb = verts

    rot = rtri_to_vers(verts)

    pos = (pa + pb) / 2
    scale = [1e-5, length(pr - pb) / SIMPLE_SIZE, length(pr - pa) / SIMPLE_SIZE]
    return pos, convquat(rot), scale


def create_two_wedges(pmax, pnext, plast, objs, simple_args={}):

    """Creates two wedges for an arbitrary triangle.

    pmax - the vertex with the greatest angle
    pnext, plast - the remaining vertices
    objs - the list to put the objects into
    simple_args - args to pass to WedgeGS"""

    import numpy as np
    from numpy import dot

    vnm = pmax - pnext
    vnl = plast - pnext

    vr = dot(vnm, vnl) / length(vnl) * normalized(vnl)
    pr = vr + pnext

    transform = rtri_to_transform(np.array([pr, pmax, pnext]))
    objs.append(WedgeGS(transform=transform, **simple_args))

    transform = rtri_to_transform(np.array([pr, plast, pmax]))
    objs.append(WedgeGS(transform=transform, **simple_args))


def create_single_wedge(pr, pa, pb, objs, simple_args={}):

    """Creates a single wedge for the given right triangle.

    pmax - the vertex with the right angle
    pnext, plast - the remaining vertices
    objs - the list to put the objects into
    simple_args - args to pass to WedgeGS"""

    import numpy as np

    transform = rtri_to_transform(np.array([pr, pa, pb]))
    objs.append(WedgeGS(transform=transform, **simple_args))


def create_triangle_simples(verts, objs, simple_args={}):

    """Creates simples for the given triangle.

    verts - sequence containing the three vertices
    objs - list to put the objects into
    simple_args - args to pass to WedgeGS"""

    import numpy as np
    from numpy import pi

    pa, pb, pc = verts

    ac = abs(vec_angle(pa - pc, pb - pc))
    ab = abs(vec_angle(pa - pb, pc - pb))
    aa = pi - ac - ab

    imax, amax = max(enumerate([aa, ab, ac]), key=lambda e: e[1])

    pmax = verts[imax]
    pnext = verts[(imax + 1) % 3]
    plast = verts[(imax + 2) % 3]

    if -0.001 < abs(amax) - pi/2 < 0.001:
        # very close to right triangle
        create_single_wedge(pmax, pnext, plast, objs, simple_args=simple_args)
    else:
        # any other triangle
        create_two_wedges(pmax, pnext, plast, objs, simple_args=simple_args)

    # objs.append(WedgeGS(
    #     type='SphereGS',
    #     transform=[pr, (), [.7/SIMPLE_SIZE]*3]))


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
