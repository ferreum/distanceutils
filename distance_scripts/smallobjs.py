#!/usr/bin/python
# File:        smallobjs.py
# Description: Finds objects with very small y or z scale in CustomObject
# Created:     2017-08-20


import argparse

from distance.bytes import DstBytes
from distance.level import PROBER


def main():
    parser = argparse.ArgumentParser(
        description="Finds objects with very small y or z scale in CustomObject.")
    parser.add_argument("FILE", nargs=1, help=".bytes CustomObject filename")
    args = parser.parse_args()

    with open(args.FILE[0], 'rb') as f:
        obj = PROBER.read(DstBytes(f))

    def get_objs(o):
        yield o
        if o.is_object_group:
            for sub in o.children:
                yield from get_objs(sub)

    def is_small(o):
        _, sy, sz = o.transform[2]
        return sy < 1e-4 or sz < 1e-4

    objs = [o for o in get_objs(obj) if is_small(o)]
    objs.sort(key=(lambda o: min(o.transform[2])), reverse=True)

    for o in objs:
        print(o.type, o.transform[2])

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
