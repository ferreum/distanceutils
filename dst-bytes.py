#!/usr/bin/python
# File:        dst-bytes.py
# Description: dst-bytes
# Created:     2017-06-28


import sys
import argparse
import traceback

from distance.bytes import DstBytes
from distance.knowntypes import maybe_partial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", nargs='+', help=".bytes filename")
    parser.add_argument("--unknown", action='append_const', const='unknown', dest='flags',
                        help="Print unknown data too (same as -f unknown).")
    parser.add_argument("-f", "--flags", action='append',
                        help="Add flags.")
    parser.set_defaults(flags=[])
    args = parser.parse_args()

    flags = [flag.strip() for arg in args.flags for flag in arg.split(',')]

    if not 'nogroups' in flags:
        flags.append('groups')

    have_error = False
    for fname in args.FILE:
        with open(fname, 'rb') as f:
            try:
                if len(args.FILE) > 1:
                    print()
                    print(f.name)
                dbytes = DstBytes(f)
                obj, _, exception = maybe_partial(dbytes)
                print(f"Type: {type(obj).__name__}")
                obj.print_data(sys.stdout, flags=flags)
            except KeyboardInterrupt:
                raise
            except:
                traceback.print_exc()
                have_error = True
    return 1 if have_error else 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
