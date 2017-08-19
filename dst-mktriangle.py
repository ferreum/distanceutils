#!/usr/bin/python
# File:        dst-mktriangle.py
# Description: dst-mktriangle
# Created:     2017-08-16


import sys
import argparse
import traceback
import itertools

from distance.bytes import DstBytes, PrintContext
from distance.level import WedgeGS, Group


def convrot(quat):
    import numpy as np
    return np.array([quat.z, quat.y, -quat.x, quat.w])


def length(vec):
    import numpy as np
    return np.linalg.norm(vec)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", nargs=1, help=".bytes filename")
    args = parser.parse_args()

    import numpy as np, quaternion
    from numpy import pi, sin, cos

    objs = []
    dest = np.array([[-10, 0, 0], [-10, 10, 0], [10, 0, 0]])

    a = pi/2
    u = np.array([4, 9, 1])
    asin = sin(a)
    srot = np.quaternion(cos(a), *(u*asin)).normalized()
    dest = np.array([(srot * np.quaternion(0, *p) / srot).imag for p in dest])

    simplesize = 64

    # scale = (1/16, 1/16, 1/16)
    # rot = np.quaternion(1, 0, 0, 0)
    # orot = np.quaternion(cos(pi/2), sin(pi/2), 0, 0)
    # a = pi / 12
    # rotstep = np.quaternion(cos(a), sin(a), 0, 0)
    # for i in range(12):
    #     rot *= rotstep
    #     pos = rot * np.quaternion(0, 0, 10, 0) / rot
    #     print(f"rot: {rot}")
    #     objs.append(WedgeGS(transform=((*pos.imag,), convrot(orot * rot), scale)))

    pr, pa, pb = dest
    rot = np.quaternion(1, 0, 0, 0)

    # rotate around y for pb
    vbr = pb - pr
    print("vbr", vbr)
    ay = -np.arctan2(vbr[2], vbr[0])
    rot *= np.quaternion(cos(ay/2), 0, sin(ay/2), 0)
    # rot = quaternion.from_euler_angles(0, ay, 0)
    print("ay", ay, rot)

    # rotate around z for pb
    vbxr = (rot.conj() * vbr * rot).imag
    az = np.arctan2(vbr[1], -vbr[0])
    rot *= np.quaternion(cos(az/2), 0, 0, sin(az/2))
    # rot = quaternion.from_euler_angles(0, ay, az)
    print("az", az, rot)

    # rotate around x for pa
    vaxr = pa - pr
    vaxr = (rot.conj() * np.quaternion(0, *vaxr) * rot).imag
    print("pa", pa, "vaxr", vaxr)
    ax = np.arctan2(vaxr[2], vaxr[1])
    rot = rot * np.quaternion(cos(ax/2), sin(ax/2), 0, 0)
    # rot = quaternion.from_euler_angles(ax, ay, az)
    print("ax", ax)

    print(" rot", rot)
    print("srot", srot)

    print("norms", rot.norm(), srot.norm())

    fixy = np.quaternion(cos(-pi/4), 0, sin(-pi/4), 0)

    pos = (pb + pa) / 2
    scale = [0, length(pr - pa) / simplesize, length(pr - pb) / simplesize]
    print("pos", pos, "rot", rot, "scale", scale)
    objs.append(WedgeGS(transform=(pos, convrot(fixy * rot), scale)))
    objs.append(WedgeGS(transform=(pos, convrot(fixy * srot), scale)))

    objs.extend(
        WedgeGS(type='SphereGS',
                transform=[point, (), [1/simplesize]*3])
        for point in itertools.chain(dest))
    group = Group(subobjects=objs)

    with open(args.FILE[0], 'wb') as f:
        group.write(DstBytes(f))

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
