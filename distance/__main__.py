"""Prints distanceutils version when executed."""


import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--gen-autoload', action='store_true')

args = parser.parse_args()


if args.gen_autoload:
    from distance import _core
    _core.write_autoload_modules()
else:
    from . import __version__
    print(f"distanceutils version {__version__}")


# vim:set sw=4 ts=8 sts=4 et:
