# Created:     2017-08-16


"""Sandbox for trying out simples generation."""


import argparse

from distance.bytes import DstBytes
from distance.level import WedgeGS, Group


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("FILE", nargs=1, help=".bytes filename")
    args = parser.parse_args()

    import numpy as np, quaternion
    from numpy import pi, sin, cos
    from distance.transform import (rtri_to_transform, rotpoint, SIMPLE_SIZE,
                                    create_triangle_simples)

    quaternion # suppress warning

    maxes = np.array([1, 1, 1])
    speed = pi/6

    maxhalf = (maxes - 1) / 2
    maxi, maxj, maxk = maxes

    objs = []

    options = dict(
        image_index=14,
        emit_index=14,
        tex_scale=(10, 10, 10),
        reflect_color=(.2, .2, .2, .2),
        world_mapped=True,
    )

    for i in range(maxi):
        for j in range(maxj):
            for k in range(maxk):
                verts = np.array([[-10, -5, 0], [10, -5, 0], [-20, 5, 0]])

                angles = speed*i, speed*j, speed*k
                alpha, beta, gamma = angles
                print("angles", angles)
                srot = np.quaternion(cos(alpha/2), sin(alpha/2), 0, 0)
                srot *= np.quaternion(cos(beta/2), 0, sin(beta/2), 0)
                srot *= np.quaternion(cos(gamma/2), 0, 0, sin(gamma/2))

                verts = np.array([rotpoint(srot, p) for p in verts])

                # offset
                verts += (np.array([i, j, k]) - maxhalf) * 30

                create_triangle_simples(verts, objs, simple_args=options)

                # objs.extend(
                #     WedgeGS(type='SphereGS',
                #             transform=[point, (), [.7/SIMPLE_SIZE]*3])
                #     for point in itertools.chain(verts))

    group = Group(children=objs)
    with open(args.FILE[0], 'wb') as f:
        group.write(DstBytes(f))

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
