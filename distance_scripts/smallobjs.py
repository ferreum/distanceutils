"""Find objects with very small y or z scale in CustomObject."""


import argparse

from distance.levelobjects import PROBER


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("FILE", help=".bytes CustomObject filename")
    args = parser.parse_args()

    obj = PROBER.read(args.FILE)

    def get_objs(o):
        yield o
        if o.is_object_group:
            for sub in o.children:
                yield from get_objs(sub)

    def is_small(o):
        _, sy, sz = o.transform[2] or (1, 1, 1)
        return sy < 1e-4 or sz < 1e-4

    objs = [o for o in get_objs(obj) if is_small(o)]
    objs.sort(key=(lambda o: min(o.transform[2])), reverse=True)

    for o in objs:
        print(o.type, o.transform[2])

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
