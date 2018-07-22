"""Common utility functions for scripts."""


import os


CACHE_PATH = os.path.expanduser('~/.cache/dst')

PROFILE_PATH = (os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
                + '/refract/Distance')


def get_cache_filename(filename):
    return os.path.join(CACHE_PATH, filename)


def get_profile_filename(filename):
    return os.path.join(PROFILE_PATH, filename)


def handle_pipeerror(func):
    def result(*args, **kw):
        try:
            return func(*args, **kw)
        except BrokenPipeError:
            return 1
    result.__name__ = func.__name__
    result.__doc__ = func.__doc__
    result.__wrapped__ = func
    return result


# vim:set sw=4 ts=8 sts=4 et:
