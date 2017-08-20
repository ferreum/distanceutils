#!/usr/bin/python
# File:        dst-objtobytes.py
# Description: dst-objtobytes
# Created:     2017-08-20


import argparse

from distance.bytes import DstBytes
from distance.level import WedgeGS, Group


def parse_floats(s):
    return [float(f) for f in s.split(' ') if f]


class ObjFile(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)


def read_obj(file):
    verts = []
    # texs = []
    # normals = []
    faces = []
    for line in file:
        left, _, vals = line.strip().partition(' ')
        if left == 'v':
            verts.append(parse_floats(vals))
        # elif left == 'vt':
        #     texs.append(parse_floats(vals))
        # elif left == 'vn':
        #     normals.append(parse_floats(vals))
        elif left == 'f':
            face = []
            for i in vals.split(' '):
                parts = i.split('/')
                face.append(int(parts[0]))
            faces.append(face)
    return ObjFile(vertices=verts, faces=faces)


def obj_to_simples(obj, dest):
    from distance.transform import create_triangle_simples
    import numpy as np, quaternion

    scale = 16

    def mkwedge(**kw):
        return WedgeGS(
            mat_color=(.8, .8, .8, 1),
            mat_emit=(0, 0, 0, 0),
            mat_reflect=(0, 0, 0, 0),
            image_index=17,
            emit_index=17,
            world_mapped=True,
            disable_diffuse=True,
            disable_bump=True,
            disable_collision=True,
            **kw)

    vertices = np.array(obj.vertices) * scale
    for face in obj.faces:
        it = iter(face)
        first = vertices[next(it) - 1]
        prev = vertices[next(it) - 1]
        for index in it:
            print(index)
            vert = vertices[index - 1]
            create_triangle_simples(np.array([first, prev, vert]), dest,
                                    cls=mkwedge)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("OBJIN", nargs=1, help=".obj filename to read")
    parser.add_argument("BYTESOUT", nargs=1, help=".bytes filename to write")
    args = parser.parse_args()

    with open(args.OBJIN[0]) as f:
        obj = read_obj(f)
    print(f"loaded {len(obj.vertices)} vertices and {len(obj.faces)} faces")

    objs = []

    obj_to_simples(obj, objs)

    group = Group(subobjects=objs)
    with open(args.BYTESOUT[0], 'wb') as f:
        group.write(DstBytes(f))

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
