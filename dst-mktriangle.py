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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", nargs=1, help=".bytes filename")
    args = parser.parse_args()

    import numpy as np, quaternion
    from numpy import pi, sin, cos
    from distance.transform import rtri_to_transform, rotpoint, SIMPLE_SIZE

    objs = []

    i = j = k = 0
    maxes = np.array([6, 6, 6])
    maxhalf = maxes / 2
    maxi, maxj, maxk = maxes
    for i in range(maxi + 1):
        for j in range(maxj + 1):
            for k in range(maxk + 1):
                print()
                verts = np.array([[-10, -5, 0], [10, -5, 0], [-10, 5, 0]])

                angles = pi/3*i, pi/3*j, pi/3*k
                print("angles", angles)
                srot = quaternion.from_euler_angles(*angles)

                verts = np.array([rotpoint(srot, p) for p in verts])

                # offset
                verts += (np.array([i, j, k]) - maxhalf) * 30

                transform = rtri_to_transform(verts, srot)

                objs.append(WedgeGS(transform=transform))

                objs.extend(
                    WedgeGS(type='SphereGS',
                            transform=[point, (), [.7/SIMPLE_SIZE]*3])
                    for point in itertools.chain(verts))

    group = Group(subobjects=objs)
    with open(args.FILE[0], 'wb') as f:
        group.write(DstBytes(f))

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
