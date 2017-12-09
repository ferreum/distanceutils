

import argparse
from itertools import zip_longest

from distance.bytes import DstBytes
from distance.base import ObjectFragment
from distance import PROBER, Level
from distance.levelfragments import NamedPropertiesFragment
from distance.printing import PrintContext


def rec_iter_fragments(orglist, reslist, path):
    for org, res in zip_longest(orglist, reslist):
        yield org, res, path + [(org, res)]


def rec_iter_objs(orglist, reslist, path):
    for org, res in zip_longest(orglist, reslist):
        p = path + [(org, res)]
        yield from rec_iter_fragments(org.fragments, res.fragments, p)
        yield from rec_iter_objs(org.children, res.children, p)


def rec_iter_layers(orglist, reslist, path):
    for org, res in zip_longest(orglist, reslist):
        yield from rec_iter_objs(org.objects, res.objects, path + [(org, res)])


def rec_iter_level(org, res, path):
    p = path + [(org, res)]
    yield from rec_iter_objs([org.settings], [res.settings], p)
    yield from rec_iter_layers(org.layers, res.layers, p)


def iter_objs(org, res, path=[]):
    if isinstance(org, Level):
        yield from rec_iter_level(org, res, path)
    else:
        yield from rec_iter_objs([org], [res], path)


def fragments_equal(org, res):
    if org.container.to_key() != res.container.to_key():
        return False
    if isinstance(org, NamedPropertiesFragment):
        return (org.props == res.props
                and org.container.content_size == res.container.content_size)
    if isinstance(org, ObjectFragment):
        return org.real_transform == res.real_transform
    return org.raw_data == res.raw_data


def iter_diffs(orig, result):
    for org, res, path in iter_objs(orig, result):
        if not fragments_equal(org, res):
            yield org, res, path


def listdiffs(orig, result):
    p = PrintContext(flags=('allprops', 'fragments', 'sections', 'offset'))
    for org, res, path in iter_diffs(orig, result):
        pstr = '/'.join(repr(org) for org, res in path)
        p(f"Difference:")
        p(f"Original path: {pstr}")
        pstr = '/'.join(repr(res) for org, res in path)
        p(f"Result path:   {pstr}")
        with p.tree_children():
            p("Original:")
            with p.tree_children():
                p.print_data_of(org)
            p.tree_next_child()
            p("Result:")
            with p.tree_children():
                p.print_data_of(res)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", help="Write result to given file.")
    parser.add_argument("FILE", help="Input file.")
    args = parser.parse_args()

    with open(args.FILE, 'rb') as f:
        data = f.read()

    db_in = DstBytes.from_data(data)
    orgobj = PROBER.read(db_in)

    db_out = DstBytes.in_memory()
    orgobj.write(db_out)

    is_equal = True

    lendiff = len(db_out.file.getbuffer()) - len(data)
    if lendiff > 0:
        print(f"result is {lendiff} bytes longer")
        is_equal = False
    elif lendiff < 0:
        print(f"result is {-lendiff} bytes shorter")
        is_equal = False

    if not lendiff and db_out.file.getbuffer() != data:
        print("data differs")
        is_equal = False

    if args.w is not None:
        with open(args.w, 'wb') as f:
            n = (f.write(db_out.file.getbuffer()))
        print(f"{n} bytes written")

    if is_equal:
        print("data matches")
    else:
        db_out.seek(0)
        resobj = PROBER.read(db_out)
        listdiffs(orgobj, resobj)

    return 0 if is_equal else 1


if __name__ == '__main__':
    exit(main())

# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
