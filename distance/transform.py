#!/usr/bin/python
# File:        transform.py
# Description: transform
# Created:     2017-08-19


SIMPLE_SIZE = 64


def convquat(quat):
    import numpy as np
    return np.array([quat.z, quat.y, -quat.x, quat.w])


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


def rtri_to_vers(verts):

    """Calculates the versor that aligns the legs of the triangle
    [(0, 0, 0), (1, 0, 0), (0, 1, 0)] with the given right-angled triangle's legs.

    `verts` is an array of 3-dimensional vertices of length 3.
    The first entry is the vertex of the triangle's right angle."""

    import numpy as np, quaternion
    from numpy import pi, sin, cos, arctan2

    pr, pa, pb = verts
    rot = np.quaternion(1, 0, 0, 0)

    # rotate around y for pa
    var = pa - pr
    ay = -arctan2(var[2], var[0])
    rot *= np.quaternion(cos(ay/2), 0, sin(ay/2), 0)

    # rotate around z for pa
    vaxr = rotpointrev(rot, var)
    az = arctan2(vaxr[1], vaxr[0])
    rot *= np.quaternion(cos(az/2), 0, 0, sin(az/2))

    # rotate around x for pb
    vbxr = rotpointrev(rot, pb - pr)
    ax = arctan2(vbxr[2], vbxr[1])
    rot *= np.quaternion(cos(ax/2), sin(ax/2), 0, 0)

    print("ax", ax, "ay", ay, "az", az)

    return rot


def rtri_to_transform(verts, srot):

    """Converts the given vetices representing a right triangle to a
    transform for a WedgeGS."""

    import numpy as np, quaternion
    from numpy import pi, sin, cos

    pr, pa, pb = verts
    rot = rtri_to_vers(verts)

    print(" rot", rot)
    print("srot", srot)
    print("diff", rot*srot.conj())
    print("norms", rot.norm(), srot.norm())

    rot = np.quaternion(cos(-pi/4), 0, sin(-pi/4), 0) * rot

    pos = (pa + pb) / 2
    scale = [0, length(pr - pb) / SIMPLE_SIZE, length(pr - pa) / SIMPLE_SIZE]
    return pos, convquat(rot), scale


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
