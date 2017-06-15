#!/usr/bin/bash
# File:        updatelevels.sh
# Description: updatelevels
# Created:     2017-06-25

mydir=$(dirname "$0")
source "$mydir/common.shlib"

"$mydir"/dst-mklevelinfos.py "$distance_wspath/WorkshopLevelInfos.bytes"

# vim:set sw=2 ts=2 sts=0 et sta sr ft=sh fdm=marker:
