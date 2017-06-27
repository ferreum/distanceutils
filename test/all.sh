#!/usr/bin/bash
# File:        all.sh
# Description: all
# Created:     2017-06-28

python -m unittest discover --pattern='*.py' "$@"

# vim:set sw=2 ts=2 sts=0 et sta sr ft=sh fdm=marker:
