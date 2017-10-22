"""Sandbox for trying out simples generation."""


import argparse

from distance.levelobjects import GoldenSimple, Group


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", "--vertices", action='store_true',
                        help="Create vertex points.")
    parser.add_argument("-n",
                        help="Specify object count.")
    parser.add_argument("FILE", help=".bytes filename")
    args = parser.parse_args()

    maxes = [3, 3, 3]
    if args.n:
        maxes = [int(s.strip()) for s in args.n.split(",")]
        maxes += [1] * (3 - len(maxes))

    import numpy as np, quaternion
    from numpy import pi, sin, cos
    from distance.transform import (rotpoint, SIMPLE_SIZE,
                                    create_triangle_simples)

    quaternion # suppress warning

    maxes = np.array(maxes)
    speed = pi/6

    maxhalf = (maxes - 1) / 2
    maxi, maxj, maxk = maxes

    objs = []

    options = dict(
        image_index=14,
        emit_index=14,
        tex_scale=(10, 10, 10),
        mat_reflect=(.2, .2, .2, .2),
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

                if args.vertices:
                    objs.extend(
                        GoldenSimple(type='SphereGS',
                                     transform=[point, (), [.7/SIMPLE_SIZE]*3])
                        for point in verts)

    group = Group(children=objs)
    print("writing...")
    n = group.write(args.FILE)
    print(f"{n} bytes written")
    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
