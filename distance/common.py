#!/usr/bin/python
# File:        common.py
# Description: common
# Created:     2017-06-15

import os


CACHE_PATH = os.path.expanduser('~/.cache/dst')


def get_cache_filename(filename):
    return os.path.join(CACHE_PATH, filename)


def format_bytes(data, fmt='02x'):
    if isinstance(data, (tuple, list)):
        return ', '.join(format_bytes(d) for d in data)
    else:
        return ' '.join(format(b, fmt) for b in data)


def format_duration(msec):
    if msec is None:
        return "None"
    negative = msec < 0
    if negative:
        msec = -msec
    hours = ""
    if msec >= 3600000:
        hours = f"{msec // 3600000}:"
        msec = msec % 3600000
    mins = msec // 60000
    msec %= 60000
    sec = msec // 1000
    msec %= 1000
    return f"{'-' if negative else ''}{hours}{mins:02}:{sec:02}.{msec:03}"


def format_color(color):
    return ', '.join(f"{round(c * 100)}%" for c in color)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
