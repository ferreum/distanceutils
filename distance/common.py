#!/usr/bin/python
# File:        common.py
# Description: common
# Created:     2017-06-15

import os

CACHE_PATH = os.path.expanduser('~/.cache/dst')

def get_cache_filename(filename):
    return os.path.join(CACHE_PATH, filename)

# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
