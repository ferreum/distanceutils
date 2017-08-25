#!/usr/bin/bash
# File:        mklevelinfos.sh
# Description: Creates level info database from WorkshopLevelInfos.bytes
# Created:     2017-06-25

mydir=$(dirname -- "$(realpath -- "$0")")
source "$mydir/common.shlib"

"$mydir"/dst-mklevelinfos.py "$distance_wspath/WorkshopLevelInfos.bytes"

# vim:set sw=2 ts=2 sts=0 et sta sr ft=sh fdm=marker:
