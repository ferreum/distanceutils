"""Common utility functions for scripts."""


import os


CACHE_PATH = os.path.expanduser('~/.cache/dst')

PROFILE_PATH = (os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
                + '/refract/Distance')


def get_cache_filename(filename):
    return os.path.join(CACHE_PATH, filename)


def get_profile_filename(filename):
    return os.path.join(PROFILE_PATH, filename)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
