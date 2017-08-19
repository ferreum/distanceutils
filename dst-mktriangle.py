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

    for i in range(7):
        for j in range(7):
            for k in range(7):
                dest = np.array([[-10, 0, 0], [-10, 10, 0], [10, 0, 0]])

                srot = quaternion.from_euler_angles(pi/3*i, pi/3*j, pi/3*k)

                dest = np.array([rotpoint(srot, p) for p in dest])

                # offset
                dest += np.array([(i-6) * 30, (j-6)*30, (k-6)*30])

                transform = rtri_to_transform(dest, srot)

                objs.append(WedgeGS(transform=transform))

                objs.extend(
                    WedgeGS(type='SphereGS',
                            transform=[point, (), [1/SIMPLE_SIZE]*3])
                    for point in itertools.chain(dest))

    group = Group(subobjects=objs)
    with open(args.FILE[0], 'wb') as f:
        group.write(DstBytes(f))

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
