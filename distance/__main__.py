"""Prints distanceutils version when executed."""

import argparse


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--list-categories', action='store_true',
                   help="List all class categories.")
group.add_argument('--list-classes', nargs='?', const='all',
                   metavar='CATEGORY|"all"',
                   help="List classes of specified category or all categories.")
args = parser.parse_args()

if args.list_categories:
    from . import DefaultClasses
    DefaultClasses.print_listing(print_classes=False)
elif args.list_classes is not None:
    category = args.list_classes
    from . import DefaultClasses
    if category == 'all':
        DefaultClasses.print_listing()
    else:
        try:
            coll = DefaultClasses.get_category(category)
        except KeyError:
            print(f"Category {category!r} doesn't exist")
            exit(1)
        else:
            coll.print_listing()
else:
    from . import __version__
    print(f"distanceutils version {__version__}")


# vim:set sw=4 ts=8 sts=4 et:
