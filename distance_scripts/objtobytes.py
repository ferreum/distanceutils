"""Convert wavefront .obj to CustomObject made from simples."""


import sys
import argparse

from distance.levelobjects import Group


def read_floats(s):
    return [float(f) for f in s.split(' ') if f]


def make_rgba(color, alpha=1.0):
    color = list(color)
    l = len(color)
    if l > 4:
        return color[:4]
    elif l == 4:
        return color
    else:
        if l < 3:
            color.extend([0] * (3 - l))
        return color + [alpha]


class Material(object):

    name = None
    ambient = (1, 1, 1, 1)
    diffuse = (1, 1, 1, 1)
    specular = (1, 1, 1, 1)
    specular_exp = 0
    opacity = 1.0
    illum = 0

    def __init__(self, base=None, **kw):
        if base:
            for k in ('ambient', 'diffuse', 'specular', 'specular_exp',
                      'opacity', 'illum'):
                self.__dict__.put(getattr(base, k))
        self.__dict__.update(kw)

    def put_options(self, dest):

        import numpy as np

        alpha = self.opacity
        if alpha < 0:
            alpha = 0
        elif alpha > 1:
            alpha = 1
        spec = np.array(make_rgba(self.specular))
        spec_exp = self.specular_exp
        if spec_exp < 0.1:
            inv_spec_exp = 1.0
        else:
            inv_spec_exp = (1.0 - min(max(spec_exp, 0.0), 1000.0) / 1000.0) ** 3
            spec *= inv_spec_exp
            spec[3] = inv_spec_exp
        dest['mat_color'] = make_rgba(self.ambient, alpha=alpha)
        dest['mat_reflect'] = make_rgba(self.diffuse)
        dest['mat_spec'] = list(spec)
        if alpha < 0.95:
            dest['additive_transp'] = True
        return dest


class ObjReader(object):

    def __init__(self, file, options={}, default_material=Material()):
        self.file = file
        self.over_options = options
        self.material = None
        self.default_material = default_material

        self.started = False
        self.options = options
        self.group_num = 0
        self.group_name = None

    def set_material(self, mtl):
        opt = dict()
        if mtl is None:
            mtl = self.default_material
        mtl.put_options(opt)
        opt.update(self.over_options)
        self.options = opt

    def __iter__(self):
        if self.started:
            raise RuntimeError("__iter__ may only be called once")
        self.started = True

        import os

        num_faces = 0
        self.vertices = verts = []
        self.set_material(None)
        mtls = {}
        for line in self.file:
            left, _, vals = line.strip().partition(' ')
            if left == 'v':
                verts.append(read_floats(vals))
            elif left == 'g':
                self.group_num += 1
                self.group_name = vals.strip()
            elif left == 'f':
                face = []
                for i in vals.split(' '):
                    parts = i.split('/')
                    if parts[0]:
                        face.append(int(parts[0]))
                num_faces += 1
                yield face
            elif left == 'usemtl':
                self.set_material(mtls.get(vals.strip(), None))
            elif left == 'mtllib':
                filename = os.path.join(
                    os.path.dirname(self.file.name), vals.strip())
                try:
                    with open(filename) as f:
                        read_mtllib(f, mtls)
                except IOError:
                    print(f"could not read mtllib: {filename}")
        self.num_faces = num_faces


def read_mtllib(file, mtls, base=None):
    mtl = None
    for line in file:
        left, _, vals = line.strip().partition(' ')
        if left == 'newmtl':
            name = vals.strip()
            mtls[name] = mtl = Material(name=name, base=base)
        elif mtl:
            if left == 'Ka':
                mtl.ambient = read_floats(vals)
            elif left == 'Kd':
                mtl.diffuse = read_floats(vals)
            elif left == 'Ks':
                mtl.specular = read_floats(vals)
            elif left == 'illum':
                mtl.illum = float(vals.strip())
            elif left == 'Ns':
                mtl.specular_exp = float(vals.strip())
    return mtls


def obj_to_simples(obj, scale=1):
    from distance.transform import create_triangle_simples
    import numpy as np, quaternion
    quaternion # suppress warning

    objs = []
    root_objs = objs
    n_tris = 0
    num_added = 0
    group_name = None
    group_num = 0
    group_verts = []

    def end_group():
        nonlocal num_added
        num_added += len(objs)
        verts = np.array(group_verts)
        center = tuple((min(verts[:,i]) + max(verts[:,i])) / 2
                       for i in range(3))
        group = Group(custom_name=group_name,
                      children=objs)
        group.recenter(center)
        root_objs.append(group)

    for face in obj:

        if obj.group_num != group_num:
            if group_num > 0:
                end_group()
            objs = []
            group_verts = []
            group_name = obj.group_name
            group_num = obj.group_num

        verts = np.array([obj.vertices[i - 1] for i in face])
        verts *= scale, scale, -scale
        group_verts.extend(verts)

        options = obj.options

        it = iter(verts)
        first = next(it)
        prev = next(it)

        for vert in it:
            n_tris += 1
            create_triangle_simples(np.array([first, prev, vert]),
                                    objs, simple_args=options)
            prev = vert
            sys.stdout.write(f"\rgenerating... created {len(objs) + num_added} "
                             f"simples for {n_tris} triangles")

    print()

    if group_num > 0:
        end_group()

    return root_objs


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("--name", help="Custom object name")
    parser.add_argument("--scale", type=int, help="Set object scale")
    parser.add_argument("OBJIN", help=".obj filename to read")
    parser.add_argument("BYTESOUT", help=".bytes filename to write")
    parser.set_defaults(scale=16)
    args = parser.parse_args()

    def_mat = Material(
        ambient=(1, 1, 1),
        diffuse=(1, 1, 1),
        specular=(1, 1, 1),
    )
    options = dict(
        image_index=17,
        emit_index=17,
        world_mapped=True,
        disable_diffuse=True,
        disable_reflect=True,
        disable_bump=True
    )

    with open(args.OBJIN) as f:
        obj = ObjReader(f, options=options, default_material=def_mat)

        objs = obj_to_simples(obj, scale=args.scale)

        print(f"converted {len(obj.vertices)} vertices and "
              f"{obj.num_faces} faces")

    group = Group(children=objs, custom_name=args.name)

    print(f"writing...")
    n = group.write(args.BYTESOUT)
    print(f"{n} bytes written")
    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
