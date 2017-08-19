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


def normalized(vec):
    import numpy as np
    return vec / np.linalg.norm(vec)


def rotpoint(rot, point):
    import numpy as np
    return (rot * np.quaternion(0, *point) / rot).imag


def rotpointrev(rot, point):
    import numpy as np
    return (rot.conj() * np.quaternion(0, *point) * rot).imag


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", nargs=1, help=".bytes filename")
    args = parser.parse_args()

    import numpy as np, quaternion
    from numpy import pi, sin, cos

    objs = []
    simplesize = 64

    def rtri_to_transform(dest, srot):
        pr, pa, pb = dest
        rot = np.quaternion(1, 0, 0, 0)

        # rotate around y for pb
        vbr = pb - pr
        ay = -np.arctan2(vbr[2], vbr[0])
        rot *= np.quaternion(cos(ay/2), 0, sin(ay/2), 0)

        # rotate around z for pb
        vbxr = rotpointrev(rot, vbr)
        az = np.arctan2(vbxr[1], vbxr[0])
        rot *= np.quaternion(cos(az/2), 0, 0, sin(az/2))

        # rotate around x for pa
        vaxr = rotpointrev(rot, pa - pr)
        ax = np.arctan2(vaxr[2], vaxr[1])
        rot = rot * np.quaternion(cos(ax/2), sin(ax/2), 0, 0)

        print("ax", ax, "ay", ay, "az", az)

        print(" rot", rot)
        print("srot", srot)
        print("diff", rot*srot.conj())

        print("norms", rot.norm(), srot.norm())

        fixy = np.quaternion(cos(-pi/4), 0, sin(-pi/4), 0)

        pos = (pb + pa) / 2
        scale = [0, length(pr - pa) / simplesize, length(pr - pb) / simplesize]
        print("pos", pos, "rot", rot, "scale", scale)
        return pos, convrot(fixy * rot), scale

    for i in range(13):
        for j in range(13):
            for k in range(13):
                dest = np.array([[-10, 0, 0], [-10, 10, 0], [10, 0, 0]])

                srot = quaternion.from_euler_angles(pi/6*i, pi/6*j, pi/6*k)

                dest = np.array([rotpoint(srot, p) for p in dest])

                # offset
                dest += np.array([(i-6) * 30, (j-6)*30, (k-6)*30])

                transform = rtri_to_transform(dest, srot)

                objs.append(WedgeGS(transform=transform))

                # objs.extend(
                #     WedgeGS(type='SphereGS',
                #             transform=[point, (), [1/simplesize]*3])
                #     for point in itertools.chain(dest))

    group = Group(subobjects=objs)
    with open(args.FILE[0], 'wb') as f:
        group.write(DstBytes(f))

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
