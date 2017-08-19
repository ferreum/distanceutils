#!/usr/bin/python
# File:        transform.py
# Description: transform
# Created:     2017-08-19


SIMPLE_SIZE = 64


def convrot(quat):
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


def rtri_to_quat(verts):
    """Converts the given vetices representing a right triangle to a
    transform for a WedgeGS.

    Parameter verts is an array of 3-dimensional vertices of length 3.
    The first entry is the vertex of the right angle."""

    import numpy as np, quaternion
    from numpy import pi, sin, cos, arctan2

    pr, pa, pb = verts
    rot = np.quaternion(1, 0, 0, 0)

    # rotate around y for pb
    vbr = pb - pr
    ay = -arctan2(vbr[2], vbr[0])
    rot *= np.quaternion(cos(ay/2), 0, sin(ay/2), 0)

    # rotate around z for pb
    vbxr = rotpointrev(rot, vbr)
    az = arctan2(vbxr[1], vbxr[0])
    rot *= np.quaternion(cos(az/2), 0, 0, sin(az/2))

    # rotate around x for pa
    vaxr = rotpointrev(rot, pa - pr)
    ax = arctan2(vaxr[2], vaxr[1])
    rot *= np.quaternion(cos(ax/2), sin(ax/2), 0, 0)

    return rot


def rtri_to_transform(verts, srot):

    """Converts the given vetices representing a right triangle to a
    transform for a WedgeGS."""

    import numpy as np, quaternion
    from numpy import pi, sin, cos

    pr, pa, pb = verts
    rot = rtri_to_quat(verts)

    print(" rot", rot)
    print("srot", srot)
    print("diff", rot*srot.conj())
    print("norms", rot.norm(), srot.norm())

    rot = np.quaternion(cos(-pi/4), 0, sin(-pi/4), 0) * rot

    pos = (pb + pa) / 2
    scale = [0, length(pr - pa) / SIMPLE_SIZE, length(pr - pb) / SIMPLE_SIZE]
    return pos, convrot(rot), scale


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
