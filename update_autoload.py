#!/usr/bin/env python


import os


def main():
    os.environ['DISTANCEUTILS_AUTOLOAD'] = "0"
    import distance
    distance._core.write_autoload_modules()


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 et:
