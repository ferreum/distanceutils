

from io import BytesIO
import argparse
from itertools import zip_longest

from distance.base import ObjectFragment
from distance import DefaultClasses, Level
from distance.printing import PrintContext


NamedPropertiesFragment = DefaultClasses.common.klass('NamedPropertiesFragment')


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
        with p.tree_children(2):
            p("Original:")
            with p.tree_children(1):
                p.print_object(org)
            p.tree_next_child()
            p("Result:")
            with p.tree_children(1):
                p.print_object(res)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", help="Write result to given file.")
    parser.add_argument("FILE", help="Input file.")
    args = parser.parse_args()

    with open(args.FILE, 'rb') as f:
        data_in = f.read()

    orgobj = DefaultClasses.file.read(BytesIO(data_in))

    buf_out = BytesIO(data_in)
    orgobj.write(buf_out)

    is_equal = True

    lendiff = len(buf_out.getbuffer()) - len(data_in)
    if lendiff > 0:
        print(f"result is {lendiff} bytes longer")
        is_equal = False
    elif lendiff < 0:
        print(f"result is {-lendiff} bytes shorter")
        is_equal = False

    if not lendiff and buf_out.getbuffer() != data_in:
        print("data differs")
        is_equal = False

    if args.w is not None:
        with open(args.w, 'wb') as f:
            n = f.write(buf_out.getbuffer())
        print(f"{n} bytes written")

    if is_equal:
        print("data matches")
    else:
        buf_out.seek(0)
        resobj = DefaultClasses.file.read(buf_out)
        listdiffs(orgobj, resobj)

    return 0 if is_equal else 1


if __name__ == '__main__':
    exit(main())

# vim:set sw=4 ts=8 sts=4 et:
